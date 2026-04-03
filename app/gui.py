import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QProgressBar, QFileDialog,
    QMessageBox, QButtonGroup, QRadioButton, QFrame,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from downloader import get_default_download_path
from app.worker import InfoWorker, DownloadWorker

STYLESHEET = """
QWidget {
    background-color: #1a1a2e;
    color: #eaeaea;
    font-family: 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
}
QLabel#title   { color: #e94560; }
QLabel#muted   { color: #888888; }
QFrame#card    { background-color: #16213e; border-radius: 10px; }

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

QRadioButton { color: #eaeaea; spacing: 6px; }
QRadioButton::indicator {
    width: 14px; height: 14px;
    border-radius: 7px;
    border: 2px solid #888;
    background: transparent;
}
QRadioButton::indicator:checked {
    background-color: #e94560;
    border-color: #e94560;
}

QPushButton#primary {
    background-color: #e94560;
    color: white;
    border: none;
    border-radius: 8px;
    padding: 11px 24px;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#primary:hover    { background-color: #c73652; }
QPushButton#primary:disabled { background-color: #555; color: #888; }

QPushButton#secondary {
    background-color: #0f3460;
    color: #eaeaea;
    border: none;
    border-radius: 6px;
    padding: 8px 12px;
    font-size: 11px;
}
QPushButton#secondary:hover { background-color: #1a4a80; }

QProgressBar {
    background-color: #0f3460;
    border-radius: 4px;
    border: none;
}
QProgressBar::chunk {
    background-color: #e94560;
    border-radius: 4px;
}
"""


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("YouTube Downloader")
        self.setFixedSize(640, 500)

        self._info_worker: InfoWorker | None = None
        self._dl_worker: DownloadWorker | None = None

        self._build_ui()
        self.setStyleSheet(STYLESHEET)

    # ------------------------------------------------------------------- UI --

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 28, 30, 24)
        root.setSpacing(0)

        # Header
        title = QLabel("YouTube Downloader")
        title.setObjectName("title")
        title.setFont(QFont("SF Pro Display", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        subtitle = QLabel("Videos & Musik bequem herunterladen")
        subtitle.setObjectName("muted")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(subtitle)
        root.addSpacing(20)

        # Card
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 14, 20, 18)
        cl.setSpacing(6)

        # URL
        cl.addWidget(self._field_label("YouTube-URL"))
        url_row = QHBoxLayout()
        self._url_edit = QLineEdit()
        self._url_edit.setObjectName("input")
        self._url_edit.setPlaceholderText("https://www.youtube.com/watch?v=...")
        self._url_edit.returnPressed.connect(self._fetch_info)
        url_row.addWidget(self._url_edit)
        info_btn = QPushButton("Info")
        info_btn.setObjectName("secondary")
        info_btn.setFixedWidth(64)
        info_btn.clicked.connect(self._fetch_info)
        url_row.addWidget(info_btn)
        cl.addLayout(url_row)

        self._info_label = QLabel("")
        self._info_label.setObjectName("muted")
        self._info_label.setWordWrap(True)
        cl.addWidget(self._info_label)
        cl.addSpacing(6)

        # Format & Qualität
        cl.addWidget(self._field_label("Format & Qualität"))
        fmt_row = QHBoxLayout()
        self._fmt_group = QButtonGroup(self)
        for i, label in enumerate(("MP4", "MP3")):
            rb = QRadioButton(label)
            if i == 0:
                rb.setChecked(True)
            self._fmt_group.addButton(rb, i)
            fmt_row.addWidget(rb)
        self._fmt_group.idToggled.connect(self._on_format_change)

        self._quality_combo = QComboBox()
        self._quality_combo.setObjectName("combo")
        self._quality_combo.addItems(["best", "1080p", "720p", "480p"])
        self._quality_combo.setFixedWidth(100)
        fmt_row.addWidget(self._quality_combo)
        fmt_row.addStretch()
        cl.addLayout(fmt_row)
        cl.addSpacing(6)

        # Speicherort
        cl.addWidget(self._field_label("Speicherort"))
        path_row = QHBoxLayout()
        self._path_edit = QLineEdit(get_default_download_path())
        self._path_edit.setObjectName("input")
        path_row.addWidget(self._path_edit)
        browse_btn = QPushButton("...")
        browse_btn.setObjectName("secondary")
        browse_btn.setFixedWidth(40)
        browse_btn.clicked.connect(self._choose_path)
        path_row.addWidget(browse_btn)
        cl.addLayout(path_row)

        root.addWidget(card)
        root.addSpacing(16)

        # Fortschritt
        self._status_label = QLabel("")
        self._status_label.setObjectName("muted")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(self._status_label)
        root.addSpacing(4)

        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setFixedHeight(8)
        root.addWidget(self._progress)
        root.addSpacing(14)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(10)
        self._dl_btn = QPushButton("Download starten")
        self._dl_btn.setObjectName("primary")
        self._dl_btn.clicked.connect(self._start_download)
        btn_row.addWidget(self._dl_btn)

        open_btn = QPushButton("Ordner öffnen")
        open_btn.setObjectName("secondary")
        open_btn.clicked.connect(self._open_folder)
        btn_row.addWidget(open_btn)
        root.addLayout(btn_row)

    def _field_label(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("muted")
        lbl.setFont(QFont("SF Pro Display", 10, QFont.Weight.Bold))
        return lbl

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

        self._info_worker = InfoWorker(url)
        self._info_worker.result.connect(self._info_label.setText)
        self._info_worker.start()

    # ---------------------------------------------------------- download ---

    def _start_download(self):
        if self._dl_worker and self._dl_worker.isRunning():
            return
        url = self._url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Fehlende URL", "Bitte eine YouTube-URL eingeben.")
            return

        fmt = "mp3" if self._fmt_group.checkedId() == 1 else "mp4"
        self._dl_worker = DownloadWorker(
            url=url,
            path=self._path_edit.text(),
            fmt=fmt,
            quality=self._quality_combo.currentText(),
        )
        self._dl_worker.progress.connect(self._on_progress)
        self._dl_worker.done.connect(self._on_done)
        self._dl_worker.error.connect(self._on_error)

        self._dl_btn.setEnabled(False)
        self._dl_btn.setText("Lädt herunter…")
        self._progress.setValue(0)
        self._dl_worker.start()

    def _on_progress(self, pct: float, label: str):
        self._progress.setValue(int(pct))
        self._status_label.setText(label)

    def _on_done(self):
        self._status_label.setText("Fertig!")
        self._dl_btn.setEnabled(True)
        self._dl_btn.setText("Download starten")
        QMessageBox.information(self, "Fertig", "Download abgeschlossen!")

    def _on_error(self, msg: str):
        self._status_label.setText("")
        self._dl_btn.setEnabled(True)
        self._dl_btn.setText("Download starten")
        QMessageBox.critical(self, "Fehler", msg)
