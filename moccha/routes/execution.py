"""Route untuk eksekusi kode & shell."""

from flask import request, jsonify

from moccha.core.auth import require_key
from moccha.core.system import (
    execute_code,
    run_shell_command,
    install_package,
)
from moccha.core.history import add_history


def register_routes(app, config) -> None:
    @app.route("/execute", methods=["POST"])
    @require_key(config.api_key)
    def execute():
        data = request.json or {}
        code = data.get("code", "")
        if not code.strip():
            return jsonify({"error": "No code"}), 400

        result = execute_code(code, config.vars)
        add_history(config.history, "execute", code, result["output"], result["success"])

        for k, v in result["variables"].items():
            config.vars[k] = v

        return jsonify(result)

    @app.route("/shell", methods=["POST"])
    @require_key(config.api_key)
    def shell():
        data = request.json or {}
        cmd = data.get("command", "")
        timeout = min(data.get("timeout", 120), 600)
        if not cmd.strip():
            return jsonify({"error": "No command"}), 400

        result = run_shell_command(cmd, str(config.workspace), timeout)
        add_history(
            config.history,
            "shell",
            cmd,
            result.get("stdout"),
            result.get("success", False),
        )
        return jsonify(result)

    @app.route("/install", methods=["POST"])
    @require_key(config.api_key)
    def install():
        pkg = (request.json or {}).get("package", "")
        if not pkg:
            return jsonify({"error": "No package"}), 400
        result = install_package(pkg)
        return jsonify(result)

