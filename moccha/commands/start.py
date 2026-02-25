"""Command `moccha start`."""

import os
import sys
import uuid
import subprocess
import time

from moccha.daemon import PID_FILE, INFO_FILE, load_info


def register(subparsers) -> None:
    p = subparsers.add_parser("start", help="Start server di background")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument(
        "--token",
        required=False,
        default="",
        help="(deprecated) Ngrok/Cloudflare token, saat ini tidak dipakai",
    )
    p.add_argument(
        "--key",
        default=None,
        help="Custom API key (auto-generate jika kosong)",
    )
    p.add_argument("--workspace", default="/content")
    p.set_defaults(_handler=run)


def run(args) -> None:
    # Cek kalau sudah jalan
    if os.path.exists(PID_FILE):
        info = load_info()
        if info:
            print("⚠️  Server sudah jalan!")
            print(f"   URL: {info.get('url')}")
            print(f"   Key: {info.get('api_key')}")
            print("   Gunakan 'moccha stop' dulu kalau mau restart.")
            sys.exit(0)

    api_key = args.key or str(uuid.uuid4())

    print("🚀 Starting server di background...")

    cmd = [
        sys.executable,
        "-c",
        f"""
import sys
sys.path.insert(0, '{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}')
from moccha.daemon import run_daemon
run_daemon(
    port={args.port},
    ngrok_token="{args.token}",
    api_key="{api_key}",
    workspace="{args.workspace}",
)
""",
    ]

    # Start sebagai background process (detached)
    log_file = open("/tmp/moccha.log", "w")
    subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=log_file,
        start_new_session=True,
    )

    # Tunggu sampai info file muncul
    print("   ⏳ Waiting for server...", end="", flush=True)
    for _ in range(30):
        time.sleep(1)
        print(".", end="", flush=True)
        if os.path.exists(INFO_FILE):
            break

    print()

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
        print("❌ Server gagal start. Cek log: cat /tmp/moccha.log")
        sys.exit(1)

