"""
Evidence Integrity Validator - Metadata Extraction Module
Extracts EXIF from images, metadata from PDFs and Office documents.
"""

import os
import struct
from datetime import datetime
from pathlib import Path


def extract_metadata(filepath: str) -> dict:
    """
    Extract metadata from a file based on its type.
    Returns dict with all discovered metadata.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")

    path = Path(filepath)
    ext = path.suffix.lower()
    result = {
        "filename": path.name,
        "filepath": str(path.absolute()),
        "type": "unknown",
        "metadata": {},
        "extracted": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    # Route to appropriate extractor
    if ext in (".jpg", ".jpeg", ".tiff", ".tif", ".png", ".webp"):
        result["type"] = "image"
        result["metadata"] = _extract_image_metadata(filepath)
    elif ext in (".pdf",):
        result["type"] = "pdf"
        result["metadata"] = _extract_pdf_metadata(filepath)
    elif ext in (".docx", ".xlsx", ".pptx"):
        result["type"] = "office"
        result["metadata"] = _extract_office_metadata(filepath)
    elif ext in (".mp4", ".avi", ".mov", ".mkv"):
        result["type"] = "video"
        result["metadata"] = _extract_video_metadata(filepath)
    else:
        result["type"] = "generic"
        result["metadata"] = _extract_generic_metadata(filepath)

    return result


def _extract_image_metadata(filepath: str) -> dict:
    """Extract EXIF and image metadata."""
    meta = {"basic": {}, "exif": {}}

    try:
        from PIL import Image
        from PIL.ExifTags import TAGS, GPSTAGS

        img = Image.open(filepath)

        # Basic image info
        meta["basic"] = {
            "format": img.format,
            "mode": img.mode,
            "width": img.width,
            "height": img.height,
            "size_mb": round(os.path.getsize(filepath) / (1024 * 1024), 2),
        }

        # EXIF data
        if hasattr(img, "_getexif") and img._getexif():
            exif = img._getexif()
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if isinstance(value, bytes):
                    try:
                        value = value.decode("utf-8", errors="replace")
                    except:
                        value = str(value)
                meta["exif"][tag] = str(value)

            # GPS data
            gps_info = {}
            for tag_id, value in exif.items():
                tag = TAGS.get(tag_id, tag_id)
                if tag == "GPSInfo":
                    for gps_tag, gps_value in value.items():
                        gps_name = GPSTAGS.get(gps_tag, gps_tag)
                        gps_info[gps_name] = str(gps_value)
            if gps_info:
                meta["gps"] = gps_info
                # Try to convert to decimal
                lat, lon = _gps_to_decimal(gps_info)
                if lat and lon:
                    meta["gps_coordinates"] = {"latitude": lat, "longitude": lon}

        img.close()

    except ImportError:
        meta["basic"]["note"] = "PIL/Pillow not installed"
    except Exception as e:
        meta["basic"]["error"] = str(e)

    return meta


def _extract_pdf_metadata(filepath: str) -> dict:
    """Extract PDF metadata."""
    meta = {"info": {}}

    try:
        import PyPDF2
        with open(filepath, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            info = reader.metadata
            if info:
                for key, value in info.items():
                    clean_key = key.replace("/", "").strip()
                    meta["info"][clean_key] = str(value)
            meta["pages"] = len(reader.pages)
    except ImportError:
        # Fallback: read raw PDF metadata
        meta["info"]["note"] = "PyPDF2 not installed, using raw extraction"
        try:
            with open(filepath, "rb") as f:
                content = f.read(4096)
                import re
                for match in re.finditer(rb"/(\w+)\s*\(([^)]*)\)", content):
                    key = match.group(1).decode("utf-8", errors="replace")
                    val = match.group(2).decode("utf-8", errors="replace")
                    meta["info"][key] = val
        except Exception as e:
            meta["info"]["error"] = str(e)

    return meta


def _extract_office_metadata(filepath: str) -> dict:
    """Extract Office document metadata."""
    meta = {"info": {}}

    try:
        import zipfile
        import xml.etree.ElementTree as ET

        with zipfile.ZipFile(filepath) as z:
            # Core properties
            if "docProps/core.xml" in z.namelist():
                core = z.read("docProps/core.xml")
                root = ET.fromstring(core)
                ns = {
                    "dc": "http://purl.org/dc/elements/1.1/",
                    "cp": "http://schemas.openxmlformats.org/package/2006/metadata/core-properties",
                    "dcterms": "http://purl.org/dc/terms/",
                }
                for key, val in [
                    ("creator", "dc:creator"),
                    ("title", "dc:title"),
                    ("subject", "dc:subject"),
                    ("description", "dc:description"),
                    ("created", "dcterms:created"),
                    ("modified", "dcterms:modified"),
                    ("lastModifiedBy", "cp:lastModifiedBy"),
                    ("revision", "cp:revision"),
                    ("category", "cp:category"),
                    ("contentStatus", "cp:contentStatus"),
                ]:
                    tag = val.split(":")[1]
                    ns_prefix = val.split(":")[0]
                    elem = root.find(f".//{{{ns[ns_prefix]}}}{tag}")
                    if elem is not None and elem.text:
                        meta["info"][key] = elem.text

    except zipfile.BadZipFile:
        meta["info"]["note"] = "Not a valid Office Open XML file"

    return meta


def _extract_video_metadata(filepath: str) -> dict:
    """Extract basic video metadata."""
    meta = {"info": {}}

    try:
        import subprocess
        result = subprocess.run(
            ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_format", "-show_streams", filepath],
            capture_output=True, text=True, timeout=10
        )
        import json
        data = json.loads(result.stdout)
        if "format" in data:
            fmt = data["format"]
            meta["info"]["format"] = fmt.get("format_name", "")
            meta["info"]["duration"] = f"{float(fmt.get('duration', 0)):.2f}s"
            meta["info"]["size"] = fmt.get("size", "")
            meta["info"]["bitrate"] = fmt.get("bit_rate", "")
        if "streams" in data:
            for s in data["streams"]:
                if s.get("codec_type") == "video":
                    meta["info"]["codec"] = s.get("codec_name", "")
                    meta["info"]["resolution"] = f"{s.get('width', '?')}x{s.get('height', '?')}"
                    meta["info"]["fps"] = s.get("r_frame_rate", "")
                    break
    except:
        meta["info"]["note"] = "ffprobe not available"

    return meta


def _extract_generic_metadata(filepath: str) -> dict:
    """Extract generic file metadata."""
    path = Path(filepath)
    stat = path.stat()

    return {
        "filesize": stat.st_size,
        "filesize_hr": _human_size(stat.st_size),
        "created": datetime.fromtimestamp(stat.st_ctime).strftime("%Y-%m-%d %H:%M:%S"),
        "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
        "accessed": datetime.fromtimestamp(stat.st_atime).strftime("%Y-%m-%d %H:%M:%S"),
        "extension": path.suffix.lower(),
        "permissions": oct(stat.st_mode)[-3:],
    }


def _gps_to_decimal(gps_info: dict) -> tuple:
    """Convert GPS EXIF coordinates to decimal degrees."""
    try:
        def _to_decimal(dms, ref):
            degrees = float(dms[0])
            minutes = float(dms[1])
            seconds = float(dms[2])
            decimal = degrees + minutes / 60.0 + seconds / 3600.0
            if ref in ("S", "W"):
                decimal = -decimal
            return decimal

        lat_dms = gps_info.get("GPSLatitude")
        lat_ref = gps_info.get("GPSLatitudeRef", "N")
        lon_dms = gps_info.get("GPSLongitude")
        lon_ref = gps_info.get("GPSLongitudeRef", "E")

        if lat_dms and lon_dms:
            import ast
            lat = _to_decimal(ast.literal_eval(lat_dms), lat_ref)
            lon = _to_decimal(ast.literal_eval(lon_dms), lon_ref)
            return (round(lat, 6), round(lon, 6))
    except:
        pass
    return (None, None)


def _human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"
