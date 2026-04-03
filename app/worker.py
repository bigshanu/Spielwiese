from PySide6.QtCore import QThread, Signal

from downloader import download_video, get_video_info, format_duration


class InfoWorker(QThread):
    """Fetches video metadata without blocking the UI."""

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
    """Runs a yt-dlp download on a dedicated Qt thread."""

    progress = Signal(float, str)
    done = Signal()
    error = Signal(str)

    def __init__(self, url: str, path: str, platform: str, fmt: str, quality: str):
        super().__init__()
        self._url = url
        self._path = path
        self._platform = platform
        self._fmt = fmt
        self._quality = quality

    def run(self):
        def hook(d):
            if d["status"] == "downloading":
                total = d.get("total_bytes") or d.get("total_bytes_estimate", 0)
                downloaded = d.get("downloaded_bytes", 0)
                pct = (downloaded / total * 100) if total else 0
                speed = d.get("_speed_str", "")
                eta = d.get("_eta_str", "")
                self.progress.emit(pct, f"{speed}  –  ETA {eta}" if speed else "")
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
            )
            self.done.emit()
        except Exception as e:
            self.error.emit(str(e))
