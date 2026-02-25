"""Integrasi dasar JDownloader via MyJDownloader API.

Menggunakan library pihak ketiga: `myjdapi`
  pip install myjdapi

Konfigurasi via environment:
  - MYJD_EMAIL
  - MYJD_PASSWORD
  - MYJD_DEVICE (opsional, nama device; default device pertama)

Aksi yang didukung:
  - ping
  - add_links   (params: {"links": ["http://...", "magnet:..."]})
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

_have_lib = False
_Myjd = None

try:  # pragma: no cover - optional dependency
    from myjdapi import Myjd

    _have_lib = True
    _Myjd = Myjd
except Exception:  # pragma: no cover - jika belum terinstall
    _have_lib = False

_client = None
_device = None


def _get_config() -> Dict[str, str]:
    return {
        "email": os.getenv("MYJD_EMAIL", ""),
        "password": os.getenv("MYJD_PASSWORD", ""),
        "device": os.getenv("MYJD_DEVICE", ""),
    }


def is_enabled() -> bool:
    cfg = _get_config()
    return bool(_have_lib and cfg["email"] and cfg["password"])


def _ensure_device():
    global _client, _device
    if not _have_lib:
        raise RuntimeError("Library 'myjdapi' belum terinstall.")

    cfg = _get_config()
    if not cfg["email"] or not cfg["password"]:
        raise RuntimeError("MYJD_EMAIL / MYJD_PASSWORD belum dikonfigurasi.")

    if _client is None:
        _client = _Myjd()
        _client.connect(cfg["email"], cfg["password"])

    if _device is not None:
        return _device

    devices = _client.list_devices()
    if not devices:
        raise RuntimeError("Tidak ada device JDownloader yang online.")

    if cfg["device"]:
        for d in devices:
            if d.get("name") == cfg["device"]:
                _device = _client.get_device(d["name"])
                break
        if _device is None:
            raise RuntimeError(f"Device '{cfg['device']}' tidak ditemukan.")
    else:
        _device = _client.get_device(devices[0]["name"])

    return _device


def handle_action(action: str, payload: Dict[str, Any], config) -> Dict[str, Any]:  # noqa: ARG001
    """Handle aksi JDownloader."""
    if not _have_lib:
        return {
            "ok": False,
            "error_code": "library_missing",
            "error": "Library 'myjdapi' belum terinstall. pip install myjdapi",
        }

    cfg = _get_config()
    if not cfg["email"] or not cfg["password"]:
        return {
            "ok": False,
            "error_code": "not_configured",
            "error": "MYJD_EMAIL / MYJD_PASSWORD belum di-set.",
        }

    try:
        device = _ensure_device()

        if action == "ping":
            return {
                "ok": True,
                "device": device.get_device_name(),
            }

        if action == "add_links":
            links: List[str] = payload.get("links") or []
            if not links:
                return {
                    "ok": False,
                    "error_code": "invalid_request",
                    "error": "Field 'links' (list) wajib diisi.",
                }

            # Format payload sesuai API myjdapi
            # Lihat dokumentasi myjdapi untuk opsi lebih lanjut.
            pkg = {
                "autostart": True,
                "links": "\n".join(links),
                "extractPassword": None,
                "priority": "DEFAULT",
                "downloadPassword": None,
                "enabled": True,
            }
            device.linkgrabber.add_links([pkg])
            return {"ok": True, "message": f"{len(links)} link dikirim ke JDownloader."}

        return {
            "ok": False,
            "error_code": "unknown_action",
            "error": f"Aksi '{action}' tidak dikenal untuk service 'jdownloader'.",
        }
    except Exception as e:
        return {
            "ok": False,
            "error_code": "service_error",
            "error": str(e),
        }

