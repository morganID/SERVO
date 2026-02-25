"""Route untuk service eksternal (Deluge, JDownloader, Mega, dll)."""

from flask import jsonify, request

from moccha.core.auth import require_key
from moccha.services import list_services, dispatch_action


def _status_from_error_code(code):
    if code in ("not_configured", "library_missing"):
        return 503
    if code in ("invalid_request",):
        return 400
    if code in ("unknown_action", "unknown_service"):
        return 404
    return 500


def register_routes(app, config) -> None:
    @app.route("/services")
    @require_key(config.api_key)
    def services_list():
        return jsonify({"services": list_services()})

    @app.route("/services/<name>/action", methods=["POST"])
    @require_key(config.api_key)
    def service_action(name):
        data = request.json or {}
        action = data.get("action") or "ping"
        payload = data.get("payload") or {}

        try:
            result = dispatch_action(name, action, payload, config)
            status = 200
            if isinstance(result, dict) and not result.get("ok", True):
                status = _status_from_error_code(result.get("error_code"))
            body = {
                "service": name,
                "action": action,
                **result,
            }
            return jsonify(body), status
        except KeyError:
            return (
                jsonify(
                    {
                        "service": name,
                        "action": action,
                        "ok": False,
                        "error_code": "unknown_service",
                        "error": f"Service '{name}' tidak dikenal.",
                    }
                ),
                404,
            )
        except Exception as e:
            return (
                jsonify(
                    {
                        "service": name,
                        "action": action,
                        "ok": False,
                        "error_code": "service_error",
                        "error": str(e),
                    }
                ),
                500,
            )

