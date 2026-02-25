"""Deluge Service - manajemen Deluge daemon dan torrent - FIXED."""

import os
import sys
import time
import json
import base64
import logging
import subprocess
import threading
from typing import Dict, Any, List, Optional
from pathlib import Path

try:
    from deluge_client import DelugeRPCClient
except ImportError:
    raise ImportError("deluge-client not installed. Run: pip install deluge-client")

logger = logging.getLogger(__name__)


class DelugeService:
    """Service for managing Deluge daemon and torrents."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.host = config.get("host", "127.0.0.1")
        self.daemon_port = config.get("port", 58846)
        self.download_path = config.get("download_path", "/content/downloads")
        self.max_download_speed = config.get("max_download_speed", -1)
        self.max_upload_speed = config.get("max_upload_speed", -1)
        self.auto_add_folder = config.get("auto_add_folder", "")

        # ✅ FIX: Config directory untuk deluged
        self.config_dir = config.get("config_dir",
                                     os.path.expanduser("~/.config/deluge"))

        # ✅ FIX: Auth credentials (harus match auth file)
        self.username = config.get("username", "localclient")
        self.password = config.get("password", "deluge123")

        # Create directories
        os.makedirs(self.download_path, exist_ok=True)
        os.makedirs(self.config_dir, exist_ok=True)
        if self.auto_add_folder:
            os.makedirs(self.auto_add_folder, exist_ok=True)

        self._client = None
        self.daemon_process = None
        self._is_running = False

    # ─────────────────────────────────────────────
    # Auth & Config Setup
    # ─────────────────────────────────────────────

    def _setup_auth(self):
        """
        ✅ FIX: Buat auth file yang WAJIB ada sebelum deluged jalan.
        Format: username:password:level
        Level 10 = Admin
        """
        auth_file = os.path.join(self.config_dir, "auth")

        # Cek apakah user sudah ada di auth file
        existing = ""
        if os.path.exists(auth_file):
            with open(auth_file, "r") as f:
                existing = f.read()

        if self.username not in existing:
            with open(auth_file, "a") as f:
                f.write(f"{self.username}:{self.password}:10\n")
            logger.info(f"Auth entry added for '{self.username}'")

        # Set permissions
        os.chmod(auth_file, 0o600)

    def _setup_config(self):
        """Setup core.conf jika belum ada."""
        core_conf = os.path.join(self.config_dir, "core.conf")

        if not os.path.exists(core_conf):
            config_data = {
                "file": 1,
                "format": 1,
                "data": {
                    "download_location": self.download_path,
                    "move_completed_path": self.download_path,
                    "daemon_port": self.daemon_port,
                    "allow_remote": True,
                    "max_download_speed": self.max_download_speed,
                    "max_upload_speed": self.max_upload_speed,
                }
            }

            with open(core_conf, "w") as f:
                json.dump(config_data, f, indent=2)

            logger.info(f"Core config created at {core_conf}")

    # ─────────────────────────────────────────────
    # Connection Management
    # ─────────────────────────────────────────────

    def _connect(self) -> bool:
        """✅ FIX: Connect dengan proper error handling dan reconnect."""
        # Cek apakah connection masih hidup
        if self._client:
            try:
                # Test connection
                self._client.call('daemon.info')
                return True
            except Exception:
                # Connection stale, reconnect
                logger.debug("Stale connection, reconnecting...")
                try:
                    self._client.disconnect()
                except:
                    pass
                self._client = None

        # Buat koneksi baru
        max_retries = 3
        for attempt in range(1, max_retries + 1):
            try:
                self._client = DelugeRPCClient(
                    self.host,
                    self.daemon_port,
                    self.username,
                    self.password
                )
                self._client.connect()

                # Verify connection
                version = self._client.call('daemon.info')
                v = version.decode() if isinstance(version, bytes) else version
                logger.info(f"Connected to Deluge {v}")
                return True

            except Exception as e:
                logger.warning(
                    f"Connection attempt {attempt}/{max_retries} failed: {e}"
                )
                self._client = None
                if attempt < max_retries:
                    time.sleep(2)

        return False

    def _disconnect(self) -> None:
        """Disconnect from Deluge daemon."""
        try:
            if self._client:
                self._client.disconnect()
        except:
            pass
        finally:
            self._client = None

    def _ensure_connected(self) -> bool:
        """Helper: pastikan terhubung, return False jika gagal."""
        if not self._is_running:
            return False
        return self._connect()

    # ─────────────────────────────────────────────
    # Helper: Decode bytes dari deluge_client
    # ─────────────────────────────────────────────

    @staticmethod
    def _decode(value):
        """
        ✅ FIX: deluge_client mengembalikan bytes untuk keys dan values.
        Fungsi ini decode secara recursive.
        """
        if isinstance(value, bytes):
            return value.decode('utf-8', errors='replace')
        elif isinstance(value, dict):
            return {
                DelugeService._decode(k): DelugeService._decode(v)
                for k, v in value.items()
            }
        elif isinstance(value, (list, tuple)):
            return [DelugeService._decode(item) for item in value]
        return value

    # ─────────────────────────────────────────────
    # Daemon Start / Stop
    # ─────────────────────────────────────────────

    def _install_deluge(self) -> bool:
        """Install Deluge jika belum ada."""
        try:
            result = subprocess.run(
                ["deluged", "--version"],
                capture_output=True, text=True
            )
            if result.returncode == 0:
                logger.info(f"Deluge already installed: {result.stdout.strip()}")
                return True
        except FileNotFoundError:
            pass

        logger.info("Installing Deluge...")
        try:
            subprocess.run(
                ["apt-get", "update", "-qq"],
                capture_output=True, check=True
            )
            subprocess.run(
                ["apt-get", "install", "-y", "-qq",
                 "deluged", "deluge-console", "python3-libtorrent"],
                capture_output=True, check=True
            )
            logger.info("Deluge installed successfully")
            return True
        except Exception as e:
            logger.error(f"Failed to install Deluge: {e}")
            return False

    def start(self) -> Dict[str, Any]:
        """Start Deluge daemon."""
        if self._is_running and self._connect():
            return {
                "success": True,
                "message": "Deluge daemon already running"
            }

        try:
            # 1. Install jika perlu
            if not self._install_deluge():
                return {
                    "success": False,
                    "error": "Failed to install Deluge"
                }

            # 2. Setup auth & config
            self._setup_auth()
            self._setup_config()

            # 3. Kill proses lama yang mungkin masih nyangkut
            subprocess.run(["killall", "deluged"],
                           capture_output=True)
            time.sleep(2)

            # ✅ FIX: Command yang benar untuk deluged
            # -d = do not daemonize (kita manage sendiri)
            # -c = config directory
            # -p = pidfile, BUKAN port (port dari config)
            # -l = log file
            cmd = [
                "deluged",
                "-d",                          # foreground mode
                "-c", self.config_dir,         # config directory
                "-l", "/tmp/deluged.log",      # log file
                "-L", "info",                  # log level
            ]

            logger.info(f"Starting deluged: {' '.join(cmd)}")

            self.daemon_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            # 4. Tunggu daemon ready
            logger.info("Waiting for daemon to start...")
            connected = False
            for i in range(10):
                time.sleep(2)

                # Cek proses masih hidup
                if self.daemon_process.poll() is not None:
                    _, stderr = self.daemon_process.communicate()
                    err = stderr.decode() if stderr else "unknown error"
                    logger.error(f"Daemon exited: {err}")

                    # Cek log
                    log_content = ""
                    try:
                        with open("/tmp/deluged.log") as f:
                            log_content = f.read()[-500:]
                    except:
                        pass

                    return {
                        "success": False,
                        "error": f"Daemon exited unexpectedly: {err}",
                        "log": log_content
                    }

                # Coba connect
                if self._connect():
                    connected = True
                    break

                logger.debug(f"  Waiting... ({i+1}/10)")

            if not connected:
                # Kill dan report error
                self.daemon_process.terminate()
                self.daemon_process = None
                return {
                    "success": False,
                    "error": "Timeout: could not connect to daemon after 20s"
                }

            self._is_running = True

            # 5. Configure settings via RPC
            self._apply_settings()

            return {
                "success": True,
                "message": "Deluge daemon started successfully",
                "pid": self.daemon_process.pid,
                "host": self.host,
                "port": self.daemon_port,
                "download_path": self.download_path
            }

        except Exception as e:
            logger.error(f"Failed to start Deluge: {e}")
            return {"success": False, "error": str(e)}

    def stop(self) -> Dict[str, Any]:
        """Stop Deluge daemon."""
        try:
            self._disconnect()

            if self.daemon_process:
                self.daemon_process.terminate()
                try:
                    self.daemon_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.daemon_process.kill()
                self.daemon_process = None

            # Juga kill semua proses deluged yang tersisa
            subprocess.run(["killall", "deluged"], capture_output=True)

            self._is_running = False
            return {"success": True, "message": "Deluge daemon stopped"}

        except Exception as e:
            logger.error(f"Failed to stop Deluge: {e}")
            return {"success": False, "error": str(e)}

    def restart(self) -> Dict[str, Any]:
        """Restart Deluge daemon."""
        self.stop()
        time.sleep(3)
        return self.start()

    def _apply_settings(self) -> None:
        """✅ FIX: Apply settings via client.call(), bukan client.core."""
        try:
            if not self._connect():
                return

            config = {
                b"download_location": self.download_path,
                b"move_completed_path": self.download_path,
            }

            if self.max_download_speed != -1:
                config[b"max_download_speed"] = float(self.max_download_speed)

            if self.max_upload_speed != -1:
                config[b"max_upload_speed"] = float(self.max_upload_speed)

            self._client.call('core.set_config', config)
            logger.info("Settings applied successfully")

        except Exception as e:
            logger.error(f"Failed to apply settings: {e}")

    # ─────────────────────────────────────────────
    # Status
    # ─────────────────────────────────────────────

    def get_status(self) -> Dict[str, Any]:
        """Get Deluge daemon status."""
        status = {
            "running": self._is_running,
            "host": self.host,
            "port": self.daemon_port,
            "download_path": self.download_path,
            "connected": False,
        }

        if self._ensure_connected():
            try:
                # ✅ FIX: Pakai client.call()
                version = self._client.call('daemon.info')
                status["version"] = self._decode(version)
                status["connected"] = True

                session_keys = [
                    b'upload_rate', b'download_rate',
                    b'dht_nodes', b'has_incoming_connections'
                ]
                stats = self._client.call(
                    'core.get_session_status', session_keys
                )
                status["stats"] = self._decode(stats)

            except Exception as e:
                logger.error(f"Failed to get status: {e}")
                status["error"] = str(e)

        return status

    def get_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        if not self._ensure_connected():
            return {"success": False, "error": "Not connected"}

        try:
            keys = [
                b'upload_rate', b'download_rate',
                b'dht_nodes', b'num_peers',
                b'payload_upload_rate', b'payload_download_rate',
                b'total_upload', b'total_download',
            ]
            stats = self._client.call('core.get_session_status', keys)
            return {
                "success": True,
                "stats": self._decode(stats)
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    # ─────────────────────────────────────────────
    # Torrent Operations
    # ─────────────────────────────────────────────

    def add_torrent(
        self,
        magnet: Optional[str] = None,
        torrent_url: Optional[str] = None,
        torrent_file: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Add torrent. Supports:
        - magnet link
        - .torrent URL
        - .torrent file path
        """
        if not self._ensure_connected():
            return {"success": False, "error": "Not connected to Deluge"}

        options = {
            "download_location": self.download_path,
            "max_download_speed": self.max_download_speed,
            "max_upload_speed": self.max_upload_speed,
        }

        try:
            torrent_id = None

            # ✅ FIX: Magnet link
            if magnet:
                torrent_id = self._client.call(
                    'core.add_torrent_magnet',
                    magnet,
                    options
                )

            # ✅ FIX: URL (.torrent download URL)
            elif torrent_url:
                torrent_id = self._client.call(
                    'core.add_torrent_url',
                    torrent_url,
                    options
                )

            # ✅ FIX: File - harus base64 encode
            elif torrent_file and os.path.exists(torrent_file):
                with open(torrent_file, 'rb') as f:
                    file_data = base64.b64encode(f.read())

                torrent_id = self._client.call(
                    'core.add_torrent_file',
                    os.path.basename(torrent_file),
                    file_data,
                    options
                )
            else:
                return {
                    "success": False,
                    "error": "Provide magnet, torrent_url, or torrent_file"
                }

            if torrent_id is None:
                return {
                    "success": False,
                    "error": "Torrent already exists or invalid"
                }

            tid = self._decode(torrent_id)
            logger.info(f"Torrent added: {tid}")

            return {
                "success": True,
                "message": "Torrent added successfully",
                "torrent_id": tid
            }

        except Exception as e:
            logger.error(f"Failed to add torrent: {e}")
            return {"success": False, "error": str(e)}

    def list_torrents(self) -> Dict[str, Any]:
        """List all torrents with status."""
        if not self._ensure_connected():
            return {"success": False, "error": "Not connected to Deluge"}

        try:
            # ✅ FIX: Pakai client.call() dengan field list
            fields = [
                'name', 'state', 'progress',
                'download_payload_rate', 'upload_payload_rate',
                'num_seeds', 'num_peers',
                'total_wanted', 'total_done',
                'eta', 'ratio', 'save_path'
            ]

            raw = self._client.call(
                'core.get_torrents_status', {}, fields
            )

            torrents = []
            for torrent_id, info in raw.items():
                decoded = self._decode(info)
                decoded['id'] = self._decode(torrent_id)
                torrents.append(decoded)

            return {
                "success": True,
                "torrents": torrents,
                "count": len(torrents)
            }

        except Exception as e:
            logger.error(f"Failed to list torrents: {e}")
            return {"success": False, "error": str(e)}

    def get_torrent_details(self, torrent_id: str) -> Dict[str, Any]:
        """Get detailed information about a specific torrent."""
        if not self._ensure_connected():
            return {"success": False, "error": "Not connected to Deluge"}

        try:
            fields = [
                'name', 'state', 'progress',
                'download_payload_rate', 'upload_payload_rate',
                'num_seeds', 'num_peers',
                'total_wanted', 'total_done',
                'eta', 'ratio', 'save_path',
                'files', 'trackers', 'peers',
                'total_size', 'hash', 'message',
                'tracker_host', 'time_added'
            ]

            # ✅ FIX: client.call()
            raw = self._client.call(
                'core.get_torrent_status', torrent_id, fields
            )

            if not raw:
                return {"success": False, "error": "Torrent not found"}

            result = self._decode(raw)
            result['id'] = torrent_id

            return {"success": True, "torrent": result}

        except Exception as e:
            logger.error(f"Failed to get torrent details: {e}")
            return {"success": False, "error": str(e)}

    def pause_torrent(self, torrent_id: str) -> Dict[str, Any]:
        """Pause a torrent."""
        if not self._ensure_connected():
            return {"success": False, "error": "Not connected"}

        try:
            # ✅ FIX: client.call()
            self._client.call('core.pause_torrent', [torrent_id])
            return {
                "success": True,
                "message": f"Torrent {torrent_id} paused"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def resume_torrent(self, torrent_id: str) -> Dict[str, Any]:
        """Resume a torrent."""
        if not self._ensure_connected():
            return {"success": False, "error": "Not connected"}

        try:
            self._client.call('core.resume_torrent', [torrent_id])
            return {
                "success": True,
                "message": f"Torrent {torrent_id} resumed"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def remove_torrent(
        self, torrent_id: str, remove_data: bool = False
    ) -> Dict[str, Any]:
        """Remove a torrent."""
        if not self._ensure_connected():
            return {"success": False, "error": "Not connected"}

        try:
            self._client.call(
                'core.remove_torrent', torrent_id, remove_data
            )
            return {
                "success": True,
                "message": f"Torrent {torrent_id} removed"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    def pause_all(self) -> Dict[str, Any]:
        """Pause all torrents."""
        if not self._ensure_connected():
            return {"success": False, "error": "Not connected"}

        try:
            self._client.call('core.pause_all_torrents')
            return {"success": True, "message": "All torrents paused"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def resume_all(self) -> Dict[str, Any]:
        """Resume all torrents."""
        if not self._ensure_connected():
            return {"success": False, "error": "Not connected"}

        try:
            self._client.call('core.resume_all_torrents')
            return {"success": True, "message": "All torrents resumed"}
        except Exception as e:
            return {"success": False, "error": str(e)}