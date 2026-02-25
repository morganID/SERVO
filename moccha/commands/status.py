"""Command `moccha status`."""

import os
import sys

from moccha.daemon import PID_FILE, load_info


def register(subparsers) -> None:
    p = subparsers.add_parser("status", help="Cek apakah server jalan")
    p.set_defaults(_handler=run)


def run(args) -> None:  # noqa: ARG001 - signature untuk konsistensi
    info = load_info()
    if info and os.path.exists(PID_FILE):
        # Verify pid masih hidup
        try:
            pid = info["pid"]
            os.kill(pid, 0)
            print(f"🟢 RUNNING (PID: {pid})")
            print(f"   URL: {info['url']}")
        except OSError:
            print("🔴 STOPPED (stale PID file)")
    else:
        print("🔴 STOPPED")

