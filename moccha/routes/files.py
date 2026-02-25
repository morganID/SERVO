"""Route untuk manajemen file."""

import os

from flask import request, jsonify, send_file

from moccha.core.auth import require_key
from moccha.core.files import list_files, upload_file


def register_routes(app, config) -> None:
    @app.route("/files")
    @require_key(config.api_key)
    def files():
        path = request.args.get("path", str(config.workspace))
        result = list_files(path)
        return jsonify(result)

    @app.route("/upload", methods=["POST"])
    @require_key(config.api_key)
    def upload():
        if "file" not in request.files:
            return jsonify({"error": "No file"}), 400
        f = request.files["file"]
        dest = request.form.get("path", str(config.workspace))
        result = upload_file(f, dest)
        return jsonify(result)

    @app.route("/download/<path:filepath>")
    @require_key(config.api_key)
    def download(filepath):
        full = os.path.join(str(config.workspace), filepath)
        if not os.path.isfile(full):
            full = filepath
        if os.path.isfile(full):
            return send_file(full, as_attachment=True)
        return jsonify({"error": "Not found"}), 404

