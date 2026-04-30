"""
Evidence Integrity Validator - Main Application
A professional forensic file integrity checking tool.
"""

import os
import sys
import json
import uuid
import shutil
import threading
import hashlib
import hmac
from datetime import datetime, timedelta
from pathlib import Path
from functools import wraps

# Ensure we can import tools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from tools.hasher import hash_file, hash_bulk, verify_hash
from tools.metadata import extract_metadata
from tools.reporter import generate_report

try:
    from flask import (
        Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
    )
except ImportError:
    os.system(f"{sys.executable} -m pip install flask -q")
    from flask import (
        Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
    )

app = Flask(__name__)
app.secret_key = uuid.uuid4().hex

# Inject license info into templates
@app.context_processor
def inject_license():
    return {
        "is_licensed": IS_LICENSED,
        "licensed_to": LICENSED_TO,
        "trial_max": TRIAL_MAX_FILES,
        "app_version": "1.0.0",
    }

BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))
UPLOAD_DIR = BASE_DIR / "uploads"
REPORT_DIR = BASE_DIR / "reports"
OUTPUT_DIR = BASE_DIR / "output"
UPLOAD_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# License system
LICENSE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.license')

# Demo mode: 3 file limit, unregistered watermark
TRIAL_MAX_FILES = 3
IS_LICENSED = False
LICENSED_TO = ""

def check_license():
    global IS_LICENSED, LICENSED_TO
    if os.path.exists(LICENSE_FILE):
        with open(LICENSE_FILE) as f:
            data = json.load(f)
            # Simple HMAC validation
            key = b"evidence-validator-secret-key-v1"
            msg = f"{data.get('name','')}:{data.get('email','')}".encode()
            expected = hmac.new(key, msg, hashlib.sha256).hexdigest()
            if data.get("sig") == expected:
                IS_LICENSED = True
                LICENSED_TO = data.get("name", "Licensed User")
                return True
    return False

def activate_license(name: str, email: str, key_text: str) -> bool:
    """Activate with a license key. Key format: EVIDENCE-XXXX-XXXX-XXXX"""
    key = b"evidence-validator-secret-key-v1"
    msg = f"{name}:{email}".encode()
    expected = hmac.new(key, msg, hashlib.sha256).hexdigest()[:20].upper()
    expected_key = f"EVIDENCE-{expected[:4]}-{expected[4:8]}-{expected[8:12]}"
    if key_text.strip().upper() == expected_key:
        sig = hmac.new(key, msg, hashlib.sha256).hexdigest()
        with open(LICENSE_FILE, 'w') as f:
            json.dump({"name": name, "email": email, "sig": sig}, f)
        check_license()
        return True
    return False

check_license()

# In-memory session store
sessions = {}


