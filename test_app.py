"""Minimal test app - just starts Flask on port 8081"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from flask import Flask
app = Flask(__name__)
@app.route('/')
def hello():
    return 'Evidence Validator is running!'
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8081, debug=False)
