"""Registry dan helper untuk service eksternal (Deluge, JDownloader, Mega, dll)."""

from __future__ import annotations

from typing import Any, Dict

from . import deluge, jdownloader, mega

SERVICE_REGISTRY = {
    "deluge": deluge,
    "jdownloader": jdownloader,
    "mega": mega,
}


def list_services() -> list[dict[str, Any]]:
    """Kembalikan daftar service + status enabled."""
    services = []
    for name, mod in SERVICE_REGISTRY.items():
        is_enabled = getattr(mod, "is_enabled", None)
        enabled = bool(is_enabled() if callable(is_enabled) else True)
        services.append({"name": name, "enabled": enabled})
    return services


def dispatch_action(name: str, action: str, payload: Dict[str, Any], config) -> Dict[str, Any]:
    """Dispatch aksi ke modul service yang sesuai."""
    mod = SERVICE_REGISTRY.get(name)
    if not mod:
        raise KeyError(f"Unknown service: {name}")

    handler = getattr(mod, "handle_action", None)
    if not callable(handler):
        raise NotImplementedError(f"Service '{name}' belum punya handler.")

    return handler(action, payload, config)

"""Moccha - Download manager for Google Colab."""

from moccha.daemon import load_info, is_running


def get_url():
    info = load_info()
    return info.get("url") if info else None


def get_info():
    return load_info()


def status():
    if is_running():
        info = load_info()
        if info:
            print(f"🟢 RUNNING")
            print(f"   URL: {info.get('url')}")
            print(f"   Key: {info.get('api_key')}")
        else:
            print("🟡 Running but no info")
    else:
        print("🔴 NOT RUNNING")