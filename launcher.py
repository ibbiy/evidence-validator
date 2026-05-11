"""Diagnostic wrapper for Evidence Validator - catches startup errors."""
import sys, os, traceback

# Write startup log
log_path = os.path.join(os.environ.get('TEMP', 'C:\\Windows\\Temp'), 'evidence_validator_debug.log')
try:
    # Try to import and run the actual app
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    from tools.hasher import hash_file, hash_bulk, verify_hash
    from tools.metadata import extract_metadata
    from tools.reporter import generate_report
    
    from flask import Flask, render_template, request, jsonify, send_from_directory, session, redirect, url_for
    
    with open(log_path, 'w') as f:
        f.write("All imports successful. Starting app...\n")
    
    # Import and run the actual app
    import app as evidence_app
    evidence_app.app.run(host='0.0.0.0', port=8081, debug=False, threaded=True)
    
except Exception as e:
    with open(log_path, 'w') as f:
        f.write(f"ERROR: {e}\n\nTraceback:\n{traceback.format_exc()}\n\nPython: {sys.version}\nPath: {sys.path}\nCWD: {os.getcwd()}\n")
    # Show error to user
    import ctypes
    ctypes.windll.user32.MessageBoxW(0, f"Error starting Evidence Validator:\n\n{e}\n\nDebug log: {log_path}", "Evidence Validator Error", 0x10)
    sys.exit(1)
