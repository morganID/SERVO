"""Integrasi dasar MEGA.nz menggunakan library `mega.py`.

  pip install mega.py

Konfigurasi via environment:
  - MEGA_EMAIL
  - MEGA_PASSWORD

Aksi yang didukung:
  - ping
  - download_url  (params: {"url": "<public-link>", "dest": "/path/ke/folder"})
  - upload_file   (params: {"path": "/path/file", "dest": "<nama-folder-di-mega-optional>"})
"""

from __future__ import annotations

import os
from typing import Any, Dict

_have_lib = False
_Mega = None

try:  # pragma: no cover - optional dependency
    from mega import Mega

    _have_lib = True
    _Mega = Mega
except Exception:  # pragma: no cover
    _have_lib = False

_client = None


def _get_config() -> Dict[str, str]:
    return {
        "email": os.getenv("MEGA_EMAIL", ""),
        "password": os.getenv("MEGA_PASSWORD", ""),
    }


def is_enabled() -> bool:
    cfg = _get_config()
    return bool(_have_lib and cfg["email"] and cfg["password"])


def _ensure_client():
    global _client
    if not _have_lib:
        raise RuntimeError("Library 'mega.py' belum terinstall.")

    cfg = _get_config()
    if not cfg["email"] or not cfg["password"]:
        raise RuntimeError("MEGA_EMAIL / MEGA_PASSWORD belum dikonfigurasi.")

    if _client is None:
        mega = _Mega()
        _client = mega.login(cfg["email"], cfg["password"])
    return _client


def handle_action(action: str, payload: Dict[str, Any], config) -> Dict[str, Any]:  # noqa: ARG001
    """Handle aksi Mega."""
    if not _have_lib:
        return {
            "ok": False,
            "error_code": "library_missing",
            "error": "Library 'mega.py' belum terinstall. pip install mega.py",
        }

    cfg = _get_config()
    if not cfg["email"] or not cfg["password"]:
        return {
            "ok": False,
            "error_code": "not_configured",
            "error": "MEGA_EMAIL / MEGA_PASSWORD belum di-set.",
        }

    try:
        client = _ensure_client()

        if action == "ping":
            # Cek bisa akses root.
            root = client.get_files()
            return {"ok": True, "files_count": len(root)}

        if action == "download_url":
            url = payload.get("url")
            dest = payload.get("dest") or "."
            if not url:
                return {
                    "ok": False,
                    "error_code": "invalid_request",
                    "error": "Field 'url' wajib diisi.",
                }
            client.download_url(url, dest)
            return {"ok": True, "message": "Download dari link Mega dimulai.", "dest": dest}

        if action == "upload_file":
            path = payload.get("path")
            dest = payload.get("dest")
            if not path:
                return {
                    "ok": False,
                    "error_code": "invalid_request",
                    "error": "Field 'path' wajib diisi.",
                }
            res = client.upload(path, dest)
            return {"ok": True, "result": res}

        return {
            "ok": False,
            "error_code": "unknown_action",
            "error": f"Aksi '{action}' tidak dikenal untuk service 'mega'.",
        }
    except Exception as e:
        return {
            "ok": False,
            "error_code": "service_error",
            "error": str(e),
        }

