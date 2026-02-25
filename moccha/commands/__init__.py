"""Struktur command-line `moccha`.

Setiap command didefinisikan di modul terpisah agar mudah dikembangkan.
"""

from . import start, stop, status, info, restart


def register_commands(subparsers) -> None:
    """Daftarkan semua subcommand ke argparse."""
    for mod in (start, stop, status, info, restart):
        mod.register(subparsers)


def get_handler(args):
    """Ambil handler function dari atribut yang di-set oleh register()."""
    return getattr(args, "_handler", None)

