#!/bin/bash
# Build Windows executable natively using Wine + PyInstaller
# For systems with Wine installed

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_DIR/dist"
VERSION=${1:-"1.0.0"}

echo "Building Evidence Integrity Validator v$VERSION for Windows..."

rm -rf "$DIST_DIR" "$PROJECT_DIR/build" "$PROJECT_DIR/*.spec"
mkdir -p "$DIST_DIR"

# Create spec
cat > "$PROJECT_DIR/evidence-validator.spec" << 'SPEC'
# [spec content same as Docker script]
a = Analysis(['app.py'], ...)
pyz = PYZ(a.pure, a.zipped_data)
exe = EXE(pyz, a.scripts, name='EvidenceValidator', console=False, icon='icons/evidence.ico')
SPEC

# Install Python + PyInstaller in Wine if not already
wine python -m pip install pyinstaller flask pillow reportlab PyPDF2

# Build
cd "$PROJECT_DIR"
wine pyinstaller evidence-validator.spec --clean --onefile

echo "✅ Build complete: $DIST_DIR/EvidenceValidator.exe"
