"""Service configuration models."""

from typing import Dict, Any, Optional


class ServiceConfig:
    """Base service configuration model."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        self.config[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.config.copy()


class DelugeConfig(ServiceConfig):
    """Deluge service configuration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
    
    @property
    def enabled(self) -> bool:
        return self.get("enabled", False)
    
    @property
    def host(self) -> str:
        return self.get("host", "localhost")
    
    @property
    def port(self) -> int:
        return self.get("port", 58846)
    
    @property
    def download_path(self) -> str:
        return self.get("download_path", "/downloads/torrents")
    
    @property
    def max_download_speed(self) -> int:
        return self.get("max_download_speed", 0)
    
    @property
    def max_upload_speed(self) -> int:
        return self.get("max_upload_speed", 0)
    
    @property
    def auto_add_folder(self) -> str:
        return self.get("auto_add_folder", "/torrents/watch")


class JDownloaderConfig(ServiceConfig):
    """JDownloader service configuration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
    
    @property
    def enabled(self) -> bool:
        return self.get("enabled", False)
    
    @property
    def host(self) -> str:
        return self.get("host", "localhost")
    
    @property
    def port(self) -> int:
        return self.get("port", 3129)
    
    @property
    def download_path(self) -> str:
        return self.get("download_path", "/downloads/jdownloader")


class MegaConfig(ServiceConfig):
    """MEGA service configuration."""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
    
    @property
    def enabled(self) -> bool:
        return self.get("enabled", False)
    
    @property
    def email(self) -> str:
        return self.get("email", "")
    
    @property
    def password(self) -> str:
        return self.get("password", "")
    
    @property
    def download_path(self) -> str:
        return self.get("download_path", "/downloads/mega")


class ServicesConfig:
    """Main services configuration."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self._deluge_config = None
        self._jdownloader_config = None
        self._mega_config = None
    
    @property
    def services(self) -> Dict[str, Any]:
        return self.config.get("services", {})
    
    @property
    def deluge(self) -> DelugeConfig:
        if self._deluge_config is None:
            self._deluge_config = DelugeConfig(self.services.get("deluge", {}))
        return self._deluge_config
    
    @property
    def jdownloader(self) -> JDownloaderConfig:
        if self._jdownloader_config is None:
            self._jdownloader_config = JDownloaderConfig(self.services.get("jdownloader", {}))
        return self._jdownloader_config
    
    @property
    def mega(self) -> MegaConfig:
        if self._mega_config is None:
            self._mega_config = MegaConfig(self.services.get("mega", {}))
        return self._mega_config
    
    def get_service_config(self, service_name: str) -> Optional[ServiceConfig]:
        """Get configuration for a specific service."""
        if service_name == "deluge":
            return self.deluge
        elif service_name == "jdownloader":
            return self.jdownloader
        elif service_name == "mega":
            return self.mega
        return None
    
    def update_service_config(self, service_name: str, config: Dict[str, Any]) -> None:
        """Update configuration for a specific service."""
        if "services" not in self.config:
            self.config["services"] = {}
        
        if service_name not in self.config["services"]:
            self.config["services"][service_name] = {}
        
        self.config["services"][service_name].update(config)
        
        # Reset cached config
        if service_name == "deluge":
            self._deluge_config = None
        elif service_name == "jdownloader":
            self._jdownloader_config = None
        elif service_name == "mega":
            self._mega_config = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return self.config.copy()