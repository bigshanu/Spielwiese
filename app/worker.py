from PySide6.QtCore import QThread, Signal

from downloader import (
    download_video, get_video_info, format_duration,
    fetch_youtube_captions, transcribe_with_whisper,
    check_yt_dlp_update, update_yt_dlp,
)


class InfoWorker(QThread):
    result = Signal(str)

    def __init__(self, url: str):
        super().__init__()
        self._url = url

    def run(self):
        try:
            info = get_video_info(self._url)
            dur = format_duration(info["duration"])
            self.result.emit(f"{info['title']}  •  {dur}  •  {info['uploader']}")
        except Exception as e:
            self.result.emit(f"Fehler: {e}")


class DownloadWorker(QThread):
    progress       = Signal(float, str)   # percent, label
    status         = Signal(str)          # status text (e.g. "Transkribiere…")
    done           = Signal(str)          # success message
    error          = Signal(str)

    def __init__(
        self,
        url: str,
        path: str,
        platform: str,
        fmt: str,
        quality: str,
        transcript: bool = False,
        transcript_method: str = "youtube",   # "youtube" | "whisper"
        transcript_model: str = "Base  (ausgewogen, ~290 MB)",
        transcript_lang: str | None = None,
        browser: str | None = None,
        playlist: bool = False,
    ):
        super().__init__()
        self._url = url
        self._path = path
        self._platform = platform
        self._fmt = fmt
        self._quality = quality
        self._transcript = transcript
        self._transcript_method = transcript_method
        self._transcript_model = transcript_model
        self._transcript_lang = transcript_lang
        self._browser = browser
        self._playlist = playlist

    def run(self):
        def hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                pct = (downloaded / total * 100) if total else 0
                speed = d.get("_speed_str", "")
                eta = d.get("_eta_str", "")
                info = d.get("info_dict") or {}
                idx, n = info.get("playlist_index"), info.get("n_entries")
                prefix = f"[{idx}/{n}] " if idx and n else ""
                self.progress.emit(pct, f"{prefix}{speed}  –  ETA {eta}" if speed else prefix)
            elif d["status"] == "finished":
                self.progress.emit(100.0, "Verarbeite…")

        try:
            download_video(
                url=self._url,
                download_path=self._path,
                platform=self._platform,
                format_choice=self._fmt,
                quality=self._quality,
                progress_hook=hook,
                browser=self._browser,
                playlist=self._playlist,
            )
        except Exception as e:
            self.error.emit(str(e))
            return

        if not self._transcript:
            self.done.emit("Download abgeschlossen!")
            return

        # ── Transcript ──────────────────────────────────────────────────
        try:
            self.status.emit("Erstelle Transkript…")
            transcript_path = None

            if self._transcript_method == "youtube":
                self.status.emit("Lade YouTube-Untertitel…")
                transcript_path = fetch_youtube_captions(
                    self._url, self._path, self._transcript_lang
                )
                if transcript_path is None:
                    self.status.emit("Keine Untertitel gefunden – verwende Whisper…")
                    transcript_path = transcribe_with_whisper(
                        self._url, self._path,
                        model_key=self._transcript_model,
                        lang_code=self._transcript_lang,
                        status_hook=lambda s: self.status.emit(s),
                    )
            else:
                transcript_path = transcribe_with_whisper(
                    self._url, self._path,
                    model_key=self._transcript_model,
                    lang_code=self._transcript_lang,
                    status_hook=lambda s: self.status.emit(s),
                )

            self.done.emit(f"Download + Transkript abgeschlossen!\n📄 {transcript_path}")
        except Exception as e:
            self.done.emit(f"Download fertig. Transkript fehlgeschlagen: {e}")


class UpdateCheckWorker(QThread):
    result = Signal(str, object)  # current_version, latest_version (or None)

    def run(self):
        current, latest = check_yt_dlp_update()
        self.result.emit(current, latest)


class UpdateWorker(QThread):
    done  = Signal()
    error = Signal(str)

    def run(self):
        try:
            update_yt_dlp()
            self.done.emit()
        except Exception as e:
            self.error.emit(str(e))
