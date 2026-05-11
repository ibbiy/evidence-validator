import sys
import os

if getattr(sys, 'frozen', False):
    # PyInstaller temp directory
    MEIPASS = sys._MEIPASS
    os.environ['EVIDENCE_VALIDATOR_MEIPASS'] = MEIPASS
