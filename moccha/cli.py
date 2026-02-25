"""CLI entry point."""

import os
import sys
import json
import time
import signal
import argparse
import subprocess
import secrets

# ✅ FIX: Import langsung dari module, BUKAN relative
from moccha.daemon import (
    run_daemon, stop_daemon, is_running,
    load_info, PID_FILE, INFO_FILE, LOG_FILE
)


def generate_api_key():
    return secrets.token_hex(16)


def cmd_start(args):
    if is_running():
        info = load_info()
        if info:
            print(f"🟢 Already running (PID: {info.get('pid')})")
            print(f"   URL: {info.get('url')}")
            print(f"   Key: {info.get('api_key')}")
            return
        print("⚠️ Stale PID file, cleaning up...")
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
    print(f"   Tunnel: cloudflared (free)")

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
        env=os.environ.copy(),
        start_new_session=True,
    )

    print("⏳ Waiting for server...")

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
            print(f"{'='*55}")

            if "localhost" in url:
                print(f"\n  ⚠️ Tunnel not active yet, check:")
                print(f"     !cat {LOG_FILE}")
            return

    print(f"\n⚠️ Timeout. Check: !cat {LOG_FILE}")


def cmd_stop(args):
    if not is_running():
        print("🔴 Not running")
        return

    if stop_daemon():
        print("🛑 Server stopped")
    else:
        print("⚠️ Force cleanup...")
        subprocess.run(["killall", "cloudflared"], capture_output=True)
        for f in [PID_FILE, INFO_FILE]:
            try:
                os.remove(f)
            except:
                pass
        print("🧹 Done")


def cmd_status(args):
    if is_running():
        info = load_info()
        if info:
            print(f"🟢 RUNNING (PID: {info.get('pid')})")
            print(f"   URL: {info.get('url')}")
            print(f"   Key: {info.get('api_key')}")
            print(f"   Tunnel: {info.get('tunnel', 'cloudflared')}")
            print(f"   Started: {info.get('started')}")
        else:
            print("🟡 Running but no info file")
    else:
        print("🔴 NOT RUNNING")


def cmd_restart(args):
    print("🔄 Restarting...")
    cmd_stop(args)
    time.sleep(3)
    cmd_start(args)


def cmd_logs(args):
    if os.path.exists(LOG_FILE):
        n = args.lines or 50
        result = subprocess.run(
            ["tail", "-n", str(n), LOG_FILE],
            capture_output=True, text=True
        )
        print(result.stdout)
    else:
        print("No log file found")


def cmd_url(args):
    info = load_info()
    if info and info.get("url"):
        print(info["url"])
    else:
        print("No URL available")


def main():
    parser = argparse.ArgumentParser(prog="moccha")
    sub = parser.add_subparsers(dest="command")

    p = sub.add_parser("start")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--api-key", type=str, default=None)
    p.add_argument("--workspace", type=str, default=None)
    p.add_argument("--ngrok-token", type=str, default=None,
                   help="(deprecated, ignored)")
    p.set_defaults(func=cmd_start)

    p = sub.add_parser("stop")
    p.set_defaults(func=cmd_stop)

    p = sub.add_parser("status")
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("restart")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--api-key", type=str, default=None)
    p.add_argument("--workspace", type=str, default=None)
    p.set_defaults(func=cmd_restart)

    p = sub.add_parser("logs")
    p.add_argument("-n", "--lines", type=int, default=50)
    p.set_defaults(func=cmd_logs)

    p = sub.add_parser("url")
    p.set_defaults(func=cmd_url)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()