#!/bin/bash
set -e

# Read version from version.txt
if [ ! -f "version.txt" ]; then
    echo "Error: version.txt not found!"
    exit 1
fi
VERSION=$(cat version.txt | tr -d '[:space:]')
PACKAGE="sokonalysis_${VERSION}_all"
APP_DIR="/usr/share/sokonalysis"

echo "======================================"
echo " Building sokonalysis v${VERSION}"
echo "======================================"

# Update control file with correct version
sed -i "s/__VERSION__/${VERSION}/g" deb/DEBIAN/control

# Step 1: Build GUI executable
echo ""
echo "[1/2] Building GUI executable with PyInstaller..."

# Build the PyInstaller command with optional files
PYINSTALLER_CMD="pyinstaller --clean --onefile \
    --name sokonalysis \
    --add-data \"assets:assets\" \
    --add-data \"version.txt:.\" \
    --add-data \"LICENSE:.\" \
    --add-data \"EN.json:.\" \
    --add-data \"assets/docs/guide.pdf:assets/docs\" \
    --add-data \"assets/symbols:assets/symbols\""

# Add ai_operations.json if it exists
if [ -f "gui/ai_operations.json" ]; then
    PYINSTALLER_CMD="$PYINSTALLER_CMD --add-data \"gui/ai_operations.json:gui\""
    echo "  ✓ ai_operations.json found"
else
    echo "  ⚠ ai_operations.json not found - creating empty file"
    mkdir -p gui
    echo '{"operations": {}, "file_handlers": {}}' > gui/ai_operations.json
    PYINSTALLER_CMD="$PYINSTALLER_CMD --add-data \"gui/ai_operations.json:gui\""
fi

# Add english_words.json if it exists
if [ -f "gui/english_words.json" ]; then
    PYINSTALLER_CMD="$PYINSTALLER_CMD --add-data \"gui/english_words.json:gui\""
    echo "  ✓ english_words.json found"
else
    echo "  ⚠ english_words.json not found - creating empty file"
    mkdir -p gui
    echo '[]' > gui/english_words.json
    PYINSTALLER_CMD="$PYINSTALLER_CMD --add-data \"gui/english_words.json:gui\""
fi

# Add gui/ai/ data files if they exist
if [ -d "gui/ai" ]; then
    PYINSTALLER_CMD="$PYINSTALLER_CMD --add-data \"gui/ai:gui/ai\""
    echo "  ✓ gui/ai/ data files found"
fi

# Add hidden imports
PYINSTALLER_CMD="$PYINSTALLER_CMD \
    --hidden-import PySide6.QtCore \
    --hidden-import PySide6.QtGui \
    --hidden-import PySide6.QtWidgets \
    --hidden-import matplotlib \
    --hidden-import matplotlib.backends.backend_qt5agg \
    --hidden-import Crypto \
    --hidden-import distro \
    --hidden-import zipfile \
    --hidden-import hashlib \
    --hidden-import subprocess \
    --hidden-import json \
    --hidden-import re \
    --hidden-import ast \
    --hidden-import random \
    --icon assets/logo.png \
    --noconsole \
    main.py"


# Execute PyInstaller
eval $PYINSTALLER_CMD

# Step 2: Build .deb package
echo ""
echo "[2/2] Building ${PACKAGE}.deb..."

rm -rf "${PACKAGE}" "${PACKAGE}.deb"

mkdir -p "${PACKAGE}/DEBIAN"
mkdir -p "${PACKAGE}${APP_DIR}"
mkdir -p "${PACKAGE}/usr/local/bin"
mkdir -p "${PACKAGE}/usr/local/share/icons"
mkdir -p "${PACKAGE}/usr/share/applications"
mkdir -p "${PACKAGE}${APP_DIR}/gui"

# Copy DEBIAN control files
cp deb/DEBIAN/control "${PACKAGE}/DEBIAN/"
cp deb/DEBIAN/postinst "${PACKAGE}/DEBIAN/"
chmod 755 "${PACKAGE}/DEBIAN/postinst"

# Copy PyInstaller executable
if [ -f "dist/sokonalysis" ]; then
    cp dist/sokonalysis "${PACKAGE}${APP_DIR}/"
else
    echo "Error: dist/sokonalysis not found!"
    exit 1
fi

# Copy assets and data files
cp -r assets "${PACKAGE}${APP_DIR}/" 2>/dev/null || true
cp version.txt "${PACKAGE}${APP_DIR}/" 2>/dev/null || true
cp LICENSE "${PACKAGE}${APP_DIR}/" 2>/dev/null || true
cp EN.json "${PACKAGE}${APP_DIR}/" 2>/dev/null || true

