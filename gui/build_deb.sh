#!/bin/bash
set -e

# ---------------------------------------------------------------
# sokonalysis build script (PyInstaller + .deb)
# Run this from the gui/ folder, inside the build venv.
#
# Optional environment variables:
#   PYTHON=python3.12   Python interpreter to use (default: python)
#   KEEP_BUILD=1        Keep build/ and *.spec after the build (debugging)
# ---------------------------------------------------------------

PYTHON="${PYTHON:-python}"

# Read version from version.txt
if [ ! -f "version.txt" ]; then
    echo "Error: version.txt not found!"
    exit 1
fi
VERSION=$(tr -d '[:space:]' < version.txt)
ARCH=$(dpkg --print-architecture)
PACKAGE="sokonalysis_${VERSION}_${ARCH}"
APP_DIR="/usr/share/sokonalysis"

echo "======================================"
echo " Building sokonalysis v${VERSION} (${ARCH})"
echo "======================================"

# Warn about very new Python versions (PyInstaller hooks/wheels often lag behind)
PYVER=$("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])')
echo "Using Python ${PYVER} ($("$PYTHON" -c 'import sys; print(sys.executable)'))"
case "$PYVER" in
    3.13|3.14|3.15)
        echo "  ⚠ Python ${PYVER} is very new. Python 3.12 is the safest choice for PyInstaller builds."
        ;;
esac

# Make sure PyInstaller is available in this interpreter
if ! "$PYTHON" -m PyInstaller --version >/dev/null 2>&1; then
    echo "Error: PyInstaller is not installed for ${PYTHON}. Run: pip install pyinstaller"
    exit 1
fi

# Update control file (safe to run repeatedly, unlike a one-time placeholder swap)
sed -i "s/^Version:.*/Version: ${VERSION}/" deb/DEBIAN/control
sed -i "s/^Architecture:.*/Architecture: ${ARCH}/" deb/DEBIAN/control

# Step 1: Build GUI executable
echo ""
echo "[1/2] Building GUI executable with PyInstaller..."

# Helper: is a Python module installed in this environment?
has_module() {
    "$PYTHON" -c "import importlib.util, sys; sys.exit(0 if importlib.util.find_spec('$1') else 1)" 2>/dev/null
}

# Using a bash array (not eval) so paths with spaces work correctly
PYI_ARGS=(
    --clean
    --onefile
    --name sokonalysis
    --add-data "assets:assets"
    --add-data "version.txt:."
    --add-data "LICENSE:."
    --add-data "EN.json:."
    --add-data "assets/docs/guide.pdf:assets/docs"
    --add-data "assets/symbols:assets/symbols"
)

# Add ai_operations.json if it exists
if [ -f "gui/ai_operations.json" ]; then
    echo "  ✓ ai_operations.json found"
else
    echo "  ⚠ ai_operations.json not found - creating empty file"
    mkdir -p gui
    echo '{"operations": {}, "file_handlers": {}}' > gui/ai_operations.json
fi
PYI_ARGS+=(--add-data "gui/ai_operations.json:gui")

# Add english_words.json if it exists
if [ -f "gui/english_words.json" ]; then
    echo "  ✓ english_words.json found"
else
    echo "  ⚠ english_words.json not found - creating empty file"
    mkdir -p gui
    echo '[]' > gui/english_words.json
fi
PYI_ARGS+=(--add-data "gui/english_words.json:gui")

# Add gui/ai/ data files if they exist
if [ -d "gui/ai" ]; then
    PYI_ARGS+=(--add-data "gui/ai:gui/ai")
    echo "  ✓ gui/ai/ data files found"
fi

# ---------------------------------------------------------------
# PyMuPDF fix: newer PyMuPDF loads ONNX model/yaml files at import
# time (pymupdf.layout). PyInstaller doesn't bundle those data
# files automatically, which caused:
#   FileNotFoundError: .../pymupdf/layout/resources/onnx/layout_rf*.yaml
# --collect-all pulls in the package's code, data files and binaries.
# ---------------------------------------------------------------
for mod in pymupdf pymupdf_layout onnxruntime; do
    if has_module "$mod"; then
        PYI_ARGS+=(--collect-all "$mod")
        echo "  ✓ Collecting all files for: $mod"
    fi
done

# Hidden imports (standard library modules are detected automatically,
# so they are intentionally not listed here)
PYI_ARGS+=(
    --hidden-import fitz
    --hidden-import PySide6.QtCore
    --hidden-import PySide6.QtGui
    --hidden-import PySide6.QtWidgets
    --hidden-import matplotlib
    --hidden-import matplotlib.backends.backend_qt5agg
    --hidden-import matplotlib.backends.backend_qtagg
    --hidden-import Crypto
    --hidden-import distro
    --icon assets/logo.png
    --noconsole
    main.py
)

# Execute PyInstaller
"$PYTHON" -m PyInstaller "${PYI_ARGS[@]}"

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
    chmod 755 "${PACKAGE}${APP_DIR}/sokonalysis"
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
fi

# Verify Pigpen symbols
PIGPEN_COUNT=0
if [ -d "assets/symbols/pigpen" ]; then
    PIGPEN_COUNT=$(ls assets/symbols/pigpen/*.png 2>/dev/null | wc -l)
    echo "  ✓ Pigpen symbols: ${PIGPEN_COUNT} images"
else
    echo "  ⚠ No Pigpen symbols found in assets/symbols/pigpen/"
fi

# Verify Navy symbols
NAVY_COUNT=0
if [ -d "assets/symbols/navy" ]; then
    NAVY_COUNT=$(ls assets/symbols/navy/*.png 2>/dev/null | wc -l)
    echo "  ✓ Navy signal symbols: ${NAVY_COUNT} images"
else
    echo "  ⚠ No Navy signal symbols found in assets/symbols/navy/"
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

# Build the .deb (--root-owner-group avoids wrong file ownership inside the package)
dpkg-deb --root-owner-group --build "${PACKAGE}"

# Cleanup (dist/ is kept so you can test ./dist/sokonalysis directly)
rm -rf "${PACKAGE}"
if [ "${KEEP_BUILD:-0}" != "1" ]; then
    rm -rf build *.spec
fi

echo ""
echo "======================================"
echo " Done: ${PACKAGE}.deb"
echo "======================================"
echo ""
echo "Test the raw binary first:   ./dist/sokonalysis"
echo "Then install the package:    sudo dpkg -i ${PACKAGE}.deb"
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
