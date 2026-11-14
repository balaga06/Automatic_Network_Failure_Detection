import os
import sys
import threading
import subprocess
import webbrowser
import time

# Fix base path for EXE
if getattr(sys, 'frozen', False):
    base_path = sys._MEIPASS
else:
    base_path = os.path.dirname(__file__)

def start_monitoring():
    monitoring_path = os.path.join(base_path, "monitoring.py")
    subprocess.Popen(["python", monitoring_path])

def open_browser():
    time.sleep(2)
    webbrowser.open("http://localhost:5000")

threading.Thread(target=start_monitoring).start()
threading.Thread(target=open_browser).start()

from dashboard.app import app
from waitress import serve

serve(app, host="0.0.0.0", port=5000)