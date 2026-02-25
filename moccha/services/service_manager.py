"""Service Manager - pengelola semua layanan - FIXED."""

import os
import copy
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .deluge_service import DelugeService

logger = logging.getLogger(__name__)


def _deep_merge(base: dict, override: dict) -> dict:
    """
    ✅ FIX: Deep merge dua dict.
    override menimpa base, tapi nested dict di-merge bukan di-replace.
    """
    result = copy.deepcopy(base)
    for key, value in override.items():
        if (
            key in result
            and isinstance(result[key], dict)
            and isinstance(value, dict)
        ):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


class ServiceManager:
    """Manages all services (Deluge, JDownloader, MEGA)."""

    # ✅ FIX: Default config yang masuk akal untuk Colab
    DEFAULT_CONFIG = {
        "services": {
            "deluge": {
                "enabled": True,
                "host": "127.0.0.1",          # ✅ bukan "localhost"
                "port": 58846,
                "username": "localclient",     # ✅ tambah username
                "password": "deluge123",       # ✅ tambah password
                "download_path": "",           # ✅ di-set dari workspace
                "max_download_speed": -1,      # ✅ -1 = unlimited, bukan 0
                "max_upload_speed": -1,
                "auto_add_folder": "",         # ✅ kosong = disable
                "config_dir": "",              # ✅ di-set saat init
            },
            "jdownloader": {
                "enabled": False,              # ✅ disabled by default
                "host": "127.0.0.1",
                "port": 3129,
                "download_path": "",
            },
            "mega": {
                "enabled": False,              # ✅ disabled by default
                "email": "",
                "password": "",
                "download_path": "",
            },
        }
    }

    # Map service name → class
    SERVICE_CLASSES = {
        "deluge": DelugeService,
        # "jdownloader": JDownloaderService,  # tambah nanti
        # "mega": MegaService,                # tambah nanti
    }

    def __init__(
        self,
        config_path: Optional[str] = None,
        workspace: Optional[str] = None,
    ):
        """
        Initialize Service Manager.

        Args:
            config_path: Path to config file. None = default location.
            workspace:   Workspace directory (dari daemon). Dipakai untuk
                         set default download paths.
        """
        self.workspace = workspace or os.path.expanduser("~/moccha_workspace")
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()

        # ✅ FIX: Set default paths yang belum di-set berdasarkan workspace
        self._apply_workspace_defaults()

        # Initialize services
        self.services: Dict[str, Any] = {}
        self._init_services()

    def _get_default_config_path(self) -> str:
        """Get default config file path."""
        config_dir = os.path.join(self.workspace, ".config")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "services_config.json")

    def _apply_workspace_defaults(self):
        """
        ✅ FIX: Set download paths berdasarkan workspace
        jika belum di-set oleh user.
        """
        services = self.config.get("services", {})

        # Deluge
        deluge = services.get("deluge", {})
        if not deluge.get("download_path"):
            deluge["download_path"] = os.path.join(
                self.workspace, "downloads", "torrents"
            )
        if not deluge.get("config_dir"):
            deluge["config_dir"] = os.path.join(
                self.workspace, ".config", "deluge"
            )
        if not deluge.get("auto_add_folder"):
            deluge["auto_add_folder"] = os.path.join(
                self.workspace, "watch"
            )

        # JDownloader
        jd = services.get("jdownloader", {})
        if not jd.get("download_path"):
            jd["download_path"] = os.path.join(
                self.workspace, "downloads", "jdownloader"
            )

        # MEGA
        mega = services.get("mega", {})
        if not mega.get("download_path"):
            mega["download_path"] = os.path.join(
                self.workspace, "downloads", "mega"
            )

    # ─────────────────────────────────────────────
    # Config Management
    # ─────────────────────────────────────────────

    def _load_config(self) -> Dict[str, Any]:
        """✅ FIX: Load config dengan proper deep merge."""
        # Mulai dari default
        config = copy.deepcopy(self.DEFAULT_CONFIG)

        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded = json.load(f)

                # ✅ FIX: Deep merge, bukan shallow update
                config = _deep_merge(config, loaded)
                logger.info(f"Config loaded from {self.config_path}")

            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON in config file: {e}")
                # Backup corrupted file
                backup = self.config_path + ".bak"
                try:
                    os.rename(self.config_path, backup)
                    logger.info(f"Corrupted config backed up to {backup}")
                except:
                    pass

            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        else:
            logger.info("No config file found, using defaults")

        # Save merged config
        self._save_config(config)
        return config

    def _save_config(self, config: Optional[Dict] = None) -> bool:
        """Save configuration to file."""
        config = config or self.config
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
            return True
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            return False

    def get_config(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for a specific service or all services."""
        services = self.config.get("services", {})
        if service_name:
            return copy.deepcopy(services.get(service_name, {}))
        return copy.deepcopy(services)

    def update_config(
        self, service_name: str, new_config: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ✅ FIX: Update config dengan deep merge dan proper restart.
        """
        if "services" not in self.config:
            self.config["services"] = {}

        if service_name not in self.config["services"]:
            self.config["services"][service_name] = {}

        # Deep merge new config
        self.config["services"][service_name] = _deep_merge(
            self.config["services"][service_name],
            new_config
        )

        # Save
        if not self._save_config():
            return {"success": False, "error": "Failed to save config"}

        # ✅ FIX: Reinitialize service jika sudah ada
        if service_name in self.services:
            try:
                # Stop dulu
                old_service = self.services[service_name]
                try:
                    old_service.stop()
                except:
                    pass

                # Buat instance baru
                svc_class = self.SERVICE_CLASSES.get(service_name)
                if svc_class:
                    svc_config = self.config["services"][service_name]
                    self.services[service_name] = svc_class(svc_config)
                    logger.info(f"Service '{service_name}' reinitialized")

            except Exception as e:
                logger.error(f"Failed to reinitialize {service_name}: {e}")
                return {
                    "success": False,
                    "error": f"Config saved but reinit failed: {e}"
                }

        return {
            "success": True,
            "message": f"Configuration updated for {service_name}",
            "config": self.get_config(service_name)
        }

    # ─────────────────────────────────────────────
    # Service Initialization
    # ─────────────────────────────────────────────

    def _init_services(self) -> None:
        """✅ FIX: Initialize services dengan proper error handling."""
        services_config = self.config.get("services", {})

        for name, svc_class in self.SERVICE_CLASSES.items():
            svc_config = services_config.get(name, {})

            if not svc_config.get("enabled", False):
                logger.debug(f"Service '{name}' is disabled, skipping")
                continue

            try:
                self.services[name] = svc_class(svc_config)
                logger.info(f"✅ Service '{name}' initialized")
            except Exception as e:
                logger.error(f"❌ Failed to initialize '{name}': {e}")
                # Jangan crash seluruh manager karena satu service gagal

    # ─────────────────────────────────────────────
    # Service Access
    # ─────────────────────────────────────────────

    def get_service(self, service_name: str) -> Optional[Any]:
        """Get service instance by name."""
        return self.services.get(service_name)

    def list_services(self) -> List[Dict[str, Any]]:
        """
        ✅ FIX: Return info lengkap, bukan cuma nama.
        """
        result = []
        services_config = self.config.get("services", {})

        for name in self.SERVICE_CLASSES:
            svc_config = services_config.get(name, {})
            info = {
                "name": name,
                "enabled": svc_config.get("enabled", False),
                "initialized": name in self.services,
                "running": False,
            }

            # Cek running status
            if name in self.services:
                try:
                    status = self.services[name].get_status()
                    info["running"] = status.get("running", False) or \
                                      status.get("connected", False)
                except:
                    pass

            result.append(info)

        return result

    # ─────────────────────────────────────────────
    # Service Control
    # ─────────────────────────────────────────────

    def start_service(self, service_name: str) -> Dict[str, Any]:
        """Start a specific service."""
        service = self.get_service(service_name)
        if not service:
            # ✅ FIX: Cek apakah disabled vs not found
            svc_config = self.config.get("services", {}).get(service_name)
            if svc_config is None:
                return {
                    "success": False,
                    "error": f"Unknown service: {service_name}. "
                             f"Available: {list(self.SERVICE_CLASSES.keys())}"
                }
            elif not svc_config.get("enabled", False):
                return {
                    "success": False,
                    "error": f"Service '{service_name}' is disabled. "
                             f"Enable it first with update_config()"
                }
            else:
                return {
                    "success": False,
                    "error": f"Service '{service_name}' failed to initialize"
                }

        try:
            # ✅ FIX: Langsung return result dari service, tanpa wrapping
            result = service.start()
            return result

        except Exception as e:
            logger.error(f"Failed to start {service_name}: {e}")
            return {"success": False, "error": str(e)}

    def stop_service(self, service_name: str) -> Dict[str, Any]:
        """Stop a specific service."""
        service = self.get_service(service_name)
        if not service:
            return {
                "success": False,
                "error": f"Service '{service_name}' not found or not enabled"
            }

        try:
            return service.stop()
        except Exception as e:
            logger.error(f"Failed to stop {service_name}: {e}")
            return {"success": False, "error": str(e)}

    def restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart a specific service."""
        service = self.get_service(service_name)
        if not service:
            return {
                "success": False,
                "error": f"Service '{service_name}' not found or not enabled"
            }

        try:
            return service.restart()
        except Exception as e:
            logger.error(f"Failed to restart {service_name}: {e}")
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────
    # Bulk Operations
    # ─────────────────────────────────────────────

    def start_all(self) -> Dict[str, Any]:
        """Start all enabled services."""
        results = {}
        for name in self.services:
            results[name] = self.start_service(name)
        return results

    def stop_all(self) -> Dict[str, Any]:
        """Stop all running services."""
        results = {}
        for name in self.services:
            results[name] = self.stop_service(name)
        return results

    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get status of a specific service."""
        service = self.get_service(service_name)
        if not service:
            return {
                "success": False,
                "error": f"Service '{service_name}' not found or not enabled"
            }

        try:
            return service.get_status()
        except Exception as e:
            logger.error(f"Failed to get status for {service_name}: {e}")
            return {"success": False, "error": str(e)}

    def get_all_status(self) -> Dict[str, Any]:
        """
        ✅ FIX: Get status semua services, termasuk yang disabled.
        """
        status = {}
        services_config = self.config.get("services", {})

        for name in self.SERVICE_CLASSES:
            if name in self.services:
                try:
                    status[name] = self.services[name].get_status()
                except Exception as e:
                    status[name] = {"error": str(e)}
            else:
                enabled = services_config.get(name, {}).get("enabled", False)
                status[name] = {
                    "running": False,
                    "connected": False,
                    "enabled": enabled,
                    "message": "disabled" if not enabled else "init failed",
                }

        return status

    # ─────────────────────────────────────────────
    # Torrent-specific shortcuts
    # ─────────────────────────────────────────────

    def add_torrent(self, **kwargs) -> Dict[str, Any]:
        """Shortcut: add torrent via Deluge."""
        deluge = self.get_service("deluge")
        if not deluge:
            return {"success": False, "error": "Deluge service not available"}
        return deluge.add_torrent(**kwargs)

    def list_torrents(self) -> Dict[str, Any]:
        """Shortcut: list torrents via Deluge."""
        deluge = self.get_service("deluge")
        if not deluge:
            return {"success": False, "error": "Deluge service not available"}
        return deluge.list_torrents()