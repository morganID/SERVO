"""Ngrok tunnel manager."""

import re


def start_ngrok(port, token):
    """Connect ngrok, return public URL string."""
    from pyngrok import ngrok

    if token:
        ngrok.set_auth_token(token)

    tun = ngrok.connect(port)
    raw = str(tun)

    # Bersihkan URL
    m = re.search(r'https?://[^\s"]+', raw)
    return m.group() if m else raw


def stop_ngrok():
    """Kill ngrok."""
    try:
        from pyngrok import ngrok
        ngrok.kill()
    except:
        pass