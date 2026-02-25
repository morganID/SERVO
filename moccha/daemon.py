"""
Background daemon - inti dari "install & run di background".
Jalankan Flask + ngrok + keepalive sebagai subprocess/nohup.
"""

import os
import sys
import time
import json
import signal
import threading
import requests
import subprocess
from datetime import datetime

PID_FILE = "/tmp/moccha.pid"
INFO_FILE = "/tmp/moccha.json"


def save_info(data):
    """Simpan info server ke file agar bisa dibaca dari cell lain."""
    with open(INFO_FILE, 'w') as f:
        json.dump(data, f)


def load_info():
    """Baca info server."""
    try:
        with open(INFO_FILE) as f:
            return json.load(f)
    except:
        return None


def is_running():
    """Cek apakah server sudah jalan."""
    if not os.path.exists(PID_FILE):
        return False
    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)  # cek pid masih hidup
        return True
    except (ProcessError, ValueError, OSError):
        return False


def run_daemon(port, ngrok_token, api_key, workspace):
    """
    Jalankan server sebagai daemon process.
    Dipanggil oleh CLI, berjalan di background.
    """
    from .app import create_app
    from .tunnel import start_ngrok

    # Simpan PID
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    # ── 1) Start Flask di thread ──────────────────────────
    app = create_app(api_key=api_key, workspace=workspace)

    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False),
        daemon=True
    )
    flask_thread.start()
    time.sleep(2)

    # ── 2) Start ngrok ────────────────────────────────────
    public_url = "http://localhost:" + str(port)
    try:
        public_url = start_ngrok(port, ngrok_token)
    except Exception as e:
        print(f"⚠️ Ngrok error: {e}", file=sys.stderr)

    # ── 3) Simpan info ke file ────────────────────────────
    info = {
        "pid": os.getpid(),
        "port": port,
        "api_key": api_key,
        "url": public_url,
        "started": datetime.now().isoformat(),
        "workspace": workspace,
    }
    save_info(info)

    # Print info ke stdout (akan di-capture atau redirect)
    print(json.dumps(info))
    sys.stdout.flush()

    # ── 4) Keep-alive loop ────────────────────────────────
    def keepalive():
        while True:
            try:
                requests.get(f'http://localhost:{port}/ping', timeout=5)
            except:
                pass
            time.sleep(30)

    threading.Thread(target=keepalive, daemon=True).start()

    # ── 5) Handle SIGTERM untuk graceful stop ─────────────
    def handle_stop(signum, frame):
        from .tunnel import stop_ngrok
        stop_ngrok()
        try:
            os.remove(PID_FILE)
            os.remove(INFO_FILE)
        except:
            pass
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)

    # ── 6) Block forever (daemon process) ─────────────────
    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        handle_stop(None, None)


def stop_daemon():
    """Stop background server."""
    if not os.path.exists(PID_FILE):
        return False

    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, signal.SIGTERM)
        time.sleep(2)
    except:
        pass

    # Cleanup
    for f in [PID_FILE, INFO_FILE]:
        try:
            os.remove(f)
        except:
            pass

    # Kill ngrok juga
    from .tunnel import stop_ngrok
    stop_ngrok()

    return True