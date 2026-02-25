"""Command `moccha stop`."""

from moccha.daemon import stop_daemon


def register(subparsers) -> None:
    p = subparsers.add_parser("stop", help="Stop server")
    p.set_defaults(_handler=run)


def run(args) -> None:  # noqa: ARG001 - signature untuk konsistensi
    print("🛑 Stopping server...")
    if stop_daemon():
        print("✅ Server stopped.")
    else:
        print("⚠️  Server tidak sedang jalan.")