# Trial limit decorator
def require_licensed(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        s = get_session()
        if not IS_LICENSED and len(s.get("files", [])) > TRIAL_MAX_FILES:
            return jsonify({
                "error": "trial_limit",
                "message": f"Trial limit reached ({TRIAL_MAX_FILES} files). Purchase license to unlock unlimited files and remove watermarks.",
                "trial_max": TRIAL_MAX_FILES,
                "licensed": False
            }), 403
        return f(*args, **kwargs)
    return wrapper


def get_session():
    sid = session.get("sid")
    if not sid:
        sid = uuid.uuid4().hex
        session["sid"] = sid
    if sid not in sessions:
        sessions[sid] = {
            "files": [],
            "case_ref": "",
            "examiner": "",
            "agency": "",
            "chain_of_custody": [],
        }
    return sessions[sid]


# ===== API ROUTES =====

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/session", methods=["GET"])
def api_session():
    return jsonify(get_session())


@app.route("/api/config", methods=["POST"])
def api_config():
    data = request.json
    s = get_session()
    s["case_ref"] = data.get("case_ref", s["case_ref"])
    s["examiner"] = data.get("examiner", s["examiner"])
    s["agency"] = data.get("agency", s["agency"])
    return jsonify({"status": "ok"})


@app.route("/api/upload", methods=["POST"])
def api_upload():
    if "file" not in request.files:
        return jsonify({"error": "No file provided"}), 400

    files = request.files.getlist("file")
    results = []
    s = get_session()

    for f in files:
        if f.filename:
            safe_name = f"{uuid.uuid4().hex}_{f.filename}"
            path = UPLOAD_DIR / safe_name
            f.save(str(path))
            s["files"].append(str(path))
            results.append({"filename": f.filename, "status": "uploaded", "path": str(path)})

    return jsonify({"results": results, "total": len(results)})


@app.route("/api/delete", methods=["POST"])
def api_delete():
    data = request.json
    path = data.get("path")
    s = get_session()
    if path in s["files"]:
        s["files"].remove(path)
        if os.path.exists(path):
            os.remove(path)
        return jsonify({"status": "deleted"})
    return jsonify({"error": "File not found"}), 404


@app.route("/api/clear", methods=["POST"])
def api_clear():
    s = get_session()
    for path in s["files"]:
        if os.path.exists(path):
            os.remove(path)
    s["files"] = []
    s["chain_of_custody"] = []
    return jsonify({"status": "cleared"})


@app.route("/api/hash", methods=["POST"])
def api_hash():
    data = request.json
    algorithm = data.get("algorithm", "sha256")
    filepath = data.get("path")

    if filepath:
        # Single file
        try:
            result = hash_file(filepath, algorithm)
            # Also extract metadata
            try:
                meta = extract_metadata(filepath)
                result["metadata"] = meta
            except:
                result["metadata"] = {}
            return jsonify(result)
        except Exception as e:
            return jsonify({"error": str(e)}), 400
    else:
        # All files in session
        s = get_session()
        results = []
        for fp in s["files"]:
            try:
                r = hash_file(fp, algorithm)
                try:
                    r["metadata"] = extract_metadata(fp)
                except:
                    r["metadata"] = {}
                results.append(r)
            except Exception as e:
                results.append({"filename": os.path.basename(fp), "error": str(e)})
        return jsonify({"results": results, "algorithm": algorithm.upper()})


@app.route("/api/verify", methods=["POST"])
def api_verify():
    data = request.json
    filepath = data.get("path")
    expected = data.get("expected")
    algorithm = data.get("algorithm", "")

    try:
        result = verify_hash(filepath, expected, algorithm)
        try:
            result["metadata"] = extract_metadata(filepath)
        except:
            result["metadata"] = {}
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route("/api/report", methods=["POST"])
def api_report():
    """Generate a PDF report."""
    data = request.json
    s = get_session()

    # Update config
    s["case_ref"] = data.get("case_ref", s.get("case_ref", ""))
    s["examiner"] = data.get("examiner", s.get("examiner", ""))
    s["agency"] = data.get("agency", s.get("agency", ""))

    # Hash all files
    algorithm = data.get("algorithm", "sha256")
    files_data = []
    for fp in s["files"]:
        try:
            r = hash_file(fp, algorithm)
            try:
                r["metadata"] = extract_metadata(fp)
            except:
                r["metadata"] = {}
            files_data.append(r)
        except Exception as e:
            files_data.append({"filename": os.path.basename(fp), "error": str(e)})

    # Build report data
    report_data = {
        "case_ref": s.get("case_ref", "N/A"),
        "examiner": s.get("examiner", "N/A"),
        "agency": s.get("agency", "N/A"),
        "exam_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "files": files_data,
        "chain_of_custody": [
            {"action": f"Files uploaded for analysis ({len(s['files'])} files)",
             "by": s.get("examiner", "N/A"),
             "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
        ],
    }

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = str(REPORT_DIR / f"evidence_report_{timestamp}.pdf")

    try:
        output_path = generate_report(report_data, report_path)
        filename = os.path.basename(output_path)
        return jsonify({
            "status": "ok",
            "report": filename,
            "report_path": f"/download/{filename}",
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/download/<filename>")
def download(filename):
    return send_from_directory(str(REPORT_DIR), filename, as_attachment=True)


@app.route("/api/bulk_scan", methods=["POST"])
def api_bulk_scan():
    """Scan a directory for all files."""
    data = request.json
    directory = data.get("directory", "")
    if not directory or not os.path.isdir(directory):
        return jsonify({"error": "Invalid directory"}), 400

    files = []
    for root, dirs, filenames in os.walk(directory):
        for fn in filenames:
            fp = os.path.join(root, fn)
            if os.path.isfile(fp) and not fp.startswith("/proc") and not fp.startswith("/sys"):
                files.append(fp)
        if len(files) > 1000:
            break

    # Hash first 100
    results = hash_bulk(files[:100], data.get("algorithm", "sha256"))
    return jsonify({
        "total_found": len(files),
        "scanned": len(results),
        "results": results,
        "note": f"Found {len(files)} files. Scanned {len(results)}. Use single file for full scan."
    })


@app.route("/api/export_csv", methods=["POST"])
def api_export_csv():
    """Export hash results as CSV."""
    data = request.json
    results = data.get("results", [])
    algorithm = data.get("algorithm", "SHA256")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_path = str(OUTPUT_DIR / f"hash_export_{timestamp}.csv")

    with open(csv_path, "w") as f:
        f.write(f"Filename,Filepath,Size,{algorithm} Hash,Last Modified\n")
        for r in results:
            fn = r.get("filename", "").replace(",", "_")
            fp = r.get("filepath", "").replace(",", "_")
            sz = r.get("filesize_hr", "")
            h = r.get("hash", "")
            mod = r.get("modified", "")
            f.write(f"{fn},{fp},{sz},{h},{mod}\n")

    return jsonify({"status": "ok", "path": csv_path})


@app.route("/api/activate", methods=["POST"])
def api_activate():
    data = request.json
    name = data.get("name", "")
    email = data.get("email", "")
    key_text = data.get("key", "")
    success = activate_license(name, email, key_text)
    return jsonify({"success": success, "licensed": IS_LICENSED})


@app.route("/api/license_status", methods=["GET"])
def api_license_status():
    return jsonify({
        "licensed": IS_LICENSED,
        "licensed_to": LICENSED_TO if IS_LICENSED else "",
        "trial_max": TRIAL_MAX_FILES,
        "trial_used": len(get_session().get("files", [])),
    })


@app.route("/api/server_status", methods=["GET"])
def api_server_status():
    return jsonify({
        "version": "1.0.0",
        "name": "Evidence Integrity Validator",
        "uptime": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })


# ===== MAIN =====
if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8081
    print(f"""
╔══════════════════════════════════════════════════╗
║        EVIDENCE INTEGRITY VALIDATOR v1.0         ║
║     Forensic File Validation & Integrity Tool    ║
╠══════════════════════════════════════════════════╣
║  Server:  http://localhost:{port}                   ║
║  Open this in your browser to get started        ║
╚══════════════════════════════════════════════════╝
    """)
    app.run(host="127.0.0.1", port=port, debug=False, threaded=True)
