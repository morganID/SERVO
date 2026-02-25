"""Command `moccha restart`."""

import os
import sys
import uuid
import time

from moccha.daemon import stop_daemon


def register(subparsers) -> None:
    p = subparsers.add_parser("restart", help="Restart server")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument(
        "--token",
        required=False,
        default="",
        help="(deprecated) Ngrok/Cloudflare token, saat ini tidak dipakai",
    )
    p.add_argument("--key", default=None)
    p.add_argument("--workspace", default="/content")
    p.set_defaults(_handler=run)


def run(args) -> None:
    print("🔄 Restarting...")
    stop_daemon()
    time.sleep(2)
    # Re-invoke start
    os.execvp(
        sys.executable,
        [
            sys.executable,
            "-m",
            "moccha.cli",
            "start",
            "--port",
            str(args.port),
            "--token",
            args.token,
            "--key",
            args.key or str(uuid.uuid4()),
            "--workspace",
            args.workspace,
        ],
    )

