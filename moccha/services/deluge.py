"""Integrasi dasar Deluge Web API.

Konfigurasi via environment:
  - DELUGE_URL       (contoh: http://127.0.0.1:8112)
  - DELUGE_PASSWORD  (password Web UI)

Aksi yang didukung:
  - ping
  - list
  - add_magnet   (params: {"magnet": "<magnet-uri>"})
"""

from __future__ import annotations

import os
import threading
from typing import Any, Dict

import requests

_session_lock = threading.Lock()
_session: requests.Session | None = None


def _get_config() -> Dict[str, str]:
    url = os.getenv("DELUGE_URL")
    password = os.getenv("DELUGE_PASSWORD")
    return {"url": url or "", "password": password or ""}


def is_enabled() -> bool:
    cfg = _get_config()
    return bool(cfg["url"] and cfg["password"])


def _ensure_session() -> requests.Session:
    global _session
    cfg = _get_config()
    if not cfg["url"] or not cfg["password"]:
        raise RuntimeError("DELUGE_URL / DELUGE_PASSWORD belum dikonfigurasi.")

    with _session_lock:
        if _session is not None:
            return _session

        sess = requests.Session()
        # Login ke Deluge Web
        resp = sess.post(
            cfg["url"].rstrip("/") + "/json",
            json={"id": 0, "method": "auth.login", "params": [cfg["password"]]},
            timeout=10,
        )
        data = resp.json()
        if not data.get("result"):
            raise RuntimeError("Gagal login ke Deluge (auth.login).")

        _session = sess
        return _session


def _call(method: str, params: list[Any] | None = None) -> Any:
    sess = _ensure_session()
    cfg = _get_config()
    payload = {"id": 0, "method": method, "params": params or []}
    resp = sess.post(cfg["url"].rstrip("/") + "/json", json=payload, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    if "error" in data and data["error"]:
        raise RuntimeError(str(data["error"]))
    return data.get("result")


def handle_action(action: str, payload: Dict[str, Any], config) -> Dict[str, Any]:  # noqa: ARG001
    """Handle aksi Deluge.

    action:
      - "ping"
      - "list"
      - "add_magnet"
    """
    if not is_enabled():
        return {
            "ok": False,
            "error_code": "not_configured",
            "error": "DELUGE_URL / DELUGE_PASSWORD belum di-set.",
        }

    try:
        if action == "ping":
            # Cek koneksi dan session
            connected = _call("web.connected")
            return {"ok": True, "connected": bool(connected)}

        if action == "list":
            # Ambil daftar torrent basic
            fields = [
                "name",
                "state",
                "progress",
                "download_payload_rate",
                "upload_payload_rate",
                "eta",
            ]
            result = _call("web.update_ui", [fields, {}])
            return {"ok": True, "torrents": result.get("torrents", {})}

        if action == "add_magnet":
            magnet = payload.get("magnet") or payload.get("uri")
            if not magnet:
                return {
                    "ok": False,
                    "error_code": "invalid_request",
                    "error": "Field 'magnet' wajib diisi.",
                }
            # Tambah torrent magnet
            _call("core.add_torrent_magnet", [magnet, {}])
            return {"ok": True, "message": "Magnet dikirim ke Deluge."}

        return {
            "ok": False,
            "error_code": "unknown_action",
            "error": f"Aksi '{action}' tidak dikenal untuk service 'deluge'.",
        }
    except Exception as e:
        return {
            "ok": False,
            "error_code": "service_error",
            "error": str(e),
        }

