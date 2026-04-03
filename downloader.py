import yt_dlp
import os
import shutil
from pathlib import Path

PLATFORMS = ("youtube", "tiktok", "instagram")


def get_default_download_path() -> str:
    return str(Path.home() / "Downloads" / "YouTube")


def _find_ffmpeg() -> str | None:
    """Locate ffmpeg — checks PATH first, then common Homebrew locations."""
    if path := shutil.which("ffmpeg"):
        return os.path.dirname(path)
    for candidate in (
        "/opt/homebrew/bin",  # Apple Silicon
        "/usr/local/bin",     # Intel Mac
    ):
        if os.path.isfile(os.path.join(candidate, "ffmpeg")):
            return candidate
    return None


def _base_opts(download_path: str, progress_hook) -> dict:
    os.makedirs(download_path, exist_ok=True)
    opts = {
        "outtmpl": os.path.join(download_path, "%(title)s.%(ext)s"),
        "noplaylist": True,
    }
    if ffmpeg_dir := _find_ffmpeg():
        opts["ffmpeg_location"] = ffmpeg_dir
    if progress_hook:
        opts["progress_hooks"] = [progress_hook]
    return opts


def _mp3_postprocessor() -> list:
    return [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}]


def build_ydl_opts(
    download_path: str,
    platform: str = "youtube",
    format_choice: str = "mp4",
    quality: str = "best",
    progress_hook=None,
) -> dict:
    opts = _base_opts(download_path, progress_hook)

    if platform == "youtube":
        opts.update(_youtube_opts(format_choice, quality))
    elif platform == "tiktok":
        opts.update(_tiktok_opts(format_choice))
    elif platform == "instagram":
        opts.update(_instagram_opts(format_choice))

    return opts


def _youtube_opts(format_choice: str, quality: str) -> dict:
    if format_choice == "mp3":
        return {"format": "bestaudio/best", "postprocessors": _mp3_postprocessor()}

    # Prefer H.264 + AAC for QuickTime compatibility
    h264, aac = "vcodec^=avc", "acodec^=mp4a"
    quality_map = {
        "best":  (f"bestvideo[{h264}][ext=mp4]+bestaudio[{aac}][ext=m4a]"
                  f"/bestvideo[{h264}]+bestaudio[{aac}]"
                  f"/bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best"),
        "1080p": (f"bestvideo[{h264}][height<=1080][ext=mp4]+bestaudio[{aac}][ext=m4a]"
                  f"/bestvideo[{h264}][height<=1080]+bestaudio[{aac}]"
                  f"/bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]"),
        "720p":  (f"bestvideo[{h264}][height<=720][ext=mp4]+bestaudio[{aac}][ext=m4a]"
                  f"/bestvideo[{h264}][height<=720]+bestaudio[{aac}]"
                  f"/bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]"),
        "480p":  (f"bestvideo[{h264}][height<=480][ext=mp4]+bestaudio[{aac}][ext=m4a]"
                  f"/bestvideo[{h264}][height<=480]+bestaudio[{aac}]"
                  f"/bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]"),
    }
    return {"format": quality_map.get(quality, quality_map["best"]), "merge_output_format": "mp4"}


def _tiktok_opts(format_choice: str) -> dict:
    if format_choice == "mp3":
        return {"format": "bestaudio/best", "postprocessors": _mp3_postprocessor()}
    return {"format": "bestvideo+bestaudio/best", "merge_output_format": "mp4"}


def _instagram_opts(format_choice: str) -> dict:
    if format_choice == "mp3":
        return {"format": "bestaudio/best", "postprocessors": _mp3_postprocessor()}
    return {"format": "bestvideo+bestaudio/best", "merge_output_format": "mp4"}


def get_video_info(url: str) -> dict:
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Unbekannt"),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", "Unbekannt"),
        }


def download_video(
    url: str,
    download_path: str,
    platform: str = "youtube",
    format_choice: str = "mp4",
    quality: str = "best",
    progress_hook=None,
) -> None:
    opts = build_ydl_opts(download_path, platform, format_choice, quality, progress_hook)
    with yt_dlp.YoutubeDL(opts) as ydl:
        ydl.download([url])


def format_duration(seconds: int) -> str:
    if not seconds:
        return "Unbekannt"
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
