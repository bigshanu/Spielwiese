#!/usr/bin/env bash
set -e

echo "==> YouTube Downloader Setup"

# Python 3 prüfen
if ! command -v python3 &>/dev/null; then
    echo "Python 3 nicht gefunden. Bitte via https://brew.sh installieren:"
    echo "  brew install python"
    exit 1
fi

# ffmpeg prüfen (wird für mp4-Merge und mp3-Konvertierung benötigt)
if ! command -v ffmpeg &>/dev/null; then
    if command -v brew &>/dev/null; then
        echo "==> Installiere ffmpeg via Homebrew..."
        brew install ffmpeg
    else
        echo "ffmpeg fehlt. Bitte installieren:"
        echo "  brew install ffmpeg"
        echo "  (Homebrew: https://brew.sh)"
        exit 1
    fi
fi

# Virtuelle Umgebung anlegen
if [ ! -d ".venv" ]; then
    echo "==> Erstelle virtuelle Umgebung (.venv)..."
    python3 -m venv .venv
fi

echo "==> Installiere Python-Abhängigkeiten..."
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet

echo ""
echo "Setup abgeschlossen!"
echo ""
echo "App starten:"
echo "  .venv/bin/python main.py"
