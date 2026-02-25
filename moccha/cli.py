"""
CLI entry point — fully non-blocking.

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

from .daemon import PID_FILE, INFO_FILE, load_info, stop_daemon


def main():
    parser = argparse.ArgumentParser(prog='moccha')
    sub = parser.add_subparsers(dest='command')

    p_start = sub.add_parser('start')
    p_start.add_argument('--port', type=int, default=5000)
    p_start.add_argument('--token', required=True)
    p_start.add_argument('--key', default=None)
    p_start.add_argument('--workspace', default='/content')

    sub.add_parser('stop')
    sub.add_parser('status')
    sub.add_parser('info')

    p_restart = sub.add_parser('restart')
    p_restart.add_argument('--port', type=int, default=5000)
    p_restart.add_argument('--token', required=True)
    p_restart.add_argument('--key', default=None)
    p_restart.add_argument('--workspace', default='/content')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    # ══════════════════════════════════════════════════════
    if args.command == 'start':
        if os.path.exists(PID_FILE):
            info = load_info()
            if info:
                print(f"⚠️  Sudah jalan!")
                print(f"   URL: {info.get('url')}")
                print(f"   Key: {info.get('api_key')}")
                return

        api_key = args.key or str(uuid.uuid4())

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

        # ━━━ SPAWN & EXIT IMMEDIATELY ━━━━━━━━━━━━━━━━━━━
        log = open('/tmp/moccha.log', 'w')
        subprocess.Popen(
            cmd,
            stdout=log,
            stderr=log,
            stdin=subprocess.DEVNULL,      # no stdin
            start_new_session=True,        # detach completely
        )
        log.close()                        # parent lepas file handle

        # LANGSUNG PRINT & RETURN — ZERO SLEEP
        print("🚀 Server spawned di background!")
        print(f"   🔑 Key: {api_key}")
        print()
        print("   ⏳ Tunggu ~10 detik lalu cek:")
        print("   → !moccha info")
        return  # ← CELL LANGSUNG SELESAI

    # ══════════════════════════════════════════════════════
    elif args.command == 'stop':
        print("🛑 Stopping...")
        if stop_daemon():
            print("✅ Stopped.")
        else:
            print("⚠️  Tidak sedang jalan.")

    # ══════════════════════════════════════════════════════
    elif args.command == 'status':
        info = load_info()
        if info and os.path.exists(PID_FILE):
            try:
                os.kill(info['pid'], 0)
                print(f"🟢 RUNNING (PID: {info['pid']})")
                print(f"   URL: {info['url']}")
                print(f"   Key: {info['api_key']}")
            except OSError:
                print("🔴 STOPPED (stale PID)")
        else:
            print("🔴 STOPPED")

    # ══════════════════════════════════════════════════════
    elif args.command == 'info':
        info = load_info()
        if info:
            print("=" * 55)
            print("  ✅ SERVER INFO")
            print("=" * 55)
            print(f"  🌍 URL : {info['url']}")
            print(f"  🔑 Key : {info['api_key']}")
            print(f"  📍 Port: {info['port']}")
            print(f"  📂 PID : {info['pid']}")
            print("=" * 55)
            print()
            print("  📋 Test:")
            print(f'  curl -H "X-API-Key: {info["api_key"]}" {info["url"]}/status')
        else:
            print("❌ Belum jalan. Start dulu: moccha start --token=xxx")

    # ══════════════════════════════════════════════════════
    elif args.command == 'restart':
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