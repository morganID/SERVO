"""Route untuk async task, variables, dan history."""

from flask import request, jsonify

from moccha.core.auth import require_key
from moccha.core.system import async_execute
from moccha.core.history import get_safe_variables


def register_routes(app, config) -> None:
    @app.route("/async-execute", methods=["POST"])
    @require_key(config.api_key)
    def async_exec():
        code = (request.json or {}).get("code", "")
        tid, task = async_execute(code, config.vars)
        config.tasks[tid] = task
        return jsonify({"task_id": tid, "status": "running"})

    @app.route("/task/<tid>")
    @require_key(config.api_key)
    def get_task(tid):
        task = config.tasks.get(tid)
        return jsonify(task) if task else (jsonify({"error": "Not found"}), 404)

    @app.route("/variables")
    @require_key(config.api_key)
    def variables():
        return jsonify(get_safe_variables(config.vars))

    @app.route("/variables/<name>", methods=["DELETE"])
    @require_key(config.api_key)
    def del_var(name):
        if name in config.vars:
            del config.vars[name]
            return jsonify({"deleted": name})
        return jsonify({"error": "Not found"}), 404

    @app.route("/history")
    @require_key(config.api_key)
    def history():
        n = int(request.args.get("limit", 20))
        return jsonify(config.history[-n:])

