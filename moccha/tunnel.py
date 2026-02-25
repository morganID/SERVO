"""
Tunnel manager - Cloudflare Tunnel (cloudflared).
Gratis, tanpa akun, tanpa limit, tidak pernah nyangkut.
"""

import os
import sys
import re
import time
import subprocess
import threading
import logging

logger = logging.getLogger(__name__)

_tunnel_process = None
_tunnel_url = None


def _install_cloudflared():
    """Install cloudflared binary jika belum ada."""
    try:
        result = subprocess.run(
            ["cloudflared", "--version"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            ver = result.stdout.strip() or result.stderr.strip()
            logger.info(f"cloudflared ready: {ver}")
            return True
    except FileNotFoundError:
        pass

    logger.info("Installing cloudflared...")
    try:
        subprocess.run([
            "wget", "-q",
            "https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64",
            "-O", "/usr/local/bin/cloudflared"
        ], check=True, timeout=60)

        subprocess.run(
            ["chmod", "+x", "/usr/local/bin/cloudflared"],
            check=True
        )

        # Verify
        result = subprocess.run(
            ["cloudflared", "--version"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            logger.info("cloudflared installed successfully")
            return True

        raise Exception("Binary downloaded but won't execute")

    except Exception as e:
        logger.error(f"Failed to install cloudflared: {e}")
        return False


def _read_url_from_process(process, timeout=30):
    """
    Baca URL dari cloudflared stderr output.
    Format: https://xxx-xxx-xxx.trycloudflare.com
    """
    url_found = {"url": None}
    pattern = re.compile(r'(https://[a-zA-Z0-9\-]+\.trycloudflare\.com)')

    def reader():
        try:
            for line in iter(process.stderr.readline, b''):
                line_str = line.decode('utf-8', errors='replace').strip()
                if line_str:
                    logger.debug(f"cloudflared: {line_str}")

                match = pattern.search(line_str)
                if match:
                    url_found["url"] = match.group(1)
                    return

                # Cek error
                if "error" in line_str.lower() and "retrying" not in line_str.lower():
                    logger.warning(f"cloudflared error: {line_str}")

        except Exception as e:
            logger.error(f"Error reading cloudflared output: {e}")

    thread = threading.Thread(target=reader, daemon=True)
    thread.start()
    thread.join(timeout=timeout)

    return url_found["url"]


def start_tunnel(port, **kwargs):
    """
    Start cloudflare tunnel.

    Args:
        port: Local port to expose

    Returns:
        Public HTTPS URL (https://xxx.trycloudflare.com)

    Raises:
        Exception jika gagal
    """
    global _tunnel_process, _tunnel_url

    # Stop tunnel lama
    stop_tunnel()
    time.sleep(1)

    # Install jika belum ada
    if not _install_cloudflared():
        raise Exception(
            "Failed to install cloudflared. "
            "Manual install: wget -q https://github.com/cloudflare/cloudflared/"
            "releases/latest/download/cloudflared-linux-amd64 "
            "-O /usr/local/bin/cloudflared && chmod +x /usr/local/bin/cloudflared"
        )

    # Kill proses lama yang mungkin nyangkut
    subprocess.run(["killall", "cloudflared"], capture_output=True)
    time.sleep(1)

    logger.info(f"Starting cloudflared tunnel → localhost:{port}")

    # Start cloudflared
    _tunnel_process = subprocess.Popen(
        [
            "cloudflared", "tunnel",
            "--url", f"http://localhost:{port}",
            "--no-autoupdate",
            "--logfile", "/tmp/cloudflared.log",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Tunggu dan baca URL dari output
    url = _read_url_from_process(_tunnel_process, timeout=30)

    if not url:
        # Cek apakah proses masih hidup
        if _tunnel_process.poll() is not None:
            _, stderr = _tunnel_process.communicate()
            err = stderr.decode('utf-8', errors='replace') if stderr else "unknown"
            _tunnel_process = None
            raise Exception(f"cloudflared exited: {err}")

        # Proses hidup tapi URL belum muncul, coba baca dari log
        try:
            time.sleep(5)
            with open("/tmp/cloudflared.log", "r") as f:
                log_content = f.read()

            pattern = re.compile(r'(https://[a-zA-Z0-9\-]+\.trycloudflare\.com)')
            match = pattern.search(log_content)
            if match:
                url = match.group(1)
        except:
            pass

    if not url:
        stop_tunnel()
        raise Exception(
            "cloudflared started but URL not found. "
            "Check /tmp/cloudflared.log for details."
        )

    _tunnel_url = url
    logger.info(f"✅ Tunnel active: {url}")

    # Background thread: monitor proses
    def monitor():
        if _tunnel_process:
            _tunnel_process.wait()
            logger.warning("cloudflared process exited")

    threading.Thread(target=monitor, daemon=True).start()

    return url


def stop_tunnel():
    """Stop cloudflared tunnel."""
    global _tunnel_process, _tunnel_url

    # Kill tracked process
    if _tunnel_process:
        try:
            _tunnel_process.terminate()
            try:
                _tunnel_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                _tunnel_process.kill()
        except:
            pass
        _tunnel_process = None

    # Kill semua proses cloudflared
    subprocess.run(["killall", "cloudflared"], capture_output=True)

    _tunnel_url = None
    logger.info("🛑 Tunnel stopped")


def get_tunnel_url():
    """Get current tunnel URL."""
    return _tunnel_url


def is_tunnel_alive():
    """Cek apakah tunnel masih aktif."""
    if _tunnel_process is None:
        return False
    return _tunnel_process.poll() is None