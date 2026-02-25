"""
CLI entry point.
Setelah install, command 'moccha' tersedia.

Usage:
    moccha start --token=xxx
    moccha stop
    moccha status
    moccha info
"""

import sys
import argparse

from .commands import register_commands, get_handler


def main():
    parser = argparse.ArgumentParser(
        prog="moccha",
        description="just fun",
    )
    sub = parser.add_subparsers(dest="command", help="Command")

    # Delegasikan definisi subcommand ke modul-modul terpisah
    register_commands(sub)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    handler = get_handler(args)
    if not handler:
        parser.print_help()
        sys.exit(1)

    handler(args)


if __name__ == '__main__':
    main()