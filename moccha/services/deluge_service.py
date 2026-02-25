"""Deluge Service - manajemen Deluge daemon dan torrent."""

import os
import time
import json
import logging
import subprocess
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from deluge_client import DelugeRPCClient
except ImportError:
    raise ImportError("deluge-client not installed. Install with: pip install deluge-client")

logger = logging.getLogger(__name__)


class DelugeService:
    """Service for managing Deluge daemon and torrents."""
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize Deluge Service.
        
        Args:
            config: Configuration dictionary with host, port, download_path, etc.
        """
        self.config = config
        self.host = config.get("host", "localhost")
        self.port = config.get("port", 58846)
        self.download_path = config.get("download_path", "/downloads/torrents")
        self.max_download_speed = config.get("max_download_speed", 0)
        self.max_upload_speed = config.get("max_upload_speed", 0)
        self.auto_add_folder = config.get("auto_add_folder", "/torrents/watch")
        
        # Create download directory if it doesn't exist
        os.makedirs(self.download_path, exist_ok=True)
        os.makedirs(self.auto_add_folder, exist_ok=True)
        
        self.client = None
        self.daemon_process = None
        self.is_running = False
        
    def _connect(self) -> bool:
        """Connect to Deluge daemon."""
        try:
            if not self.client:
                self.client = DelugeRPCClient(self.host, self.port, "localclient", "")
                self.client.connect()
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Deluge: {e}")
            return False
    
    def _disconnect(self) -> None:
        """Disconnect from Deluge daemon."""
        try:
            if self.client:
                self.client.disconnect()
                self.client = None
        except Exception as e:
            logger.error(f"Error disconnecting from Deluge: {e}")
    
    def start(self) -> Dict[str, Any]:
        """Start Deluge daemon."""
        if self.is_running:
            return {"success": True, "message": "Deluge daemon already running"}
        
        try:
            # Check if deluged is available, if not try to install
            try:
                subprocess.run(["deluged", "--version"], capture_output=True, check=True)
            except (subprocess.CalledProcessError, FileNotFoundError):
                # Try to install Deluge
                print("Installing Deluge...")
                try:
                    # Try apt-get first (Linux)
                    subprocess.run(["apt-get", "update", "-qq"], check=True)
                    subprocess.run(["apt-get", "install", "-y", "-qq", 
                                  "deluge", "deluged", "deluge-web", "deluge-console", "python3-libtorrent"], 
                                 check=True)
                except:
                    # Try pip install as fallback
                    subprocess.run([sys.executable, "-m", "pip", "install", "deluge"], check=True)
            
            # Start deluged daemon
            self.daemon_process = subprocess.Popen(
                ["deluged", "-d", "-P", str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait a bit for daemon to start
            time.sleep(3)
            
            # Try to connect
            if self._connect():
                self.is_running = True
                
                # Configure settings
                self._configure_settings()
                
                return {
                    "success": True,
                    "message": "Deluge daemon started successfully",
                    "pid": self.daemon_process.pid,
                    "host": self.host,
                    "port": self.port
                }
            else:
                # If connection failed, kill the process
                self.daemon_process.terminate()
                self.daemon_process = None
                return {"success": False, "error": "Failed to connect to Deluge daemon"}
                
        except Exception as e:
            logger.error(f"Failed to start Deluge daemon: {e}")
            return {"success": False, "error": str(e)}
    
    def stop(self) -> Dict[str, Any]:
        """Stop Deluge daemon."""
        if not self.is_running:
            return {"success": True, "message": "Deluge daemon not running"}
        
        try:
            # Disconnect client
            self._disconnect()
            
            # Stop daemon process
            if self.daemon_process:
                self.daemon_process.terminate()
                self.daemon_process.wait(timeout=10)
                self.daemon_process = None
            
            self.is_running = False
            return {"success": True, "message": "Deluge daemon stopped"}
            
        except Exception as e:
            logger.error(f"Failed to stop Deluge daemon: {e}")
            return {"success": False, "error": str(e)}
    
    def restart(self) -> Dict[str, Any]:
        """Restart Deluge daemon."""
        stop_result = self.stop()
        if not stop_result.get("success"):
            return stop_result
        
        # Wait a bit before restarting
        time.sleep(2)
        
        return self.start()
    
    def _configure_settings(self) -> None:
        """Configure Deluge settings."""
        try:
            if not self._connect():
                return
            
            # Set download/upload speed limits
            if self.max_download_speed > 0:
                self.client.core.set_config({"max_download_speed": self.max_download_speed})
            
            if self.max_upload_speed > 0:
                self.client.core.set_config({"max_upload_speed": self.max_upload_speed})
            
            # Set download location
            self.client.core.set_config({"download_location": self.download_path})
            
            # Enable auto-add folder
            self.client.core.set_config({
                "autoadd_enable": True,
                "autoadd_location": self.auto_add_folder
            })
            
        except Exception as e:
            logger.error(f"Failed to configure Deluge settings: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get Deluge daemon status."""
        status = {
            "running": self.is_running,
            "host": self.host,
            "port": self.port,
            "download_path": self.download_path,
            "auto_add_folder": self.auto_add_folder
        }
        
        if self.is_running and self._connect():
            try:
                # Get daemon info
                daemon_info = self.client.daemon.info()
                status.update({
                    "daemon_info": daemon_info,
                    "connected": True
                })
                
                # Get stats
                stats = self.client.core.get_session_status([
                    "upload_rate", "download_rate", "dht_nodes"
                ])
                status["stats"] = {
                    "upload_rate": stats["upload_rate"],
                    "download_rate": stats["download_rate"],
                    "dht_nodes": stats["dht_nodes"]
                }
                
            except Exception as e:
                logger.error(f"Failed to get Deluge status: {e}")
                status["connected"] = False
                status["error"] = str(e)
        else:
            status["connected"] = False
        
        return status
    
    def add_torrent(self, torrent_url: Optional[str] = None, torrent_file: Optional[str] = None) -> Dict[str, Any]:
        """Add torrent to Deluge."""
        if not self.is_running:
            return {"success": False, "error": "Deluge daemon not running"}
        
        if not self._connect():
            return {"success": False, "error": "Failed to connect to Deluge"}
        
        try:
            if torrent_url:
                # Add torrent from URL
                torrent_id = self.client.core.add_torrent_uri(torrent_url, {})
            elif torrent_file and os.path.exists(torrent_file):
                # Add torrent from file
                with open(torrent_file, 'rb') as f:
                    torrent_data = f.read()
                torrent_id = self.client.core.add_torrent_file(os.path.basename(torrent_file), torrent_data, {})
            else:
                return {"success": False, "error": "No torrent URL or file provided"}
            
            return {
                "success": True,
                "message": "Torrent added successfully",
                "torrent_id": str(torrent_id)
            }
            
        except Exception as e:
            logger.error(f"Failed to add torrent: {e}")
            return {"success": False, "error": str(e)}
    
    def list_torrents(self) -> Dict[str, Any]:
        """List all torrents."""
        if not self.is_running:
            return {"success": False, "error": "Deluge daemon not running"}
        
        if not self._connect():
            return {"success": False, "error": "Failed to connect to Deluge"}
        
        try:
            # Get all torrents
            torrents = self.client.core.get_torrents_status({}, [
                "name", "progress", "state", "download_payload_rate", 
                "upload_payload_rate", "num_seeds", "num_peers",
                "total_wanted", "total_done", "eta", "ratio"
            ])
            
            # Format results
            result = []
            for torrent_id, torrent_info in torrents.items():
                result.append({
                    "id": str(torrent_id),
                    "name": torrent_info["name"],
                    "progress": torrent_info["progress"],
                    "state": torrent_info["state"],
                    "download_rate": torrent_info["download_payload_rate"],
                    "upload_rate": torrent_info["upload_payload_rate"],
                    "seeds": torrent_info["num_seeds"],
                    "peers": torrent_info["num_peers"],
                    "total_wanted": torrent_info["total_wanted"],
                    "total_done": torrent_info["total_done"],
                    "eta": torrent_info["eta"],
                    "ratio": torrent_info["ratio"]
                })
            
            return {
                "success": True,
                "torrents": result,
                "count": len(result)
            }
            
        except Exception as e:
            logger.error(f"Failed to list torrents: {e}")
            return {"success": False, "error": str(e)}
    
    def get_torrent_details(self, torrent_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific torrent."""
        if not self.is_running:
            return {"success": False, "error": "Deluge daemon not running"}
        
        if not self._connect():
            return {"success": False, "error": "Failed to connect to Deluge"}
        
        try:
            # Get torrent status
            torrent_info = self.client.core.get_torrent_status(torrent_id, [
                "name", "progress", "state", "download_payload_rate", 
                "upload_payload_rate", "num_seeds", "num_peers",
                "total_wanted", "total_done", "eta", "ratio",
                "files", "trackers", "peers"
            ])
            
            if not torrent_info:
                return {"success": False, "error": "Torrent not found"}
            
            # Format files
            files = []
            if "files" in torrent_info:
                for i, file_info in enumerate(torrent_info["files"]):
                    files.append({
                        "index": i,
                        "path": file_info["path"],
                        "size": file_info["size"],
                        "offset": file_info["offset"]
                    })
            
            # Format trackers
            trackers = []
            if "trackers" in torrent_info:
                for tracker in torrent_info["trackers"]:
                    trackers.append({
                        "url": tracker["url"],
                        "tier": tracker["tier"]
                    })
            
            # Format peers
            peers = []
            if "peers" in torrent_info:
                for peer_id, peer_info in torrent_info["peers"].items():
                    peers.append({
                        "peer_id": peer_id,
                        "ip": peer_info["ip"],
                        "progress": peer_info["progress"],
                        "down_speed": peer_info["down_speed"],
                        "up_speed": peer_info["up_speed"]
                    })
            
            result = {
                "id": torrent_id,
                "name": torrent_info["name"],
                "progress": torrent_info["progress"],
                "state": torrent_info["state"],
                "download_rate": torrent_info["download_payload_rate"],
                "upload_rate": torrent_info["upload_payload_rate"],
                "seeds": torrent_info["num_seeds"],
                "peers": torrent_info["num_peers"],
                "total_wanted": torrent_info["total_wanted"],
                "total_done": torrent_info["total_done"],
                "eta": torrent_info["eta"],
                "ratio": torrent_info["ratio"],
                "files": files,
                "trackers": trackers,
                "peers": peers
            }
            
            return {"success": True, "torrent": result}
            
        except Exception as e:
            logger.error(f"Failed to get torrent details: {e}")
            return {"success": False, "error": str(e)}
    
    def pause_torrent(self, torrent_id: str) -> Dict[str, Any]:
        """Pause a specific torrent."""
        if not self.is_running:
            return {"success": False, "error": "Deluge daemon not running"}
        
        if not self._connect():
            return {"success": False, "error": "Failed to connect to Deluge"}
        
        try:
            self.client.core.pause_torrent([torrent_id])
            return {"success": True, "message": f"Torrent {torrent_id} paused"}
        except Exception as e:
            logger.error(f"Failed to pause torrent: {e}")
            return {"success": False, "error": str(e)}
    
    def resume_torrent(self, torrent_id: str) -> Dict[str, Any]:
        """Resume a specific torrent."""
        if not self.is_running:
            return {"success": False, "error": "Deluge daemon not running"}
        
        if not self._connect():
            return {"success": False, "error": "Failed to connect to Deluge"}
        
        try:
            self.client.core.resume_torrent([torrent_id])
            return {"success": True, "message": f"Torrent {torrent_id} resumed"}
        except Exception as e:
            logger.error(f"Failed to resume torrent: {e}")
            return {"success": False, "error": str(e)}
    
    def remove_torrent(self, torrent_id: str, remove_data: bool = False) -> Dict[str, Any]:
        """Remove a specific torrent."""
        if not self.is_running:
            return {"success": False, "error": "Deluge daemon not running"}
        
        if not self._connect():
            return {"success": False, "error": "Failed to connect to Deluge"}
        
        try:
            self.client.core.remove_torrent(torrent_id, remove_data)
            return {"success": True, "message": f"Torrent {torrent_id} removed"}
        except Exception as e:
            logger.error(f"Failed to remove torrent: {e}")
            return {"success": False, "error": str(e)}
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Deluge statistics."""
        if not self.is_running:
            return {"success": False, "error": "Deluge daemon not running"}
        
        if not self._connect():
            return {"success": False, "error": "Failed to connect to Deluge"}
        
        try:
            stats = self.client.core.get_session_status([
                "upload_rate", "download_rate", "dht_nodes",
                "num_peers", "num_connections", "payload_upload_rate",
                "payload_download_rate"
            ])
            
            return {
                "success": True,
                "stats": {
                    "upload_rate": stats["upload_rate"],
                    "download_rate": stats["download_rate"],
                    "dht_nodes": stats["dht_nodes"],
                    "num_peers": stats["num_peers"],
                    "num_connections": stats["num_connections"],
                    "payload_upload_rate": stats["payload_upload_rate"],
                    "payload_download_rate": stats["payload_download_rate"]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to get Deluge stats: {e}")
            return {"success": False, "error": str(e)}
    
    def get_peers(self, torrent_id: str) -> Dict[str, Any]:
        """Get peer information for a specific torrent."""
        if not self.is_running:
            return {"success": False, "error": "Deluge daemon not running"}
        
        if not self._connect():
            return {"success": False, "error": "Failed to connect to Deluge"}
        
        try:
            peers = self.client.core.get_torrent_status(torrent_id, ["peers"])
            
            peer_list = []
            if "peers" in peers:
                for peer_id, peer_info in peers["peers"].items():
                    peer_list.append({
                        "peer_id": peer_id,
                        "ip": peer_info["ip"],
                        "progress": peer_info["progress"],
                        "down_speed": peer_info["down_speed"],
                        "up_speed": peer_info["up_speed"],
                        "client": peer_info["client"]
                    })
            
            return {
                "success": True,
                "peers": peer_list,
                "count": len(peer_list)
            }
            
        except Exception as e:
            logger.error(f"Failed to get peers: {e}")
            return {"success": False, "error": str(e)}