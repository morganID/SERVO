"""
Daemon entry point - dipanggil oleh CLI sebagai subprocess.
File terpisah supaya bisa di-run dengan: python -m moccha.daemon_entry
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--api-key", type=str, required=True)
    parser.add_argument("--workspace", type=str, required=True)
    args = parser.parse_args()

    # Import dan jalankan daemon
    from .daemon import run_daemon

    run_daemon(
        port=args.port,
        api_key=args.api_key,
        workspace=args.workspace,
    )


if __name__ == "__main__":
    main()