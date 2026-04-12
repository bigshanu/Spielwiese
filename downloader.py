import yt_dlp
import os
import re
import shutil
import tempfile
from pathlib import Path

PLATFORMS = ("youtube", "tiktok", "instagram")

WHISPER_MODELS = {
    "Tiny  (schnell, ~150 MB)":  "tiny",
    "Base  (ausgewogen, ~290 MB)": "base",
    "Small (genau, ~490 MB)":    "small",
    "Medium (sehr genau, ~1.5 GB)": "medium",
}

LANGUAGES = {
    "Auto-Erkennung": None,
    "Deutsch":   "de",
    "Englisch":  "en",
    "Französisch": "fr",
    "Spanisch":  "es",
    "Italienisch": "it",
    "Türkisch":  "tr",
    "Arabisch":  "ar",
    "Japanisch": "ja",
    "Chinesisch": "zh",
}


def get_default_download_path() -> str:
    return str(Path.home() / "Downloads" / "YouTube")


def _find_ffmpeg() -> str | None:
    if path := shutil.which("ffmpeg"):
        return os.path.dirname(path)
    for candidate in ("/opt/homebrew/bin", "/usr/local/bin"):
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
    # Kein merge_output_format — Instagram liefert Videos (MP4) UND Bilder (JPG).
    # merge_output_format würde bei Bild-Posts einen Fehler verursachen.
    # noplaylist bleibt False damit Karussell-Posts (mehrere Bilder/Videos) vollständig
    # heruntergeladen werden.
    return {
        "format": "bestvideo+bestaudio/best",
        "noplaylist": False,
    }


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


# ── Transcript ────────────────────────────────────────────────────────────────

def _vtt_to_text(vtt_path: str) -> str:
    """Strip timestamps and metadata from a .vtt subtitle file → plain text."""
    text = Path(vtt_path).read_text(encoding="utf-8", errors="ignore")
    # Remove header, timestamps, and tags
    lines = []
    for line in text.splitlines():
        if re.match(r"WEBVTT|NOTE|^\d+$|-->|^$", line.strip()):
            continue
        clean = re.sub(r"<[^>]+>", "", line).strip()
        if clean:
            lines.append(clean)
    # Deduplicate consecutive identical lines (common in auto-captions)
    deduped = [lines[0]] if lines else []
    for line in lines[1:]:
        if line != deduped[-1]:
            deduped.append(line)
    return " ".join(deduped)


def fetch_youtube_captions(url: str, download_path: str, lang_code: str | None) -> str | None:
    """
    Try to download YouTube auto-captions via yt-dlp.
    Returns the transcript text, or None if no captions found.
    """
    langs = [lang_code, "en"] if lang_code and lang_code != "en" else ["en", "de"]

    with tempfile.TemporaryDirectory() as tmp:
        opts = {
            "skip_download": True,
            "writeautomaticsub": True,
            "subtitleslangs": langs,
            "subtitlesformat": "vtt",
            "outtmpl": os.path.join(tmp, "%(title)s.%(ext)s"),
            "quiet": True,
            "no_warnings": True,
        }
        try:
            with yt_dlp.YoutubeDL(opts) as ydl:
                info = ydl.extract_info(url, download=True)
                title = info.get("title", "transcript")
        except Exception:
            return None

        # Find the downloaded .vtt file
        vtt_files = list(Path(tmp).glob("*.vtt"))
        if not vtt_files:
            return None

        text = _vtt_to_text(str(vtt_files[0]))
        if not text:
            return None

        out_path = os.path.join(download_path, f"{title}.txt")
        Path(out_path).write_text(text, encoding="utf-8")
        return out_path


def transcribe_with_whisper(
    url: str,
    download_path: str,
    model_key: str = "Base  (ausgewogen, ~290 MB)",
    lang_code: str | None = None,
    status_hook=None,
) -> str:
    """
    Download audio and transcribe locally with faster-whisper.
    Returns the path to the saved .txt file.
    """
    from faster_whisper import WhisperModel

    model_size = WHISPER_MODELS.get(model_key, "base")

    if status_hook:
        status_hook("Lade Audio herunter…")

    with tempfile.TemporaryDirectory() as tmp:
        # Download audio only
        ffmpeg_dir = _find_ffmpeg()
        opts = {
            "format": "bestaudio/best",
            "outtmpl": os.path.join(tmp, "audio.%(ext)s"),
            "noplaylist": True,
            "quiet": True,
            "postprocessors": [{"key": "FFmpegExtractAudio", "preferredcodec": "mp3", "preferredquality": "192"}],
        }
        if ffmpeg_dir:
            opts["ffmpeg_location"] = ffmpeg_dir

        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(url, download=True)
            title = info.get("title", "transcript")

        audio_path = os.path.join(tmp, "audio.mp3")
        if not os.path.exists(audio_path):
            # Find whatever audio file was created
            audio_files = [f for f in Path(tmp).iterdir() if f.suffix in (".mp3", ".m4a", ".wav", ".opus")]
            if not audio_files:
                raise FileNotFoundError("Audio-Datei nicht gefunden.")
            audio_path = str(audio_files[0])

        if status_hook:
            status_hook(f"Lade Whisper-Modell ({model_size})…")

        model = WhisperModel(model_size, device="cpu", compute_type="int8")

        if status_hook:
            status_hook("Transkribiere…")

        segments, _ = model.transcribe(audio_path, beam_size=5, language=lang_code)
        text = " ".join(seg.text.strip() for seg in segments)

    os.makedirs(download_path, exist_ok=True)
    out_path = os.path.join(download_path, f"{title}.txt")
    Path(out_path).write_text(text, encoding="utf-8")
    return out_path


def format_duration(seconds: int) -> str:
    if not seconds:
        return "Unbekannt"
    minutes, secs = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes}:{secs:02d}"
