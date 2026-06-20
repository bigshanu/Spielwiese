import os

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QComboBox, QProgressBar, QFileDialog,
    QMessageBox, QButtonGroup, QRadioButton, QFrame, QCheckBox,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

from downloader import get_default_download_path, WHISPER_MODELS, LANGUAGES
from app.worker import InfoWorker, DownloadWorker

PLATFORMS = [
    {"id": "youtube",   "label": "YouTube",   "has_quality": True,
     "placeholder": "https://www.youtube.com/watch?v=..."},
    {"id": "tiktok",    "label": "TikTok",    "has_quality": False,
     "placeholder": "https://www.tiktok.com/@user/video/..."},
    {"id": "instagram", "label": "Instagram", "has_quality": False,
     "placeholder": "https://www.instagram.com/reel/... oder /p/... (Videos, Bilder, Karussells)"},
]

# Browser IDs understood by yt-dlp's cookiesfrombrowser option
BROWSERS = {
    "Keiner":  None,
    "Safari":  "safari",
    "Chrome":  "chrome",
    "Firefox": "firefox",
    "Brave":   "brave",
}

STYLESHEET = """
QWidget {
    background-color: #1a1a2e;
    color: #eaeaea;
    font-family: 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
}
QLabel#title { color: #e94560; }
QLabel#muted { color: #888888; }
QFrame#card  { background-color: #16213e; border-radius: 10px; }
QFrame#transcript-card {
    background-color: #16213e;
    border-radius: 8px;
    border: 1px solid #2a2a4a;
}

QPushButton#tab {
    background-color: #0f3460;
    color: #888;
    border: none;
    border-radius: 8px;
    padding: 8px 0;
    font-size: 13px;
    font-weight: bold;
}
QPushButton#tab[active=true] {
    background-color: #e94560;
    color: white;
}
QPushButton#tab:hover { color: #eaeaea; }

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
    width: 14px; height: 14px; border-radius: 7px;
    border: 2px solid #888; background: transparent;
}
QRadioButton::indicator:checked { background-color: #e94560; border-color: #e94560; }

QCheckBox { color: #eaeaea; spacing: 6px; }
QCheckBox::indicator {
    width: 16px; height: 16px; border-radius: 4px;
    border: 2px solid #888; background: transparent;
}
QCheckBox::indicator:checked { background-color: #e94560; border-color: #e94560; }

QPushButton#primary {
    background-color: #e94560; color: white;
    border: none; border-radius: 8px;
    padding: 11px 24px; font-size: 13px; font-weight: bold;
}
QPushButton#primary:hover    { background-color: #c73652; }
QPushButton#primary:disabled { background-color: #555; color: #888; }

QPushButton#secondary {
    background-color: #0f3460; color: #eaeaea;
    border: none; border-radius: 6px;
    padding: 8px 12px; font-size: 11px;
}
QPushButton#secondary:hover { background-color: #1a4a80; }

QProgressBar { background-color: #0f3460; border-radius: 4px; border: none; }
QProgressBar::chunk { background-color: #e94560; border-radius: 4px; }
"""


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Downloader")
        self.setFixedSize(640, 650)

        self._platform_idx = 0
        self._info_worker: InfoWorker | None = None
        self._dl_worker: DownloadWorker | None = None

        self._build_ui()
        self.setStyleSheet(STYLESHEET)
        self._switch_platform(0)

    # ------------------------------------------------------------------- UI --

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(30, 28, 30, 24)
        root.setSpacing(0)

        # Header
        title = QLabel("Downloader")
        title.setObjectName("title")
        title.setFont(QFont("SF Pro Display", 22, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(title)

        subtitle = QLabel("YouTube  •  TikTok  •  Instagram")
        subtitle.setObjectName("muted")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        root.addWidget(subtitle)
        root.addSpacing(18)

        # Platform tabs
        tab_row = QHBoxLayout()
        tab_row.setSpacing(8)
        self._tab_btns = []
        for i, p in enumerate(PLATFORMS):
            btn = QPushButton(p["label"])
            btn.setObjectName("tab")
            btn.clicked.connect(lambda _, idx=i: self._switch_platform(idx))
            tab_row.addWidget(btn)
            self._tab_btns.append(btn)
        root.addLayout(tab_row)
        root.addSpacing(14)

        # Main card
        card = QFrame()
        card.setObjectName("card")
        cl = QVBoxLayout(card)
        cl.setContentsMargins(20, 14, 20, 18)
        cl.setSpacing(6)

        cl.addWidget(self._field_label("URL"))
        url_row = QHBoxLayout()
        self._url_edit = QLineEdit()
        self._url_edit.setObjectName("input")
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

        # Browser cookie selector (TikTok / Instagram only)
        self._browser_row = QWidget()
        browser_layout = QHBoxLayout(self._browser_row)
        browser_layout.setContentsMargins(0, 4, 0, 0)
        browser_layout.setSpacing(8)
        browser_lbl = self._field_label("Login via Browser")
        browser_lbl.setFixedWidth(110)
        browser_layout.addWidget(browser_lbl)
        self._browser_combo = QComboBox()
        self._browser_combo.setObjectName("combo")
        self._browser_combo.addItems(list(BROWSERS.keys()))
        self._browser_combo.setFixedWidth(120)
        browser_layout.addWidget(self._browser_combo)
        hint = QLabel("(für altersgeschützte Inhalte)")
        hint.setObjectName("muted")
        hint.setFont(QFont("SF Pro Display", 10))
        browser_layout.addWidget(hint)
        browser_layout.addStretch()
        cl.addWidget(self._browser_row)

        root.addWidget(card)
        root.addSpacing(10)

        # ── Transcript card ────────────────────────────────────────────────
        tc = QFrame()
        tc.setObjectName("transcript-card")
        tl = QVBoxLayout(tc)
        tl.setContentsMargins(16, 12, 16, 14)
        tl.setSpacing(8)

        self._transcript_cb = QCheckBox("Transkript erstellen  (gesprochener Text / Gesang → .txt)")
        self._transcript_cb.setFont(QFont("SF Pro Display", 11, QFont.Weight.Bold))
        self._transcript_cb.toggled.connect(self._on_transcript_toggle)
        tl.addWidget(self._transcript_cb)

        self._transcript_opts = QWidget()
        opts_layout = QVBoxLayout(self._transcript_opts)
        opts_layout.setContentsMargins(0, 0, 0, 0)
        opts_layout.setSpacing(6)

        method_row = QHBoxLayout()
        method_row.addWidget(self._field_label_inline("Methode:"))
        self._method_combo = QComboBox()
        self._method_combo.setObjectName("combo")
        self._method_combo.addItems(["YouTube Untertitel (schnell)", "Whisper KI (alle Plattformen)"])
        self._method_combo.currentIndexChanged.connect(self._on_method_change)
        self._method_combo.setFixedWidth(260)
        method_row.addWidget(self._method_combo)
        method_row.addStretch()
        opts_layout.addLayout(method_row)

        model_row = QHBoxLayout()
        model_row.addWidget(self._field_label_inline("Modell:"))
        self._model_combo = QComboBox()
        self._model_combo.setObjectName("combo")
        self._model_combo.addItems(list(WHISPER_MODELS.keys()))
        self._model_combo.setCurrentIndex(1)  # Base als Default
        self._model_combo.setFixedWidth(260)
        model_row.addWidget(self._model_combo)
        model_row.addStretch()
        opts_layout.addLayout(model_row)

        lang_row = QHBoxLayout()
        lang_row.addWidget(self._field_label_inline("Sprache:"))
        self._lang_combo = QComboBox()
        self._lang_combo.setObjectName("combo")
        self._lang_combo.addItems(list(LANGUAGES.keys()))
        self._lang_combo.setFixedWidth(180)
        lang_row.addWidget(self._lang_combo)
        lang_row.addStretch()
        opts_layout.addLayout(lang_row)

        tl.addWidget(self._transcript_opts)
        self._transcript_opts.setVisible(False)
        root.addWidget(tc)
        root.addSpacing(12)

        # Progress
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
        root.addSpacing(12)

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

    def _field_label_inline(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setObjectName("muted")
        lbl.setFont(QFont("SF Pro Display", 10))
        lbl.setFixedWidth(62)
        return lbl

    # ──────────────────────────────────────────────────── platform switching --

    def _switch_platform(self, idx: int):
        self._platform_idx = idx
        platform = PLATFORMS[idx]
        for i, btn in enumerate(self._tab_btns):
            btn.setProperty("active", i == idx)
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        self._url_edit.setPlaceholderText(platform["placeholder"])
        self._url_edit.clear()
        self._info_label.clear()
        self._status_label.clear()
        self._progress.setValue(0)
        self._quality_combo.setVisible(platform["has_quality"])
        base = str(__import__("pathlib").Path.home() / "Downloads")
        self._path_edit.setText(f"{base}/{platform['label']}")

        # Browser-Cookie-Auswahl nur für TikTok / Instagram
        is_social = platform["id"] in ("tiktok", "instagram")
        self._browser_row.setVisible(is_social)
        if not is_social:
            self._browser_combo.setCurrentIndex(0)  # zurück auf "Keiner"

        # YouTube-Untertitel-Methode nur bei YouTube sinnvoll
        is_youtube = platform["id"] == "youtube"
        yt_item = self._method_combo.model().item(0)
        yt_item.setEnabled(is_youtube)
        if not is_youtube and self._method_combo.currentIndex() == 0:
            self._method_combo.setCurrentIndex(1)

    # ──────────────────────────────────────────────────── transcript UI ──

    def _on_transcript_toggle(self, checked: bool):
        self._transcript_opts.setVisible(checked)

    def _on_method_change(self, idx: int):
        self._model_combo.setEnabled(idx == 1)

    def _on_format_change(self, btn_id: int, checked: bool):
        if checked:
            has_quality = PLATFORMS[self._platform_idx]["has_quality"]
            self._quality_combo.setEnabled(btn_id == 0 and has_quality)

    # ──────────────────────────────────────────────────────────────────────

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

    # ─────────────────────────────────────────────────────── download ──

    def _start_download(self):
        if self._dl_worker and self._dl_worker.isRunning():
            return
        url = self._url_edit.text().strip()
        if not url:
            QMessageBox.warning(self, "Fehlende URL", "Bitte eine URL eingeben.")
            return

        platform = PLATFORMS[self._platform_idx]
        fmt = "mp3" if self._fmt_group.checkedId() == 1 else "mp4"
        quality = self._quality_combo.currentText() if platform["has_quality"] else "best"

        transcript = self._transcript_cb.isChecked()
        method = "whisper" if self._method_combo.currentIndex() == 1 else "youtube"
        model_key = self._model_combo.currentText()
        lang_code = LANGUAGES.get(self._lang_combo.currentText())

        browser = BROWSERS.get(self._browser_combo.currentText())

        self._dl_worker = DownloadWorker(
            url=url,
            path=self._path_edit.text(),
            platform=platform["id"],
            fmt=fmt,
            quality=quality,
            transcript=transcript,
            transcript_method=method,
            transcript_model=model_key,
            transcript_lang=lang_code,
            browser=browser,
        )
        self._dl_worker.progress.connect(self._on_progress)
        self._dl_worker.status.connect(self._status_label.setText)
        self._dl_worker.done.connect(self._on_done)
        self._dl_worker.error.connect(self._on_error)

        self._dl_btn.setEnabled(False)
        self._dl_btn.setText("Lädt herunter…")
        self._progress.setValue(0)
        self._dl_worker.start()

    def _on_progress(self, pct: float, label: str):
        self._progress.setValue(int(pct))
        self._status_label.setText(label)

    def _on_done(self, msg: str):
        self._status_label.setText("Fertig!")
        self._dl_btn.setEnabled(True)
        self._dl_btn.setText("Download starten")
        QMessageBox.information(self, "Fertig", msg)

    def _on_error(self, msg: str):
        self._status_label.setText("")
        self._dl_btn.setEnabled(True)
        self._dl_btn.setText("Download starten")
        QMessageBox.critical(self, "Fehler", msg)
