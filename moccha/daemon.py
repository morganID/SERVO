"""CLI entry point - updated for cloudflared."""

import os
import sys
import json
import time
import signal
import argparse
import subprocess
import secrets

from .daemon import (
    run_daemon, stop_daemon, is_running,
    load_info, PID_FILE, INFO_FILE, LOG_FILE
)


def generate_api_key():
    return secrets.token_hex(16)


def cmd_start(args):
    """Start the server."""
    if is_running():
        info = load_info()
        if info:
            print(f"🟢 Already running (PID: {info.get('pid')})")
            print(f"   URL: {info.get('url')}")
            print(f"   Key: {info.get('api_key')}")
            return
        print("⚠️ PID file exists but server may be dead. Cleaning up...")
        try:
            os.remove(PID_FILE)
        except:
            pass

    port = args.port or 5000
    api_key = args.api_key or generate_api_key()
    workspace = args.workspace or os.path.expanduser("~/moccha_workspace")

    os.makedirs(workspace, exist_ok=True)

    print(f"🚀 Starting server...")
    print(f"   Port: {port}")
    print(f"   Workspace: {workspace}")
    print(f"   Tunnel: cloudflared (free, no token needed)")

    # ✅ Tidak perlu ngrok token lagi!
    # Jalankan daemon di background
    env = os.environ.copy()

    # Redirect stderr ke log file
    log_f = open(LOG_FILE, 'a')

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "moccha.daemon_entry",
            "--port", str(port),
            "--api-key", api_key,
            "--workspace", workspace,
        ],
        stdout=subprocess.PIPE,
        stderr=log_f,
        env=env,
        start_new_session=True,
    )

    # Tunggu info file muncul
    print("⏳ Waiting for server to start...")

    for i in range(30):
        time.sleep(2)
        info = load_info()
        if info and info.get("url"):
            url = info["url"]
            print(f"\n{'='*55}")
            print(f"  🟢 Server is running!")
            print(f"  🌐 URL: {url}")
            print(f"  🔑 Key: {api_key}")
            print(f"  📂 Workspace: {workspace}")
            print(f"  🔧 Tunnel: cloudflared")
            print(f"{'='*55}")

            if "localhost" in url:
                print(f"\n  ⚠️ Tunnel belum aktif, cek log:")
                print(f"     cat {LOG_FILE}")

            return

    # Timeout
    print(f"\n⚠️ Server mungkin jalan tapi tunnel belum ready")
    print(f"   Cek log: cat {LOG_FILE}")
    print(f"   Cek status: moccha status")


def cmd_stop(args):
    """Stop the server."""
    if not is_running():
        print("🔴 Server is not running")
        return

    info = load_info()
    if stop_daemon():
        print("🛑 Server stopped")
    else:
        print("⚠️ Failed to stop server cleanly")
        # Force kill
        subprocess.run(["killall", "cloudflared"], capture_output=True)
        try:
            os.remove(PID_FILE)
            os.remove(INFO_FILE)
        except:
            pass
        print("🧹 Cleaned up")


def cmd_status(args):
    """Show server status."""
    if is_running():
        info = load_info()
        if info:
            print(f"🟢 RUNNING (PID: {info.get('pid')})")
            print(f"   URL: {info.get('url')}")
            print(f"   Key: {info.get('api_key')}")
            print(f"   Tunnel: {info.get('tunnel', 'unknown')}")
            print(f"   Started: {info.get('started')}")
            print(f"   Workspace: {info.get('workspace')}")
        else:
            print("🟡 Process running but no info file")
    else:
        print("🔴 NOT RUNNING")


def cmd_restart(args):
    """Restart the server."""
    print("🔄 Restarting...")
    cmd_stop(args)
    time.sleep(3)
    cmd_start(args)


def cmd_logs(args):
    """Show logs."""
    if os.path.exists(LOG_FILE):
        lines = args.lines or 50
        result = subprocess.run(
            ["tail", "-n", str(lines), LOG_FILE],
            capture_output=True, text=True
        )
        print(result.stdout)
    else:
        print("No log file found")


def cmd_url(args):
    """Show current URL."""
    info = load_info()
    if info and info.get("url"):
        print(info["url"])
    else:
        print("No URL available. Server may not be running.")


def main():
    parser = argparse.ArgumentParser(
        prog="moccha",
        description="Moccha Server Manager"
    )
    sub = parser.add_subparsers(dest="command")

    # start
    p_start = sub.add_parser("start", help="Start server")
    p_start.add_argument("--port", type=int, default=5000)
    p_start.add_argument("--api-key", type=str, default=None)
    p_start.add_argument("--workspace", type=str, default=None)
    # ✅ ngrok-token tetap ada tapi opsional & diabaikan
    p_start.add_argument("--ngrok-token", type=str, default=None,
                         help="(deprecated, ignored - using cloudflared)")
    p_start.set_defaults(func=cmd_start)

    # stop
    p_stop = sub.add_parser("stop", help="Stop server")
    p_stop.set_defaults(func=cmd_stop)

    # status
    p_status = sub.add_parser("status", help="Show status")
    p_status.set_defaults(func=cmd_status)

    # restart
    p_restart = sub.add_parser("restart", help="Restart server")
    p_restart.add_argument("--port", type=int, default=5000)
    p_restart.add_argument("--api-key", type=str, default=None)
    p_restart.add_argument("--workspace", type=str, default=None)
    p_restart.set_defaults(func=cmd_restart)

    # logs
    p_logs = sub.add_parser("logs", help="Show logs")
    p_logs.add_argument("-n", "--lines", type=int, default=50)
    p_logs.set_defaults(func=cmd_logs)

    # url
    p_url = sub.add_parser("url", help="Show current URL")
    p_url.set_defaults(func=cmd_url)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()