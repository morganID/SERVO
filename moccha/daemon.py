"""
Background daemon - pakai cloudflared tunnel.
"""

import os
import sys
import time
import json
import signal
import threading
import subprocess
import requests as req
from datetime import datetime

PID_FILE = "/tmp/moccha.pid"
INFO_FILE = "/tmp/moccha.json"
LOG_FILE = "/tmp/moccha.log"


def log(msg):
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
    if not os.path.exists(PID_FILE):
        return False
    try:
        with open(PID_FILE) as f:
            pid = int(f.read().strip())
        os.kill(pid, 0)
        return True
    except (ProcessLookupError, ValueError, OSError, PermissionError):
        try:
            os.remove(PID_FILE)
        except:
            pass
        return False


def wait_for_flask(port, timeout=15):
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


def run_daemon(port, api_key=None, workspace=None):
    """Jalankan server sebagai daemon process."""
    # Import DISINI, bukan di top-level (avoid circular)
    from moccha.app import create_app
    from moccha.tunnel import start_tunnel, stop_tunnel, is_tunnel_alive

    with open(PID_FILE, 'w') as f:
        f.write(str(os.getpid()))

    log(f"🚀 Daemon starting (PID: {os.getpid()})")
    log(f"   Port: {port}")
    log(f"   Workspace: {workspace}")

    # ── 1) Start Flask ────────────────────────────────────
    app = create_app(api_key=api_key, workspace=workspace)

    flask_thread = threading.Thread(
        target=lambda: app.run(host='0.0.0.0', port=port, use_reloader=False),
        daemon=True
    )
    flask_thread.start()

    log("⏳ Waiting for Flask...")
    if wait_for_flask(port, timeout=15):
        log("✅ Flask is ready")
    else:
        log("⚠️ Flask may not be ready, continuing...")

    # ── 2) Start Cloudflared Tunnel ───────────────────────
    public_url = f"http://localhost:{port}"

    log("📡 Starting cloudflared tunnel...")
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            public_url = start_tunnel(port)
            log(f"✅ Tunnel active: {public_url}")
            break
        except Exception as e:
            log(f"❌ Tunnel attempt {attempt}/{max_retries}: {e}")
            if attempt < max_retries:
                log("   Retrying in 3s...")
                time.sleep(3)
            else:
                log(f"❌ All tunnel attempts failed")
                log(f"⚠️ Fallback: {public_url}")

    # ── 3) Save info ─────────────────────────────────────
    info = {
        "pid": os.getpid(),
        "port": port,
        "api_key": api_key,
        "url": public_url,
        "tunnel": "cloudflared",
        "started": datetime.now().isoformat(),
        "workspace": workspace,
    }
    save_info(info)

    print(json.dumps(info))
    sys.stdout.flush()
    log(f"🌐 URL: {public_url}")

    # ── 4) Keep-alive + tunnel monitor ────────────────────
    def keepalive():
        while True:
            try:
                req.get(f'http://localhost:{port}/ping', timeout=5)
            except:
                pass

            if not is_tunnel_alive():
                log("⚠️ Tunnel died, restarting...")
                try:
                    new_url = start_tunnel(port)
                    log(f"✅ Tunnel restarted: {new_url}")
                    current_info = load_info() or info
                    current_info["url"] = new_url
                    save_info(current_info)
                except Exception as e:
                    log(f"❌ Tunnel restart failed: {e}")

            time.sleep(30)

    threading.Thread(target=keepalive, daemon=True).start()

    # ── 5) Handle SIGTERM ─────────────────────────────────
    def handle_stop(signum, frame):
        log("🛑 Stopping daemon...")
        stop_tunnel()
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

    from moccha.tunnel import stop_tunnel
    stop_tunnel()

    return True