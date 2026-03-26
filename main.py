import sys
import os
import threading

from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QPushButton, QComboBox,
    QProgressBar, QFileDialog, QMessageBox, QButtonGroup, QRadioButton,
    QFrame,
)
from PyQt6.QtCore import Qt, pyqtSignal, QObject
from PyQt6.QtGui import QFont, QColor, QPalette

from downloader import (
    download_video, get_video_info, get_default_download_path, format_duration,
)

# ------------------------------------------------------------------ signals --

class WorkerSignals(QObject):
    progress = pyqtSignal(float, str)   # percent, label
    info     = pyqtSignal(str)
    done     = pyqtSignal()
    error    = pyqtSignal(str)


# --------------------------------------------------------------------- main --

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader")
        self.setFixedSize(640, 520)
        self._is_downloading = False
        self._signals = WorkerSignals()
        self._signals.progress.connect(self._on_progress)
        self._signals.info.connect(self._on_info)
        self._signals.done.connect(self._on_done)
        self._signals.error.connect(self._on_error)
        self._build_ui()
        self._apply_style()

    # ------------------------------------------------------------------- UI --

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 28, 30, 24)
        root.setSpacing(0)

        # Title
        title = QLabel("YouTube Downloader")
        title.setFont(QFont("SF Pro Display", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setObjectName("title")
        root.addWidget(title)

        subtitle = QLabel("Videos & Musik bequem herunterladen")
        subtitle.setFont(QFont("SF Pro Display", 11))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setObjectName("subtitle")
        root.addWidget(subtitle)
        root.addSpacing(20)

        # Card
        card = QFrame()
        card.setObjectName("card")
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(20, 14, 20, 18)
        card_layout.setSpacing(6)

        # URL row
        card_layout.addWidget(self._label("YouTube-URL"))
        url_row = QHBoxLayout()
        self._url_edit = QLineEdit()
        self._url_edit.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self._url_edit.setObjectName("input")
        self._url_edit.returnPressed.connect(self._fetch_info)
        url_row.addWidget(self._url_edit)
        info_btn = QPushButton("Info")
        info_btn.setObjectName("secondaryBtn")
        info_btn.setFixedWidth(64)
        info_btn.clicked.connect(self._fetch_info)
        url_row.addWidget(info_btn)
        card_layout.addLayout(url_row)

        self._info_label = QLabel("")
        self._info_label.setObjectName("infoText")
        self._info_label.setWordWrap(True)
        card_layout.addWidget(self._info_label)
        card_layout.addSpacing(6)

        # Format + Quality
        card_layout.addWidget(self._label("Format & Qualität"))
        fmt_row = QHBoxLayout()
        self._fmt_group = QButtonGroup(self)
        for i, fmt in enumerate(("MP4", "MP3")):
            rb = QRadioButton(fmt)
            rb.setObjectName("radio")
            if i == 0:
                rb.setChecked(True)
            self._fmt_group.addButton(rb, i)
            fmt_row.addWidget(rb)
        self._fmt_group.idToggled.connect(self._on_format_change)

        self._quality_combo = QComboBox()
        self._quality_combo.addItems(["best", "1080p", "720p", "480p"])
        self._quality_combo.setObjectName("combo")
        self._quality_combo.setFixedWidth(100)
        fmt_row.addWidget(self._quality_combo)
        fmt_row.addStretch()
        card_layout.addLayout(fmt_row)
        card_layout.addSpacing(6)

        # Path
        card_layout.addWidget(self._label("Speicherort"))
        path_row = QHBoxLayout()
        self._path_edit = QLineEdit(get_default_download_path())
        self._path_edit.setObjectName("input")
        path_row.addWidget(self._path_edit)
        browse_btn = QPushButton("...")
        browse_btn.setObjectName("secondaryBtn")
        browse_btn.setFixedWidth(40)
        browse_btn.clicked.connect(self._choose_path)
        path_row.addWidget(browse_btn)
        card_layout.addLayout(path_row)

        root.addWidget(card)
        root.addSpacing(16)

        # Progress
        self._progress_label = QLabel("")
        self._progress_label.setObjectName("subtitle")
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._progress_label)
        root.addSpacing(4)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setValue(0)
        self._progress_bar.setObjectName("progress")
        self._progress_bar.setTextVisible(False)
        self._progress_bar.setFixedHeight(8)
        root.addWidget(self._progress_bar)
        root.addSpacing(14)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)

        self._dl_btn = QPushButton("Download starten")
        self._dl_btn.setObjectName("primaryBtn")
        self._dl_btn.clicked.connect(self._start_download)
        btn_row.addWidget(self._dl_btn)

        open_btn = QPushButton("Ordner öffnen")
        open_btn.setObjectName("secondaryBtn")
        open_btn.clicked.connect(self._open_folder)
        btn_row.addWidget(open_btn)

        root.addLayout(btn_row)

    def _label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("fieldLabel")
        lbl.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
        return lbl

    def _apply_style(self):
        self.setStyleSheet("""
            QWidget {
                background-color: #1a1a2e;
                color: #eaeaea;
                font-family: 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
            }
            QLabel#title { color: #e94560; }
            QLabel#subtitle, QLabel#infoText, QLabel#fieldLabel { color: #888888; }
            QFrame#card {
                background-color: #16213e;
                border-radius: 10px;
            }
            QLineEdit#input {
                background-color: #0f3460;
                border: none;
                border-radius: 6px;
                padding: 8px 10px;
                color: #eaeaea;
                font-size: 12px;
            }
            QLineEdit#input:focus { border: 1px solid #e94560; }
            QComboBox#combo {
                background-color: #0f3460;
                border: none;
                border-radius: 6px;
                padding: 6px 10px;
                color: #eaeaea;
            }
            QComboBox#combo::drop-down { border: none; }
            QComboBox#combo QAbstractItemView {
                background-color: #0f3460;
                color: #eaeaea;
                selection-background-color: #e94560;
            }
            QRadioButton#radio { color: #eaeaea; spacing: 6px; }
            QRadioButton#radio::indicator {
                width: 14px; height: 14px;
                border-radius: 7px;
                border: 2px solid #888;
                background: transparent;
            }
            QRadioButton#radio::indicator:checked {
                background-color: #e94560;
                border-color: #e94560;
            }
            QPushButton#primaryBtn {
                background-color: #e94560;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 11px 24px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#primaryBtn:hover { background-color: #c73652; }
            QPushButton#primaryBtn:disabled { background-color: #555; color: #888; }
            QPushButton#secondaryBtn {
                background-color: #0f3460;
                color: #eaeaea;
                border: none;
                border-radius: 6px;
                padding: 8px 12px;
                font-size: 11px;
            }
            QPushButton#secondaryBtn:hover { background-color: #1a4a80; }
            QProgressBar#progress {
                background-color: #0f3460;
                border-radius: 4px;
                border: none;
            }
            QProgressBar#progress::chunk {
                background-color: #e94560;
                border-radius: 4px;
            }
        """)

    # ------------------------------------------------------------ handlers --

    def _on_format_change(self, btn_id: int, checked: bool):
        if checked:
            self._quality_combo.setEnabled(btn_id == 0)

    def _choose_path(self):
        path = QFileDialog.getExistingDirectory(self, "Speicherort wählen", self._path_edit.text())
        if path:
            self._path_edit.setText(path)

    def _open_folder(self):
        path = self._path_edit.text()
        if os.path.exists(path):
            os.system(f'open "{path}"')
        else:
            QMessageBox.information(self, "Info", f"Ordner existiert noch nicht:\n{path}")

    def _fetch_info(self):
        url = self._url_edit.text().strip()
        if not url:
            return
        self._info_label.setText("Lade Info…")

        def fetch():
            try:
                info = get_video_info(url)
                dur = format_duration(info["duration"])
                self._signals.info.emit(
                    f"{info['title']}  •  {dur}  •  {info['uploader']}"
                )
            except Exception as e:
                self._signals.info.emit(f"Fehler: {e}")

        threading.Thread(target=fetch, daemon=True).start()

    # ---------------------------------------------------------- download ---

    def _start_download(self):
        if self._is_downloading:
            return
        url = self._url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Fehlende URL", "Bitte eine YouTube-URL eingeben.")
            return

        self._is_downloading = True
        self._dl_btn.setEnabled(False)
        self._dl_btn.setText("Lädt herunter…")
        self._progress_bar.setValue(0)

        fmt = "mp3" if self._fmt_group.checkedId() == 1 else "mp4"
        quality = self._quality_combo.currentText()
        path = self._path_edit.text()

        def hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                speed = d.get("_speed_str", "")
                eta = d.get("_eta_str", "")
                pct = (downloaded / total * 100) if total else 0
                label = f"{speed}  –  ETA {eta}" if speed else ""
                self._signals.progress.emit(pct, label)
            elif d["status"] == "finished":
                self._signals.progress.emit(100, "Verarbeite…")

        def run():
            try:
                download_video(url=url, download_path=path, format_choice=fmt,
                               quality=quality, progress_hook=hook)
                self._signals.done.emit()
            except Exception as e:
                self._signals.error.emit(str(e))

        threading.Thread(target=run, daemon=True).start()

    def _on_progress(self, pct: float, label: str):
        self._progress_bar.setValue(int(pct))
        self._progress_label.setText(label)

    def _on_info(self, text: str):
        self._info_label.setText(text)

    def _on_done(self):
        self._progress_label.setText("Fertig!")
        self._is_downloading = False
        self._dl_btn.setEnabled(True)
        self._dl_btn.setText("Download starten")
        QMessageBox.information(self, "Fertig", "Download abgeschlossen!")

    def _on_error(self, msg: str):
        self._progress_label.setText("")
        self._is_downloading = False
        self._dl_btn.setEnabled(True)
        self._dl_btn.setText("Download starten")
        QMessageBox.critical(self, "Fehler", msg)


# ----------------------------------------------------------------- entrypoint

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
