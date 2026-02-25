"""
CLI entry point.
Setelah install, command 'moccha' tersedia.

Usage:
    moccha start --token=xxx
    moccha stop
    moccha status
    moccha info
"""

import os
import sys
import json
import uuid
import argparse
import subprocess
import time
import threading

from .daemon import PID_FILE, INFO_FILE, load_info, stop_daemon


def _wait_and_print(timeout=30):
    """Background thread: tunggu server ready lalu print info."""
    for i in range(timeout):
        time.sleep(1)
        if os.path.exists(INFO_FILE):
            break

    info = load_info()
    if info:
        print()
        print("=" * 55)
        print("  ✅ SERVER RUNNING IN BACKGROUND!")
        print("=" * 55)
        print(f"  🌍 URL : {info['url']}")
        print(f"  🔑 Key : {info['api_key']}")
        print(f"  📍 Port: {info['port']}")
        print(f"  📂 PID : {info['pid']}")
        print("=" * 55)
        print()
        print("  📋 Quick test:")
        print(f'  curl -H "X-API-Key: {info["api_key"]}" {info["url"]}/status')
        print()
        print("  🛑 Stop:  moccha stop")
        print("  ℹ️  Info:  moccha info")
        print()
    else:
        print("\n❌ Server gagal start. Cek log: cat /tmp/moccha.log")


def main():
    parser = argparse.ArgumentParser(
        prog='moccha',
        description='just fun'
    )
    sub = parser.add_subparsers(dest='command', help='Command')

    # ── start ─────────────────────────────────────────────
    p_start = sub.add_parser('start', help='Start server di background')
    p_start.add_argument('--port', type=int, default=5000)
    p_start.add_argument('--token', required=True, help='Ngrok auth token')
    p_start.add_argument('--key', default=None,
                         help='Custom API key (auto-generate jika kosong)')
    p_start.add_argument('--workspace', default='/content')
    p_start.add_argument(
        '--wait', action='store_true', default=False,
        help='Blocking: tunggu sampai server ready baru return'
    )

    # ── stop ──────────────────────────────────────────────
    sub.add_parser('stop', help='Stop server')

    # ── status ────────────────────────────────────────────
    sub.add_parser('status', help='Cek apakah server jalan')

    # ── info ──────────────────────────────────────────────
    sub.add_parser('info', help='Tampilkan URL & API key')

    # ── restart ───────────────────────────────────────────
    p_restart = sub.add_parser('restart', help='Restart server')
    p_restart.add_argument('--port', type=int, default=5000)
    p_restart.add_argument('--token', required=True)
    p_restart.add_argument('--key', default=None)
    p_restart.add_argument('--workspace', default='/content')
    p_restart.add_argument('--wait', action='store_true', default=False)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # ══════════════════════════════════════════════════════
    if args.command == 'start':
        # Cek kalau sudah jalan
        if os.path.exists(PID_FILE):
            info = load_info()
            if info:
                print(f"⚠️  Server sudah jalan!")
                print(f"   URL: {info.get('url')}")
                print(f"   Key: {info.get('api_key')}")
                print(f"   Gunakan 'moccha stop' dulu kalau mau restart.")
                return                          # ← bukan sys.exit agar non-blocking

        api_key = args.key or str(uuid.uuid4())

        print("🚀 Starting server di background...")

        # ── Spawn daemon subprocess (detached) ────────────
        cmd = [
            sys.executable, '-c',
            f"""
import sys, os
sys.path.insert(0, '{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}')
from moccha.daemon import run_daemon
run_daemon(
    port={args.port},
    ngrok_token="{args.token}",
    api_key="{api_key}",
    workspace="{args.workspace}",
)
"""
        ]

        log_file = open('/tmp/moccha.log', 'w')
        subprocess.Popen(
            cmd,
            stdout=log_file,
            stderr=log_file,
            start_new_session=True,             # detach dari parent
        )

        # ── Non-blocking vs blocking ─────────────────────
        if args.wait:
            # Kalau user minta --wait, blocking di sini
            _wait_and_print(timeout=30)
        else:
            # DEFAULT: non-blocking!
            # Spawn daemon thread → print nanti, main() langsung return
            t = threading.Thread(target=_wait_and_print, args=(30,), daemon=True)
            t.start()

            print("   ✅ Daemon spawned! Server starting di background.")
            print("   📋 Cek nanti:  moccha info")
            print("   🛑 Stop:       moccha stop")
            print()
            # main() langsung return → cell / shell langsung bebas
            return

    # ══════════════════════════════════════════════════════
    elif args.command == 'stop':
        print("🛑 Stopping server...")
        if stop_daemon():
            print("✅ Server stopped.")
        else:
            print("⚠️  Server tidak sedang jalan.")

    # ══════════════════════════════════════════════════════
    elif args.command == 'status':
        info = load_info()
        if info and os.path.exists(PID_FILE):
            try:
                pid = info['pid']
                os.kill(pid, 0)
                print(f"🟢 RUNNING (PID: {pid})")
                print(f"   URL: {info['url']}")
            except OSError:
                print("🔴 STOPPED (stale PID file)")
        else:
            print("🔴 STOPPED")

    # ══════════════════════════════════════════════════════
    elif args.command == 'info':
        info = load_info()
        if info:
            print(json.dumps(info, indent=2))
        else:
            print("❌ Server tidak jalan. Start dulu: moccha start --token=xxx")

    # ══════════════════════════════════════════════════════
    elif args.command == 'restart':
        print("🔄 Restarting...")
        stop_daemon()
        time.sleep(2)
        os.execvp(sys.executable, [
            sys.executable, '-m', 'moccha.cli',
            'start',
            '--port', str(args.port),
            '--token', args.token,
            '--key', args.key or str(uuid.uuid4()),
            '--workspace', args.workspace,
        ])


if __name__ == '__main__':
    main()