"""Cloudflare tunnel manager (menggantikan ngrok).

Menggunakan binary `cloudflared` dan mode trycloudflare.com (tanpa akun).
Pastikan `cloudflared` tersedia di PATH.
"""

import re
import subprocess
import threading
from typing import Optional

_proc_lock = threading.Lock()
_proc: Optional[subprocess.Popen] = None


def start_ngrok(port, token=None):  # noqa: ARG001 - token disimpan untuk kompatibilitas
    """Start Cloudflare tunnel, return public URL string.

    Nama fungsi tetap `start_ngrok` demi kompatibilitas dengan kode lama.
    Sekarang implementasi menggunakan `cloudflared tunnel --url ...`.
    """
    global _proc

    with _proc_lock:
        if _proc is not None and _proc.poll() is None:
            # Sudah jalan; tidak ada URL yang disimpan di sini, jadi biarkan caller restart dulu kalau perlu.
            raise RuntimeError("Cloudflare tunnel sudah berjalan.")

        cmd = [
            "cloudflared",
            "tunnel",
            "--url",
            f"http://127.0.0.1:{port}",
            "--no-autoupdate",
        ]

        # Jalankan cloudflared dan baca output untuk mencari URL trycloudflare.com
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        _proc = proc

    url = None
    if proc.stdout is None:
        raise RuntimeError("Gagal menjalankan cloudflared (tidak ada stdout).")

    for line in proc.stdout:
        # Contoh: `https://xxxx-....trycloudflare.com`
        m = re.search(r"https://[a-zA-Z0-9.-]+trycloudflare\.com", line)
        if m:
            url = m.group(0)
            break

        # Kalau proses mati sebelum URL muncul → error
        if proc.poll() is not None:
            break

    if not url:
        raise RuntimeError("Gagal mendapatkan URL Cloudflare tunnel dari output cloudflared.")

    # Biarkan `cloudflared` tetap jalan di background; stdout boleh dibiarkan begitu saja.
    return url


def stop_ngrok():
    """Stop Cloudflare tunnel process (kompatibel dengan nama lama)."""
    global _proc

    with _proc_lock:
        if _proc is None:
            return

        if _proc.poll() is None:
            try:
                _proc.terminate()
                _proc.wait(timeout=5)
            except Exception:
                try:
                    _proc.kill()
                except Exception:
                    pass

        _proc = None