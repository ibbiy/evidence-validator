#!/bin/bash
# Build Windows executable using Docker + PyInstaller
# Requires Docker installed

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DIST_DIR="$PROJECT_DIR/dist"
VERSION=${1:-"1.0.0"}

echo "============================================"
echo " Building Evidence Integrity Validator v$VERSION"
echo "============================================"

# Clean
rm -rf "$PROJECT_DIR/build" "$DIST_DIR" "$PROJECT_DIR/*.spec"
mkdir -p "$DIST_DIR"

# Create PyInstaller spec
cat > "$PROJECT_DIR/evidence-validator.spec" << SPEC
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

block_cipher = None

a = Analysis(
    ['app.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('templates/*.html', 'templates'),
        ('static/**/*', 'static'),
        ('tools/*.py', 'tools'),
    ],
    hiddenimports=['PIL', 'PIL.ExifTags', 'PyPDF2', 'reportlab', 'flask'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'matplotlib', 'numpy', 'scipy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='EvidenceValidator',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icons/evidence.ico',
)
SPEC

echo "Building with Docker..."
docker run --rm -v "$PROJECT_DIR:/src" \
    cdrx/pyinstaller-windows:latest \
    "pyinstaller evidence-validator.spec --clean --onefile"

echo ""
echo "✅ Build complete!"
echo "Output: $DIST_DIR/EvidenceValidator.exe"
ls -lh "$DIST_DIR/EvidenceValidator.exe" 2>/dev/null || echo "(check dist/ folder)"
