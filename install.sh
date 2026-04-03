#!/usr/bin/env bash
set -euo pipefail

echo "================================================"
echo "  YouTube Downloader — Setup"
echo "================================================"

# ── 1. Homebrew ──────────────────────────────────────
if ! command -v brew &>/dev/null; then
    echo "ERROR: Homebrew fehlt. Bitte installieren:"
    echo "  /bin/bash -c \"\$(curl -fsSL https://raw.githubusercontent.com/homebrew/install/HEAD/install.sh)\""
    exit 1
fi

# ── 2. ffmpeg ────────────────────────────────────────
if ! command -v ffmpeg &>/dev/null; then
    echo "→ Installiere ffmpeg …"
    brew install ffmpeg
else
    echo "✓ ffmpeg vorhanden"
fi

# ── 3. Python 3.12 via Homebrew ──────────────────────
# Explizit python@3.12 verwenden — NICHT das System-Python 3.9 (Xcode CLT)
if ! brew list python@3.12 &>/dev/null; then
    echo "→ Installiere python@3.12 …"
    brew install python@3.12
else
    echo "✓ python@3.12 vorhanden"
fi

BREW_PYTHON="$(brew --prefix python@3.12)/bin/python3.12"

if [ ! -x "$BREW_PYTHON" ]; then
    echo "ERROR: Homebrew-Python nicht gefunden unter $BREW_PYTHON"
    exit 1
fi

echo "✓ Python: $("$BREW_PYTHON" --version)"

# ── 4. Altes .venv aufräumen ─────────────────────────
# Entfernen falls mit dem kaputten System-Python 3.9 erstellt
if [ -d ".venv" ]; then
    VENV_VER="$(.venv/bin/python3 -c 'import sys; print(sys.version)' 2>/dev/null || echo 'unknown')"
    if [[ "$VENV_VER" == *"3.9"* ]] || [[ "$VENV_VER" == "unknown" ]]; then
        echo "→ Entferne altes .venv (Python 3.9 / defekt) …"
        rm -rf .venv
    else
        echo "✓ Vorhandenes .venv ist kompatibel ($VENV_VER)"
    fi
fi

# ── 5. Virtuelle Umgebung ────────────────────────────
if [ ! -d ".venv" ]; then
    echo "→ Erstelle .venv mit Homebrew-Python …"
    "$BREW_PYTHON" -m venv .venv
fi

# ── 6. Abhängigkeiten ────────────────────────────────
echo "→ Installiere Python-Pakete (PySide6 + yt-dlp) …"
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet

# ── 7. Smoke-Test ────────────────────────────────────
echo "→ Prüfe PySide6 …"
if ! .venv/bin/python -c "from PySide6.QtWidgets import QApplication" 2>/dev/null; then
    echo "ERROR: PySide6 konnte nicht importiert werden."
    echo "Bitte melde diesen Fehler."
    exit 1
fi
echo "✓ PySide6 OK"

# ── 8. Starter-Datei ────────────────────────────────
# .command-Datei = im Finder doppelklickbar
STARTER="Start YouTube Downloader.command"
cat > "$STARTER" <<'EOF'
#!/usr/bin/env bash
cd "$(dirname "$0")"
.venv/bin/python main.py
EOF
chmod +x "$STARTER"

echo ""
echo "================================================"
echo "  Setup abgeschlossen!"
echo ""
echo "  Starten via Terminal:"
echo "    .venv/bin/python main.py"
echo ""
echo "  Oder Doppelklick auf:"
echo "    'Start YouTube Downloader.command'"
echo "================================================"
