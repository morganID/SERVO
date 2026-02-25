"""Ngrok tunnel manager."""

import re
import sys


def start_ngrok(port, token):
    """Connect ngrok, return public URL string."""
    from pyngrok import ngrok

    if token:
        print(f"🔑 Setting ngrok auth token...", file=sys.stderr)
        ngrok.set_auth_token(token)
    else:
        print(f"⚠️  No ngrok auth token provided, using anonymous connection...", file=sys.stderr)

    print(f"📡 Connecting to ngrok on port {port}...", file=sys.stderr)
    try:
        tun = ngrok.connect(port)
        raw = str(tun)
        print(f"✅ Ngrok connected successfully: {raw}", file=sys.stderr)
        
        # Bersihkan URL
        m = re.search(r'https?://[^\s"]+', raw)
        url = m.group() if m else raw
        print(f"🌐 Public URL: {url}", file=sys.stderr)
        return url
    except Exception as e:
        print(f"❌ Ngrok connection failed: {e}", file=sys.stderr)
        print(f"⚠️  Error details: {type(e).__name__}", file=sys.stderr)
        return f"http://localhost:{port}"


def stop_ngrok():
    """Kill ngrok."""
    print(f"🛑 Stopping ngrok tunnel...", file=sys.stderr)
    try:
        from pyngrok import ngrok
        ngrok.kill()
        print("✅ Ngrok stopped successfully", file=sys.stderr)
    except Exception as e:
        print(f"⚠️  Failed to stop ngrok: {e}", file=sys.stderr)
        print(f"⚠️  Error details: {type(e).__name__}", file=sys.stderr)
