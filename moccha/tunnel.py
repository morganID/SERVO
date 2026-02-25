# tunnel.py - FIXED VERSION
import os
import time
import sys

_ngrok_tunnel = None

def start_ngrok(port, token):
    """Start ngrok tunnel - versi yang PASTI JALAN di Colab."""
    global _ngrok_tunnel

    if not token:
        raise ValueError("❌ Ngrok token kosong! Set token dulu.")

    # ── Method 1: Pakai pyngrok (recommended) ──
    try:
        from pyngrok import ngrok, conf

        # Kill semua proses ngrok lama dulu
        try:
            ngrok.kill()
            time.sleep(2)
        except:
            pass

        # Set auth token
        conf.get_default().auth_token = token

        # Buka tunnel
        _ngrok_tunnel = ngrok.connect(port, "http")
        public_url = _ngrok_tunnel.public_url

        # Force HTTPS
        if public_url.startswith("http://"):
            public_url = public_url.replace("http://", "https://")

        print(f"✅ Ngrok tunnel active: {public_url}", file=sys.stderr)
        return public_url

    except ImportError:
        print("⚠️ pyngrok tidak ditemukan, coba method 2...", file=sys.stderr)

    # ── Method 2: Pakai ngrok binary langsung ──
    try:
        import subprocess
        import json as _json

        # Set auth token via CLI
        subprocess.run(
            ["ngrok", "config", "add-authtoken", token],
            capture_output=True, text=True
        )

        # Start ngrok di background
        proc = subprocess.Popen(
            ["ngrok", "http", str(port), "--log=stdout", "--log-format=json"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        # Tunggu tunnel ready, baca dari API
        time.sleep(4)

        # Ngrok local API
        resp = requests.get("http://127.0.0.1:4040/api/tunnels", timeout=5)
        tunnels = resp.json()["tunnels"]

        if tunnels:
            public_url = tunnels[0]["public_url"]
            if public_url.startswith("http://"):
                public_url = public_url.replace("http://", "https://")
            print(f"✅ Ngrok tunnel active: {public_url}", file=sys.stderr)
            return public_url
        else:
            raise Exception("Tidak ada tunnel yang terbuka")

    except Exception as e2:
        raise Exception(f"Semua method ngrok gagal: {e2}")


def stop_ngrok():
    """Stop ngrok tunnel."""
    global _ngrok_tunnel
    try:
        from pyngrok import ngrok
        ngrok.kill()
        _ngrok_tunnel = None
        print("🛑 Ngrok stopped", file=sys.stderr)
    except:
        # Fallback: kill process
        import subprocess
        subprocess.run(["killall", "ngrok"], capture_output=True)