# Copy GUI JSON data files
if [ -f "gui/ai_operations.json" ]; then
    cp gui/ai_operations.json "${PACKAGE}${APP_DIR}/gui/"
    echo "  ✓ ai_operations.json copied to package"
fi

if [ -f "gui/english_words.json" ]; then
    cp gui/english_words.json "${PACKAGE}${APP_DIR}/gui/"
    echo "  ✓ english_words.json copied to package"
fi

# Copy gui/ai/ data files
if [ -d "gui/ai" ]; then
    mkdir -p "${PACKAGE}${APP_DIR}/gui/ai"
    cp -r gui/ai/. "${PACKAGE}${APP_DIR}/gui/ai/" 2>/dev/null || true
    echo "  ✓ gui/ai/ data files copied to package"
fi

# Verify Morse code symbols
MORSE_COUNT=0
if [ -d "assets/symbols/morse" ]; then
    MORSE_COUNT=$(ls assets/symbols/morse/*.png 2>/dev/null | wc -l)
    echo "  ✓ Morse code symbols: ${MORSE_COUNT} images"
else
    echo "  ⚠ No Morse code symbols found in assets/symbols/morse/"
    mkdir -p "assets/symbols/morse"
fi

# Verify Pigpen symbols
PIGPEN_COUNT=0
if [ -d "assets/symbols/pigpen" ]; then
    PIGPEN_COUNT=$(ls assets/symbols/pigpen/*.png 2>/dev/null | wc -l)
    echo "  ✓ Pigpen symbols: ${PIGPEN_COUNT} images"
else
    echo "  ⚠ No Pigpen symbols found in assets/symbols/pigpen/"
    mkdir -p "assets/symbols/pigpen"
fi

# Verify Navy symbols
NAVY_COUNT=0
if [ -d "assets/symbols/navy" ]; then
    NAVY_COUNT=$(ls assets/symbols/navy/*.png 2>/dev/null | wc -l)
    echo "  ✓ Navy signal symbols: ${NAVY_COUNT} images"
else
    echo "  ⚠ No Navy signal symbols found in assets/symbols/navy/"
    mkdir -p "assets/symbols/navy"
fi

# Copy guide PDF
mkdir -p "${PACKAGE}${APP_DIR}/assets/docs"
if [ -f "assets/docs/guide.pdf" ]; then
    cp assets/docs/guide.pdf "${PACKAGE}${APP_DIR}/assets/docs/"
    echo "  ✓ Guide PDF copied"
elif [ -f "assets/guide.pdf" ]; then
    cp assets/guide.pdf "${PACKAGE}${APP_DIR}/assets/"
    echo "  ✓ Guide PDF copied (from assets/)"
else
    echo "  ⚠ No guide.pdf found — user guide will show 'not found'"
fi

# Copy icons
if [ -f "assets/logo.png" ]; then
    cp assets/logo.png "${PACKAGE}/usr/local/share/icons/sokonalysis.png"
fi
if [ -f "assets/logo.svg" ]; then
    cp assets/logo.svg "${PACKAGE}/usr/local/share/icons/sokonalysis.svg"
fi
if [ -f "assets/logo.ico" ]; then
    cp assets/logo.ico "${PACKAGE}/usr/local/share/icons/sokonalysis.ico"
fi

# Copy desktop file
if [ -f "sokonalysis.desktop" ]; then
    cp sokonalysis.desktop "${PACKAGE}/usr/share/applications/"
fi

# Count toolbar icons
ICON_COUNT=0
if [ -d "assets/icons" ]; then
    ICON_COUNT=$(ls assets/icons/*.png 2>/dev/null | wc -l)
    echo "  ✓ Toolbar icons: ${ICON_COUNT} images"
fi

# Create launcher script
cat > "${PACKAGE}/usr/local/bin/sokonalysis" << 'LAUNCHER'
#!/bin/bash
exec /usr/share/sokonalysis/sokonalysis "$@"
LAUNCHER
chmod 755 "${PACKAGE}/usr/local/bin/sokonalysis"

# Build the .deb
dpkg-deb --build "${PACKAGE}"

# Cleanup
rm -rf "${PACKAGE}"
rm -rf build dist *.spec

echo ""
echo "======================================"
echo " Done: ${PACKAGE}.deb"
echo "======================================"
echo ""
echo "The .deb contains:"
echo "  - Standalone executable (no Python required)"
echo "  - Morse code symbols (${MORSE_COUNT} images)"
echo "  - Pigpen symbols (${PIGPEN_COUNT} images)"
echo "  - Navy signal symbols (${NAVY_COUNT} images)"
echo "  - Toolbar icons (${ICON_COUNT} images)"
echo "  - Guide PDF"
echo "  - AI Operations JSON"
echo "  - English Words JSON"
echo ""