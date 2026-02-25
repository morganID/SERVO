"""Flask app with service management API."""

import os
import json
import logging
from flask import Flask, request, jsonify

logger = logging.getLogger(__name__)


def create_app(api_key=None, workspace=None):
    app = Flask(__name__)

    app.config["API_KEY"] = api_key
    app.config["WORKSPACE"] = workspace or os.path.expanduser("~/moccha_workspace")

    # ── Initialize ServiceManager ──
    from moccha.service_manager import ServiceManager

    sm = ServiceManager(workspace=app.config["WORKSPACE"])
    app.config["SERVICE_MANAGER"] = sm

    # ── Auth Middleware ──
    @app.before_request
    def check_auth():
        # Skip auth for ping
        if request.endpoint == "ping":
            return None

        key = app.config.get("API_KEY")
        if not key:
            return None

        provided = (
            request.headers.get("X-API-Key")
            or request.args.get("api_key")
        )

        if provided != key:
            return jsonify({"error": "Unauthorized"}), 401

    # ── Health ──
    @app.route("/ping")
    def ping():
        return jsonify({"status": "ok"})

    @app.route("/")
    def index():
        info = {
            "name": "moccha",
            "status": "running",
            "workspace": app.config["WORKSPACE"],
            "services": sm.list_services(),
        }
        return jsonify(info)

    # ─────────────────────────────────────────
    # Service API
    # ─────────────────────────────────────────

    @app.route("/api/services", methods=["GET"])
    def api_list_services():
        return jsonify({"services": sm.list_services()})

    @app.route("/api/services/<name>/start", methods=["POST"])
    def api_start_service(name):
        result = sm.start_service(name)
        code = 200 if result.get("success") else 400
        return jsonify(result), code

    @app.route("/api/services/<name>/stop", methods=["POST"])
    def api_stop_service(name):
        result = sm.stop_service(name)
        code = 200 if result.get("success") else 400
        return jsonify(result), code

    @app.route("/api/services/<name>/restart", methods=["POST"])
    def api_restart_service(name):
        result = sm.restart_service(name)
        code = 200 if result.get("success") else 400
        return jsonify(result), code

    @app.route("/api/services/<name>/status", methods=["GET"])
    def api_service_status(name):
        result = sm.get_service_status(name)
        return jsonify(result)

    @app.route("/api/services/<name>/config", methods=["GET"])
    def api_service_config_get(name):
        config = sm.get_config(name)
        return jsonify(config)

    @app.route("/api/services/<name>/config", methods=["POST"])
    def api_service_config_update(name):
        data = request.get_json() or {}
        result = sm.update_config(name, data)
        code = 200 if result.get("success") else 400
        return jsonify(result), code

    @app.route("/api/services/status", methods=["GET"])
    def api_all_services_status():
        return jsonify(sm.get_all_status())

    # ─────────────────────────────────────────
    # Torrent API (delegates to Deluge service)
    # ─────────────────────────────────────────

    def _get_deluge():
        """Helper: get Deluge service or return error."""
        deluge = sm.get_service("deluge")
        if not deluge:
            return None, jsonify({
                "success": False,
                "error": "Deluge not available. Start it first: "
                         "moccha service start deluge"
            }), 400
        return deluge, None, None

    @app.route("/api/torrents", methods=["GET"])
    def api_list_torrents():
        deluge = sm.get_service("deluge")
        if not deluge:
            return jsonify({
                "success": False,
                "error": "Deluge not running. Start: moccha service start deluge"
            }), 400
        return jsonify(deluge.list_torrents())

    @app.route("/api/torrents/add", methods=["POST"])
    def api_add_torrent():
        deluge = sm.get_service("deluge")
        if not deluge:
            return jsonify({
                "success": False,
                "error": "Deluge not running"
            }), 400

        data = request.get_json() or {}
        result = deluge.add_torrent(
            magnet=data.get("magnet"),
            torrent_url=data.get("torrent_url"),
            torrent_file=data.get("torrent_file"),
        )
        code = 200 if result.get("success") else 400
        return jsonify(result), code

    @app.route("/api/torrents/stats", methods=["GET"])
    def api_torrent_stats():
        deluge = sm.get_service("deluge")
        if not deluge:
            return jsonify({"success": False, "error": "Deluge not running"}), 400
        return jsonify(deluge.get_stats())

    @app.route("/api/torrents/<torrent_id>", methods=["GET"])
    def api_torrent_detail(torrent_id):
        deluge = sm.get_service("deluge")
        if not deluge:
            return jsonify({"success": False, "error": "Deluge not running"}), 400
        return jsonify(deluge.get_torrent_details(torrent_id))

    @app.route("/api/torrents/<torrent_id>/pause", methods=["POST"])
    def api_pause_torrent(torrent_id):
        deluge = sm.get_service("deluge")
        if not deluge:
            return jsonify({"success": False, "error": "Deluge not running"}), 400
        return jsonify(deluge.pause_torrent(torrent_id))

    @app.route("/api/torrents/<torrent_id>/resume", methods=["POST"])
    def api_resume_torrent(torrent_id):
        deluge = sm.get_service("deluge")
        if not deluge:
            return jsonify({"success": False, "error": "Deluge not running"}), 400
        return jsonify(deluge.resume_torrent(torrent_id))

    @app.route("/api/torrents/<torrent_id>", methods=["DELETE"])
    def api_remove_torrent(torrent_id):
        deluge = sm.get_service("deluge")
        if not deluge:
            return jsonify({"success": False, "error": "Deluge not running"}), 400

        remove_data = request.args.get("remove_data", "false") == "true"
        return jsonify(deluge.remove_torrent(torrent_id, remove_data))

    @app.route("/api/torrents/pause-all", methods=["POST"])
    def api_pause_all():
        deluge = sm.get_service("deluge")
        if not deluge:
            return jsonify({"success": False, "error": "Deluge not running"}), 400
        return jsonify(deluge.pause_all())

    @app.route("/api/torrents/resume-all", methods=["POST"])
    def api_resume_all():
        deluge = sm.get_service("deluge")
        if not deluge:
            return jsonify({"success": False, "error": "Deluge not running"}), 400
        return jsonify(deluge.resume_all())

    return app