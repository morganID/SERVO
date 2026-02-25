"""Registrasi routing Flask, dipecah per modul."""

from . import system, execution, files, tasks, services


def register_all_routes(app, config) -> None:
    """Daftarkan semua route ke app."""
    system.register_routes(app, config)
    execution.register_routes(app, config)
    files.register_routes(app, config)
    tasks.register_routes(app, config)
    services.register_routes(app, config)

