"""Command `moccha info`."""

import json

from moccha.daemon import load_info


def register(subparsers) -> None:
    p = subparsers.add_parser("info", help="Tampilkan URL & API key")
    p.set_defaults(_handler=run)


def run(args) -> None:  # noqa: ARG001 - signature untuk konsistensi
    info = load_info()
    if info:
        print(json.dumps(info, indent=2))
    else:
        print("❌ Server tidak jalan. Start dulu: moccha start --token=xxx")

