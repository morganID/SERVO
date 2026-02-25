"""Route untuk info service & status dasar."""

from datetime import datetime

from flask import jsonify

from moccha.core.auth import require_key
from moccha.core.system import get_system_info


def register_routes(app, config) -> None:
    @app.route("/")
    def home():
        return jsonify(
            {
                "service": "moccha",
                "version": "2.0.0",
                "status": "running",
                "uptime": str(datetime.now() - config.start_time),
            }
        )

    @app.route("/ping")
    def ping():
        return jsonify({"pong": True})

    @app.route("/status")
    @require_key(config.api_key)
    def status():
        return jsonify(
            {
                "uptime": str(datetime.now() - config.start_time),
                "system": get_system_info(),
                "executions": len(config.history),
                "variables": len(config.vars),
            }
        )

