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
if ! brew list python@3.12 &>/dev/null; then
    echo "→ Installiere python@3.12 …"
    brew install python@3.12
else
    echo "✓ python@3.12 vorhanden"
fi

BREW_PYTHON="$(brew --prefix python@3.12)/bin/python3.12"
echo "✓ Python: $("$BREW_PYTHON" --version)"

# ── 4. Altes .venv aufräumen ─────────────────────────
if [ -d ".venv" ]; then
    VENV_VER="$(.venv/bin/python3 -c 'import sys; print(sys.version)' 2>/dev/null || echo 'unknown')"
    if [[ "$VENV_VER" == *"3.9"* ]] || [[ "$VENV_VER" == "unknown" ]]; then
        echo "→ Entferne altes .venv …"
        rm -rf .venv
    fi
fi

# ── 5. Virtuelle Umgebung ────────────────────────────
if [ ! -d ".venv" ]; then
    echo "→ Erstelle .venv …"
    "$BREW_PYTHON" -m venv .venv
fi

# ── 6. Abhängigkeiten ────────────────────────────────
echo "→ Installiere Pakete (PySide6 + yt-dlp + Pillow) …"
.venv/bin/pip install --upgrade pip --quiet
.venv/bin/pip install -r requirements.txt --quiet

# ── 7. Smoke-Test ────────────────────────────────────
echo "→ Prüfe PySide6 …"
if ! .venv/bin/python -c "from PySide6.QtWidgets import QApplication" 2>/dev/null; then
    echo "ERROR: PySide6 konnte nicht importiert werden."
    exit 1
fi
echo "✓ PySide6 OK"

# ── 8. Icon generieren ───────────────────────────────
echo "→ Generiere App-Icon …"
.venv/bin/python icon.py

# ICNS für macOS erzeugen (braucht sips + iconutil, beide auf macOS vorinstalliert)
mkdir -p AppIcon.iconset
sips -z 16   16   icon.png --out AppIcon.iconset/icon_16x16.png      &>/dev/null
sips -z 32   32   icon.png --out AppIcon.iconset/icon_16x16@2x.png   &>/dev/null
sips -z 32   32   icon.png --out AppIcon.iconset/icon_32x32.png      &>/dev/null
sips -z 64   64   icon.png --out AppIcon.iconset/icon_32x32@2x.png   &>/dev/null
sips -z 128  128  icon.png --out AppIcon.iconset/icon_128x128.png    &>/dev/null
sips -z 256  256  icon.png --out AppIcon.iconset/icon_128x128@2x.png &>/dev/null
sips -z 256  256  icon.png --out AppIcon.iconset/icon_256x256.png    &>/dev/null
sips -z 512  512  icon.png --out AppIcon.iconset/icon_256x256@2x.png &>/dev/null
sips -z 512  512  icon.png --out AppIcon.iconset/icon_512x512.png    &>/dev/null
cp icon.png AppIcon.iconset/icon_512x512@2x.png
iconutil -c icns AppIcon.iconset
rm -rf AppIcon.iconset
echo "✓ Icon erstellt"

# ── 9. .app-Bundle bauen ─────────────────────────────
APP="YouTube Downloader.app"
echo "→ Erstelle $APP …"

# Alte Version entfernen
rm -rf "$APP"

mkdir -p "$APP/Contents/MacOS"
mkdir -p "$APP/Contents/Resources"

# Launcher-Script (findet das Repo-Verzeichnis relativ zum .app)
cat > "$APP/Contents/MacOS/YouTube Downloader" <<'LAUNCHER'
#!/usr/bin/env bash
# Homebrew-PATH einbinden (Apple Silicon + Intel), damit ffmpeg gefunden wird
export PATH="/opt/homebrew/bin:/usr/local/bin:$PATH"
# Verzeichnis der .app ermitteln -> eine Ebene höher = Repo-Root
REPO="$(cd "$(dirname "$0")/../../.." && pwd)"
cd "$REPO"
exec .venv/bin/python main.py
LAUNCHER
chmod +x "$APP/Contents/MacOS/YouTube Downloader"

# Icon kopieren
cp AppIcon.icns "$APP/Contents/Resources/AppIcon.icns"

# Info.plist
cat > "$APP/Contents/Info.plist" <<'PLIST'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
  "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>CFBundleExecutable</key>
  <string>YouTube Downloader</string>
  <key>CFBundleIconFile</key>
  <string>AppIcon</string>
  <key>CFBundleIdentifier</key>
  <string>personal.youtube-downloader</string>
  <key>CFBundleName</key>
  <string>YouTube Downloader</string>
  <key>CFBundleDisplayName</key>
  <string>YouTube Downloader</string>
  <key>CFBundlePackageType</key>
  <string>APPL</string>
  <key>CFBundleShortVersionString</key>
  <string>1.0</string>
  <key>LSMinimumSystemVersion</key>
  <string>13.0</string>
  <key>NSHighResolutionCapable</key>
  <true/>
  <key>NSPrincipalClass</key>
  <string>NSApplication</string>
</dict>
</plist>
PLIST

echo "✓ $APP erstellt"

echo ""
echo "================================================"
echo "  Setup abgeschlossen!"
echo ""
echo "  App starten: Doppelklick auf"
echo "  'YouTube Downloader.app'"
echo ""
echo "  Tipp: Ziehe die .app in deinen Programme-Ordner"
echo "================================================"
