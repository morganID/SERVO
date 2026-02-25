"""Flask API Server - semua endpoint."""

import os
from datetime import datetime

from flask import Flask
from flask_cors import CORS

from moccha.config import Config
from moccha.routes import register_all_routes


def create_app(api_key, workspace="/content"):
    """Factory: bikin Flask app."""

    app = Flask(__name__)
    CORS(app)

    config = Config(api_key, workspace)

    # Delegasikan pendaftaran route ke modul terpisah
    register_all_routes(app, config)

    return app


def main():
    """Run server langsung, cocok untuk Colab."""
    api_key = os.getenv("MOCCHA_API_KEY")
    if not api_key:
        # Default sederhana; untuk production sebaiknya set env sendiri
        import uuid

        api_key = str(uuid.uuid4())

    workspace = os.getenv("MOCCHA_WORKSPACE", "/content")
    port = int(os.getenv("MOCCHA_PORT", "5000"))

    app = create_app(api_key=api_key, workspace=workspace)
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()