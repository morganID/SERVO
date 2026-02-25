"""Modul autentikasi."""

from functools import wraps
from flask import request, jsonify


def require_key(api_key: str):
    """Decorator untuk memeriksa API key."""

    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            key = request.headers.get('X-API-Key', '')
            if key != api_key:
                return jsonify({"error": "Invalid API key"}), 401
            return f(*args, **kwargs)
        return decorated
    return decorator