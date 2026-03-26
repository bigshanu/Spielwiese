#!/usr/bin/env bash
set -e

echo "==> YouTube Downloader Setup"

# Homebrew prüfen
if ! command -v brew &>/dev/null; then
    echo "Homebrew fehlt. Bitte installieren: https://brew.sh"
    exit 1
fi

# Homebrew-Python + Tcl/Tk installieren
# Das System-Python 3.9 (Xcode CLT) nutzt Tcl/Tk 8.5 und crasht auf modernem macOS.
# Homebrew-Python bringt ein kompatibles Tcl/Tk 8.6+ mit.
if ! brew list python-tk &>/dev/null 2>&1; then
    echo "==> Installiere python-tk via Homebrew (inkl. Tcl/Tk 8.6)..."
    brew install python-tk
fi

BREW_PYTHON=$(brew --prefix python)/bin/python3
if [ ! -x "$BREW_PYTHON" ]; then
    echo "==> Installiere python via Homebrew..."
    brew install python
    BREW_PYTHON=$(brew --prefix python)/bin/python3
fi

# ffmpeg prüfen
if ! command -v ffmpeg &>/dev/null; then
    echo "==> Installiere ffmpeg via Homebrew..."
    brew install ffmpeg
fi

# Virtuelle Umgebung mit Homebrew-Python anlegen
if [ ! -d ".venv" ]; then
    echo "==> Erstelle virtuelle Umgebung (.venv) mit Homebrew-Python..."
    "$BREW_PYTHON" -m venv .venv
fi

echo "==> Installiere Python-Abhängigkeiten..."
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet

echo ""
echo "Setup abgeschlossen!"
echo ""
echo "App starten:"
echo "  .venv/bin/python main.py"
