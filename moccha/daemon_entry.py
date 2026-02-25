"""
Daemon entry point.
Run: python -m moccha.daemon_entry --port 5000 --api-key KEY --workspace DIR
"""

import argparse


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--api-key", type=str, required=True)
    parser.add_argument("--workspace", type=str, required=True)
    args = parser.parse_args()

    from moccha.daemon import run_daemon

    run_daemon(
        port=args.port,
        api_key=args.api_key,
        workspace=args.workspace,
    )


# ✅ Ini yang dipanggil oleh: python -m moccha.daemon_entry
if __name__ == "__main__":
    main()