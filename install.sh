#!/usr/bin/env bash
set -e

echo "==> YouTube Downloader Setup"

# Homebrew prüfen
if ! command -v brew &>/dev/null; then
    echo "Homebrew fehlt. Bitte installieren: https://brew.sh"
    exit 1
fi

# ffmpeg installieren (für mp4-Merge und mp3-Konvertierung)
if ! command -v ffmpeg &>/dev/null; then
    echo "==> Installiere ffmpeg via Homebrew..."
    brew install ffmpeg
fi

# Homebrew-Python 3 ermitteln (NICHT das System-Python 3.9 von Xcode CLT verwenden)
BREW_PYTHON=$(brew --prefix)/bin/python3
if [ ! -x "$BREW_PYTHON" ]; then
    echo "==> Installiere python via Homebrew..."
    brew install python
fi

echo "==> Verwende Python: $($BREW_PYTHON --version)"

# Altes .venv entfernen falls es mit System-Python erstellt wurde
if [ -d ".venv" ]; then
    VENV_PYTHON="$($( pwd)/.venv/bin/python3 -c 'import sys; print(sys.executable)' 2>/dev/null || echo '')"
    if [[ "$VENV_PYTHON" == *"CommandLineTools"* ]] || [[ "$VENV_PYTHON" == *"3.9"* ]]; then
        echo "==> Entferne altes .venv (System-Python 3.9)..."
        rm -rf .venv
    fi
fi

# Virtuelle Umgebung mit Homebrew-Python erstellen
if [ ! -d ".venv" ]; then
    echo "==> Erstelle virtuelle Umgebung (.venv) mit Homebrew-Python..."
    "$BREW_PYTHON" -m venv .venv
fi

echo "==> Installiere Python-Abhängigkeiten (yt-dlp + PyQt6)..."
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet

echo ""
echo "Setup abgeschlossen!"
echo ""
echo "App starten:"
echo "  .venv/bin/python main.py"
