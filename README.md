# Evidence Integrity Validator v1.0

A professional forensic file integrity checking and evidence validation tool for digital forensics investigators, law enforcement, and cybersecurity professionals.

## Features

- **File Hashing** - Drag & drop files, compute MD5, SHA1, SHA256, SHA512, BLAKE2b
- **Bulk Processing** - Hash multiple files at once
- **Hash Verification** - Verify files against known hash values
- **Metadata Extraction** - EXIF from images (with GPS coordinates), PDF metadata, Office documents
- **PDF Reports** - Generate court-ready forensic reports with chain of custody
- **CSV Export** - Export hash results for spreadsheets
- **Clean Web UI** - Simple, professional interface

## Quick Start

```bash
pip install -r requirements.txt
python app.py
```

Open http://localhost:8081 in your browser.

## Building for Distribution

### Windows (.exe)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "EvidenceValidator" app.py
```

### macOS (.app)
```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name "EvidenceValidator" app.py
```

## License

Commercial license. Contact for distribution rights.
