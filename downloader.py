import yt_dlp
import os
from pathlib import Path


def get_default_download_path() -> str:
    return str(Path.home() / "Downloads" / "YouTube")


def build_ydl_opts(
    download_path: str,
    format_choice: str = "mp4",
    quality: str = "best",
    progress_hook=None,
) -> dict:
    os.makedirs(download_path, exist_ok=True)

    opts = {
        "outtmpl": os.path.join(download_path, "%(title)s.%(ext)s"),
        "noplaylist": True,
    }

    if progress_hook:
        opts["progress_hooks"] = [progress_hook]

    if format_choice == "mp3":
        opts.update(
            {
                "format": "bestaudio/best",
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            }
        )
    else:
        quality_map = {
            "best": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "1080p": "bestvideo[height<=1080][ext=mp4]+bestaudio[ext=m4a]/best[height<=1080]",
            "720p": "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]",
            "480p": "bestvideo[height<=480][ext=mp4]+bestaudio[ext=m4a]/best[height<=480]",
        }
        opts["format"] = quality_map.get(quality, quality_map["best"])
        opts["merge_output_format"] = "mp4"

    return opts


def get_video_info(url: str) -> dict:
    with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        info = ydl.extract_info(url, download=False)
        return {
            "title": info.get("title", "Unbekannt"),
            "duration": info.get("duration", 0),
            "uploader": info.get("uploader", "Unbekannt"),
            "thumbnail": info.get("thumbnail", ""),
        }


def download_video(
    url: str,
    download_path: str,
    format_choice: str = "mp4",
    quality: str = "best",
    progress_hook=None,
) -> None:
    opts = build_ydl_opts(download_path, format_choice, quality, progress_hook)
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
