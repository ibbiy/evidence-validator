#!/usr/bin/env python3
"""
Evidence Validator - Sales Page + Demo Server
Serves the landing page and a demo instance of the app.
"""

import sys
import os
from http.server import HTTPServer, SimpleHTTPRequestHandler
import threading
import webbrowser

SALES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "sales-page")
SALES_PORT = 8082


class SalesHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=SALES_DIR, **kwargs)

    def log_message(self, format, *args):
        print(f"[Sales Page] {args[0]} {args[1]} {args[2]}")


def run_sales_server():
    server = HTTPServer(("0.0.0.0", SALES_PORT), SalesHandler)
    print(f"📢 Sales page:    http://localhost:{SALES_PORT}")
    print(f"   Public URL:    http://5.189.179.230:{SALES_PORT}")
    print(f"   (if firewall allows port {SALES_PORT})")
    server.serve_forever()


if __name__ == "__main__":
    print("=" * 55)
    print("  Evidence Integrity Validator - Sales Server")
    print("=" * 55)
    print()
    run_sales_server()
