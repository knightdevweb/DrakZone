#!/usr/bin/env python3
# dashboard.py
import os
import sys
import json
import glob
import threading
import subprocess
from flask import Flask, render_template, jsonify

app = Flask(__name__)

def get_latest_results():
    """Finds the most recent drakgrab_results_smtp_* folder and its JSON file."""
    folders = glob.glob("drakgrab_results_smtp_*")
    if not folders:
        return None, None
    
    folders.sort(reverse=True)
    latest_folder = folders[0]
    
    json_files = glob.glob(os.path.join(latest_folder, "json", "*.json"))
    if not json_files:
        return latest_folder, None
        
    json_files.sort(reverse=True)
    latest_json = json_files[0]
    
    with open(latest_json, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    return latest_folder, data

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/data')
def api_data():
    folder, data = get_latest_results()
    if not data:
        return jsonify({"error": "No scan results found. Waiting for drakzone.py to generate data..."}), 404
    
    total = len(data)
    smtp_found = len([r for r in data if r.get('status') == 'ok'])
    open_relays = len([r for r in data if r.get('open_relay')])
    high_value = len([r for r in data if r.get('score', 0) >= 30 or r.get('open_relay')])
    
    summary = {
        "total": total,
        "smtp_found": smtp_found,
        "open_relays": open_relays,
        "high_value": high_value,
        "folder": folder
    }
    
    return jsonify({"summary": summary, "results": data})

def launch_drakzone():
    """Launches drakzone.py in the background, keeping terminal stdin/stdout active."""
    # Ensure we use the exact same Python executable and path
    script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'drakzone.py')
    
    print("\n" + "="*70)
    print("🚀 LAUNCHING DRAKZONE.py IN BACKGROUND...")
    print("👉 Please complete the CLI prompts below to start the scan.")
    print("🌐 The Web Dashboard is live at: http://127.0.0.1:5090")
    print("="*70 + "\n")
    
    # Popen inherits the current terminal's stdin/stdout so you can interact with the CLI
    subprocess.Popen([sys.executable, script_path])

if __name__ == '__main__':
    # 1. Start the drakzone.py CLI script in a background thread
    scan_thread = threading.Thread(target=launch_drakzone, daemon=True)
    scan_thread.start()
    
    # 2. Start the Flask web dashboard
    # Note: debug=False is required so Flask's reloader doesn't kill the background thread
    print("\n📡 Starting DrakZone Web Dashboard...")
    app.run(host='127.0.0.1', port=5090, debug=False, use_reloader=False)