"""
Background daemon - FIXED VERSION
"""

import os
import sys
import time
import json
import signal
import threading
import subprocess
from datetime import datetime

PID_FILE = "/tmp/moccha.pid"
INFO_FILE = "/tmp/moccha.json"
LOG_FILE = "/tmp/moccha.log"


def log(msg):
    """Log ke file DAN stderr supaya bisa di-debug."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line, file=sys.stderr)
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(line + "\n")
    except:
        pass


def save_info(data):
    with open(INFO_FILE, 'w') as f:
        json.dump(data, f)


def load_info():
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
        os.kill(pid, 0)
        return True
    # ✅ FIX: ProcessError → ProcessLookupError
    except (ProcessLookupError, ValueError, OSError, PermissionError):
        # PID file ada tapi proses sudah mati, cleanup
        try:
            os.remove(PID_FILE)
        except:
            pass
        return False


def wait_for_flask(port, timeout=10):
    """Tunggu sampai Flask benar-benar ready."""
    import requests as req
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = req.get(f"http://127.0.0.1:{port}/ping", timeout=2)
            if r.status_code == 200:
                return True
        except:
            pass
        time.sleep(0.5)
    return False


def run_daemon(port, ngrok_token, api_key, workspace):
    """
    Jalankan server sebagai daemon process.
    """
    from .app import create_app
    from .tunnel import start_ngrok

    # Simpan PID
    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    log(f"🚀 Daemon starting (PID: {os.getpid()})")
    log(f"   Port: {port}")
    log(f"   Workspace: {workspace}")
    log(f"   Ngrok token: {'SET (' + ngrok_token[:8] + '...)' if ngrok_token else 'NOT SET!'}")

    # ── 1) Start Flask di thread ──────────────────────────
    app = create_app(api_key=api_key, workspace=workspace)

    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False),
        daemon=True
    )
    flask_thread.start()

    # ✅ FIX: Tunggu Flask benar-benar ready, bukan cuma sleep
    log("⏳ Waiting for Flask to be ready...")
    if wait_for_flask(port, timeout=15):
        log("✅ Flask is ready!")
    else:
        log("⚠️  Flask might not be ready yet, continuing anyway...")

    # ── 2) Start ngrok ────────────────────────────────────
    public_url = f"http://localhost:{port}"

    if not ngrok_token:
        log("❌ NGROK TOKEN IS EMPTY!")
        log("   Set via: moccha start --ngrok-token YOUR_TOKEN")
        log(f"   Fallback to: {public_url}")
    else:
        # ✅ FIX: Kill stale ngrok processes first
        log("🔄 Killing any stale ngrok processes...")
        subprocess.run(["killall", "ngrok"], capture_output=True)
        time.sleep(2)

        # ✅ FIX: Retry logic
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                log(f"📡 Ngrok attempt {attempt}/{max_retries}...")
                public_url = start_ngrok(port, ngrok_token)
                log(f"✅ Ngrok connected: {public_url}")
                break
            except Exception as e:
                log(f"❌ Ngrok attempt {attempt} failed: {type(e).__name__}: {e}")
                if attempt < max_retries:
                    log(f"   Retrying in 3s...")
                    # Kill ngrok lagi sebelum retry
                    subprocess.run(["killall", "ngrok"], capture_output=True)
                    time.sleep(3)
                else:
                    log(f"❌ All ngrok attempts failed!")
                    log(f"⚠️  Fallback to: {public_url}")

    # ── 3) Simpan info ke file ────────────────────────────
    info = {
        "pid": os.getpid(),
        "port": port,
        "api_key": api_key,
        "url": public_url,
        "started": datetime.now().isoformat(),
        "workspace": workspace,
        "ngrok_connected": not public_url.startswith("http://localhost"),
    }
    save_info(info)

    # Print info ke stdout
    print(json.dumps(info))
    sys.stdout.flush()

    log(f"📋 Server info saved to {INFO_FILE}")
    log(f"🌐 URL: {public_url}")

    # ── 4) Keep-alive loop ────────────────────────────────
    import requests as req

    def keepalive():
        while True:
            try:
                req.get(f'http://localhost:{port}/ping', timeout=5)
            except:
                pass
            time.sleep(30)

    threading.Thread(target=keepalive, daemon=True).start()

    # ── 5) Handle SIGTERM ─────────────────────────────────
    def handle_stop(signum, frame):
        log("🛑 Stopping daemon...")
        from .tunnel import stop_ngrok
        stop_ngrok()
        for fpath in [PID_FILE, INFO_FILE]:
            try:
                os.remove(fpath)
            except:
                pass
        log("👋 Daemon stopped")
        sys.exit(0)

    signal.signal(signal.SIGTERM, handle_stop)
    signal.signal(signal.SIGINT, handle_stop)

    # ── 6) Block forever ──────────────────────────────────
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

    for fpath in [PID_FILE, INFO_FILE]:
        try:
            os.remove(fpath)
        except:
            pass

    from .tunnel import stop_ngrok
    stop_ngrok()

    return True