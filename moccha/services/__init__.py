"""Moccha - Download manager for Google Colab."""

from moccha.daemon import load_info, is_running


def get_url():
    info = load_info()
    return info.get("url") if info else None


def get_info():
    return load_info()


def status():
    if is_running():
        info = load_info()
        if info:
            print(f"🟢 RUNNING")
            print(f"   URL: {info.get('url')}")
            print(f"   Key: {info.get('api_key')}")
        else:
            print("🟡 Running but no info")
    else:
        print("🔴 NOT RUNNING")