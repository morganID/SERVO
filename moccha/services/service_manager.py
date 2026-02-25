"""Service Manager - pengelola semua layanan (Deluge, JDownloader, MEGA)."""

import os
import json
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path

from .deluge_service import DelugeService
from .jdownloader_service import JDownloaderService
from .mega_service import MegaService

logger = logging.getLogger(__name__)


class ServiceManager:
    """Manages all services (Deluge, JDownloader, MEGA)."""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize Service Manager.
        
        Args:
            config_path: Path to config file. If None, uses default location.
        """
        self.config_path = config_path or self._get_default_config_path()
        self.config = self._load_config()
        
        # Initialize services
        self.services: Dict[str, Any] = {}
        self._init_services()
        
    def _get_default_config_path(self) -> str:
        """Get default config file path."""
        home = os.path.expanduser("~")
        config_dir = os.path.join(home, ".moccha")
        os.makedirs(config_dir, exist_ok=True)
        return os.path.join(config_dir, "services_config.json")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file."""
        default_config = {
            "services": {
                "deluge": {
                    "enabled": True,
                    "host": "localhost",
                    "port": 58846,
                    "download_path": "/downloads/torrents",
                    "max_download_speed": 0,
                    "max_upload_speed": 0,
                    "auto_add_folder": "/torrents/watch"
                },
                "jdownloader": {
                    "enabled": True,
                    "host": "localhost", 
                    "port": 3129,
                    "download_path": "/downloads/jdownloader"
                },
                "mega": {
                    "enabled": True,
                    "email": "",
                    "password": "",
                    "download_path": "/downloads/mega"
                }
            }
        }
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    default_config.update(loaded_config)
                    return default_config
            except Exception as e:
                logger.error(f"Failed to load config: {e}")
        
        # Save default config
        self._save_config(default_config)
        return default_config
    
    def _save_config(self, config: Dict[str, Any]) -> None:
        """Save configuration to file."""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
    
    def _init_services(self) -> None:
        """Initialize all services based on config."""
        services_config = self.config.get("services", {})
        
        # Initialize Deluge service
        if services_config.get("deluge", {}).get("enabled", False):
            try:
                self.services["deluge"] = DelugeService(services_config["deluge"])
                logger.info("Deluge service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Deluge service: {e}")
        
        # Initialize JDownloader service
        if services_config.get("jdownloader", {}).get("enabled", False):
            try:
                self.services["jdownloader"] = JDownloaderService(services_config["jdownloader"])
                logger.info("JDownloader service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize JDownloader service: {e}")
        
        # Initialize MEGA service
        if services_config.get("mega", {}).get("enabled", False):
            try:
                self.services["mega"] = MegaService(services_config["mega"])
                logger.info("MEGA service initialized")
            except Exception as e:
                logger.error(f"Failed to initialize MEGA service: {e}")
    
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get service instance by name."""
        return self.services.get(service_name)
    
    def get_all_services(self) -> Dict[str, Any]:
        """Get all initialized services."""
        return self.services
    
    def get_service_status(self, service_name: str) -> Dict[str, Any]:
        """Get status of a specific service."""
        service = self.get_service(service_name)
        if not service:
            return {"error": f"Service {service_name} not found or not enabled"}
        
        try:
            return service.get_status()
        except Exception as e:
            logger.error(f"Failed to get status for {service_name}: {e}")
            return {"error": str(e)}
    
    def get_all_services_status(self) -> Dict[str, Any]:
        """Get status of all services."""
        status = {}
        for name, service in self.services.items():
            try:
                status[name] = service.get_status()
            except Exception as e:
                logger.error(f"Failed to get status for {name}: {e}")
                status[name] = {"error": str(e)}
        return status
    
    def start_service(self, service_name: str) -> Dict[str, Any]:
        """Start a specific service."""
        service = self.get_service(service_name)
        if not service:
            return {"error": f"Service {service_name} not found or not enabled"}
        
        try:
            result = service.start()
            return {"success": True, "message": f"{service_name} started", "result": result}
        except Exception as e:
            logger.error(f"Failed to start {service_name}: {e}")
            return {"error": str(e)}
    
    def stop_service(self, service_name: str) -> Dict[str, Any]:
        """Stop a specific service."""
        service = self.get_service(service_name)
        if not service:
            return {"error": f"Service {service_name} not found or not enabled"}
        
        try:
            result = service.stop()
            return {"success": True, "message": f"{service_name} stopped", "result": result}
        except Exception as e:
            logger.error(f"Failed to stop {service_name}: {e}")
            return {"error": str(e)}
    
    def restart_service(self, service_name: str) -> Dict[str, Any]:
        """Restart a specific service."""
        service = self.get_service(service_name)
        if not service:
            return {"error": f"Service {service_name} not found or not enabled"}
        
        try:
            result = service.restart()
            return {"success": True, "message": f"{service_name} restarted", "result": result}
        except Exception as e:
            logger.error(f"Failed to restart {service_name}: {e}")
            return {"error": str(e)}
    
    def update_config(self, service_name: str, config: Dict[str, Any]) -> Dict[str, Any]:
        """Update configuration for a specific service."""
        if "services" not in self.config:
            self.config["services"] = {}
        
        if service_name not in self.config["services"]:
            self.config["services"][service_name] = {}
        
        # Update config
        self.config["services"][service_name].update(config)
        
        # Save to file
        self._save_config(self.config)
        
        # Reinitialize service if it exists
        if service_name in self.services:
            try:
                # Stop current service
                self.services[service_name].stop()
                
                # Reinitialize with new config
                if service_name == "deluge":
                    self.services[service_name] = DelugeService(self.config["services"]["deluge"])
                elif service_name == "jdownloader":
                    self.services[service_name] = JDownloaderService(self.config["services"]["jdownloader"])
                elif service_name == "mega":
                    self.services[service_name] = MegaService(self.config["services"]["mega"])
                
                return {"success": True, "message": f"Configuration updated for {service_name}"}
            except Exception as e:
                logger.error(f"Failed to update config for {service_name}: {e}")
                return {"error": str(e)}
        
        return {"success": True, "message": f"Configuration updated for {service_name}"}
    
    def get_config(self, service_name: Optional[str] = None) -> Dict[str, Any]:
        """Get configuration for a specific service or all services."""
        if service_name:
            return self.config.get("services", {}).get(service_name, {})
        return self.config.get("services", {})
    
    def list_services(self) -> List[str]:
        """List all available services."""
        return list(self.services.keys())