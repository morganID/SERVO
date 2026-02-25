"""CLI entry point - with service management."""

import os
import sys
import json
import time
import argparse
import subprocess
import secrets

from moccha.daemon import (
    stop_daemon, is_running,
    load_info, PID_FILE, INFO_FILE, LOG_FILE
)


def generate_api_key():
    return secrets.token_hex(16)


# ─────────────────────────────────────────────
# Server Commands
# ─────────────────────────────────────────────

def cmd_start(args):
    if is_running():
        info = load_info()
        if info:
            print(f"🟢 Already running (PID: {info.get('pid')})")
            print(f"   URL: {info.get('url')}")
            print(f"   Key: {info.get('api_key')}")
            return

        print("⚠️ Stale PID file, cleaning up...")
        try:
            os.remove(PID_FILE)
        except:
            pass

    port = args.port or 5000
    api_key = args.api_key or generate_api_key()
    workspace = args.workspace or os.path.expanduser("~/moccha_workspace")
    os.makedirs(workspace, exist_ok=True)

    try:
        open(LOG_FILE, 'w').close()
    except:
        pass

    print(f"🚀 Starting server...")
    print(f"   Port: {port}")
    print(f"   Workspace: {workspace}")

    cmd = (
        f'nohup {sys.executable} -m moccha.daemon_entry '
        f'--port {port} '
        f'--api-key {api_key} '
        f'--workspace {workspace} '
        f'>> {LOG_FILE} 2>&1 &'
    )
    os.system(cmd)

    print("⏳ Waiting for tunnel...")

    for i in range(15):
        time.sleep(1)
        info = load_info()
        if info and info.get("url") and "localhost" not in info["url"]:
            print(f"\n{'='*55}")
            print(f"  🟢 Server is running!")
            print(f"  🌐 URL: {info['url']}")
            print(f"  🔑 Key: {api_key}")
            print(f"  📂 Workspace: {workspace}")
            print(f"{'='*55}")
            return

    info = load_info()
    if info:
        print(f"\n🟡 Server starting (tunnel connecting...)")
        print(f"   URL: {info.get('url', 'pending...')}")
        print(f"   Key: {api_key}")
        print(f"\n   !moccha status  — check status")
        print(f"   !moccha logs    — check logs")
    else:
        print(f"\n⚠️ May have failed. Check: !cat {LOG_FILE}")


def cmd_stop(args):
    if not is_running():
        print("🔴 Not running")
        return

    if stop_daemon():
        print("🛑 Server stopped")
    else:
        print("⚠️ Force cleanup...")
        subprocess.run(["killall", "cloudflared"], capture_output=True)
        for f in [PID_FILE, INFO_FILE]:
            try:
                os.remove(f)
            except:
                pass
        print("🧹 Done")


def cmd_status(args):
    if is_running():
        info = load_info()
        if info:
            print(f"🟢 RUNNING (PID: {info.get('pid')})")
            print(f"   URL: {info.get('url')}")
            print(f"   Key: {info.get('api_key')}")
            print(f"   Tunnel: {info.get('tunnel', 'cloudflared')}")
            print(f"   Started: {info.get('started')}")
        else:
            print("🟡 Running but no info file")
    else:
        print("🔴 NOT RUNNING")


def cmd_restart(args):
    print("🔄 Restarting...")
    cmd_stop(args)
    time.sleep(3)
    cmd_start(args)


def cmd_logs(args):
    if os.path.exists(LOG_FILE):
        n = args.lines or 50
        result = subprocess.run(
            ["tail", "-n", str(n), LOG_FILE],
            capture_output=True, text=True
        )
        print(result.stdout)
    else:
        print("No log file found")


def cmd_url(args):
    info = load_info()
    if info and info.get("url"):
        print(info["url"])
    else:
        print("No URL available")


# ─────────────────────────────────────────────
# Service Commands
# ─────────────────────────────────────────────

def _get_api():
    """Helper: get API base URL and key."""
    info = load_info()
    if not info:
        print("❌ Server not running. Start with: moccha start")
        return None, None

    url = info.get("url", "")
    key = info.get("api_key", "")

    if "localhost" in url:
        url = f"http://localhost:{info.get('port', 5000)}"

    return url, key


def _api_request(method, endpoint, data=None):
    """Helper: make API request to moccha server."""
    import requests

    url, key = _get_api()
    if not url:
        return None

    headers = {"X-API-Key": key, "Content-Type": "application/json"}
    full_url = f"{url}{endpoint}"

    try:
        if method == "GET":
            r = requests.get(full_url, headers=headers, timeout=15)
        elif method == "POST":
            r = requests.post(full_url, headers=headers, json=data or {}, timeout=15)
        elif method == "DELETE":
            r = requests.delete(full_url, headers=headers, timeout=15)
        else:
            print(f"❌ Unknown method: {method}")
            return None

        return r.json()

    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to server at {url}")
        print(f"   Is it running? Check: moccha status")
        return None
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return None


def cmd_service(args):
    """Service management commands."""
    action = args.action
    service_name = args.name

    if action == "list":
        result = _api_request("GET", "/api/services")
        if result:
            services = result.get("services", [])
            if not services:
                print("📭 No services configured")
                return

            print(f"\n{'='*50}")
            print(f"  📦 Services")
            print(f"{'='*50}")
            for svc in services:
                name = svc.get("name", "?")
                enabled = svc.get("enabled", False)
                running = svc.get("running", False)
                initialized = svc.get("initialized", False)

                if running:
                    icon = "🟢"
                    status = "RUNNING"
                elif initialized:
                    icon = "🟡"
                    status = "STOPPED"
                elif enabled:
                    icon = "🔴"
                    status = "ERROR"
                else:
                    icon = "⚫"
                    status = "DISABLED"

                print(f"  {icon} {name:15s} {status}")
            print()
        return

    if not service_name:
        print("❌ Service name required")
        print("   Usage: moccha service start deluge")
        print("   Available: deluge, jdownloader, mega")
        return

    if action == "start":
        print(f"🚀 Starting {service_name}...")
        result = _api_request("POST", f"/api/services/{service_name}/start")
        if result:
            if result.get("success"):
                print(f"✅ {service_name} started!")
                # Print extra info
                pid = result.get("pid")
                port = result.get("port")
                dl_path = result.get("download_path")
                if pid:
                    print(f"   PID: {pid}")
                if port:
                    print(f"   Port: {port}")
                if dl_path:
                    print(f"   Downloads: {dl_path}")
            else:
                print(f"❌ Failed: {result.get('error', 'unknown')}")

    elif action == "stop":
        print(f"🛑 Stopping {service_name}...")
        result = _api_request("POST", f"/api/services/{service_name}/stop")
        if result:
            if result.get("success"):
                print(f"✅ {service_name} stopped")
            else:
                print(f"❌ Failed: {result.get('error', 'unknown')}")

    elif action == "restart":
        print(f"🔄 Restarting {service_name}...")
        result = _api_request("POST", f"/api/services/{service_name}/restart")
        if result:
            if result.get("success"):
                print(f"✅ {service_name} restarted")
            else:
                print(f"❌ Failed: {result.get('error', 'unknown')}")

    elif action == "status":
        result = _api_request("GET", f"/api/services/{service_name}/status")
        if result:
            print(f"\n{'='*50}")
            print(f"  📦 {service_name}")
            print(f"{'='*50}")
            for k, v in result.items():
                if k != "success":
                    print(f"  {k}: {v}")
            print()

    elif action == "config":
        result = _api_request("GET", f"/api/services/{service_name}/config")
        if result:
            print(f"\n⚙️ Config for {service_name}:")
            print(json.dumps(result, indent=2))

    else:
        print(f"❌ Unknown action: {action}")
        print("   Actions: list, start, stop, restart, status, config")


# ─────────────────────────────────────────────
# Torrent Commands
# ─────────────────────────────────────────────

def cmd_torrent(args):
    """Torrent management commands."""
    action = args.action

    if action == "add":
        if not args.url:
            print("❌ URL/magnet required: moccha torrent add <magnet_or_url>")
            return

        url_or_magnet = args.url
        data = {}

        if url_or_magnet.startswith("magnet:"):
            data["magnet"] = url_or_magnet
            print(f"🧲 Adding magnet link...")
        else:
            data["torrent_url"] = url_or_magnet
            print(f"📥 Adding torrent URL...")

        result = _api_request("POST", "/api/torrents/add", data)
        if result:
            if result.get("success"):
                tid = result.get("torrent_id", "?")
                print(f"✅ Torrent added! ID: {tid}")
            else:
                print(f"❌ Failed: {result.get('error', 'unknown')}")

    elif action == "list":
        result = _api_request("GET", "/api/torrents")
        if result:
            torrents = result.get("torrents", [])
            count = result.get("count", 0)

            if count == 0:
                print("📭 No torrents")
                return

            print(f"\n{'='*65}")
            print(f"  📦 Torrents ({count})")
            print(f"{'='*65}")

            for t in torrents:
                name = t.get("name", "?")
                state = t.get("state", "?")
                progress = t.get("progress", 0)
                dl_rate = t.get("download_payload_rate", 0) / 1024
                ul_rate = t.get("upload_payload_rate", 0) / 1024
                tid = t.get("id", "?")

                # Progress bar
                bar_len = 20
                filled = int(bar_len * progress / 100)
                bar = '█' * filled + '░' * (bar_len - filled)

                # State icon
                icons = {
                    "Downloading": "⬇️",
                    "Seeding": "⬆️",
                    "Paused": "⏸️",
                    "Queued": "⏳",
                    "Checking": "🔍",
                    "Error": "❌",
                }
                icon = icons.get(state, "📦")

                print(f"\n  {icon} {name}")
                print(f"     [{bar}] {progress:.1f}%")
                print(f"     {state} | ⬇️ {dl_rate:.1f} KB/s | ⬆️ {ul_rate:.1f} KB/s")
                print(f"     ID: {tid[:16]}...")

            print()

    elif action == "pause":
        if not args.torrent_id:
            print("❌ Torrent ID required: moccha torrent pause <id>")
            return
        result = _api_request("POST", f"/api/torrents/{args.torrent_id}/pause")
        if result and result.get("success"):
            print(f"⏸️ Torrent paused")
        else:
            print(f"❌ Failed: {result.get('error', 'unknown') if result else 'no response'}")

    elif action == "resume":
        if not args.torrent_id:
            print("❌ Torrent ID required: moccha torrent resume <id>")
            return
        result = _api_request("POST", f"/api/torrents/{args.torrent_id}/resume")
        if result and result.get("success"):
            print(f"▶️ Torrent resumed")
        else:
            print(f"❌ Failed: {result.get('error', 'unknown') if result else 'no response'}")

    elif action == "remove":
        if not args.torrent_id:
            print("❌ Torrent ID required: moccha torrent remove <id>")
            return
        remove_data = getattr(args, 'remove_data', False)
        endpoint = f"/api/torrents/{args.torrent_id}"
        if remove_data:
            endpoint += "?remove_data=true"
        result = _api_request("DELETE", endpoint)
        if result and result.get("success"):
            print(f"🗑️ Torrent removed")
        else:
            print(f"❌ Failed: {result.get('error', 'unknown') if result else 'no response'}")

    elif action == "info":
        if not args.torrent_id:
            print("❌ Torrent ID required: moccha torrent info <id>")
            return
        result = _api_request("GET", f"/api/torrents/{args.torrent_id}")
        if result and result.get("success"):
            torrent = result.get("torrent", {})
            print(f"\n{'='*50}")
            print(f"  📦 {torrent.get('name', '?')}")
            print(f"{'='*50}")
            for k, v in torrent.items():
                if k not in ("files", "trackers", "peers"):
                    print(f"  {k}: {v}")

            files = torrent.get("files", [])
            if files:
                print(f"\n  📁 Files ({len(files)}):")
                for f in files[:10]:
                    size_mb = f.get("size", 0) / 1024 / 1024
                    print(f"     {f.get('path', '?')} ({size_mb:.1f} MB)")
                if len(files) > 10:
                    print(f"     ... and {len(files) - 10} more")
            print()
        else:
            print(f"❌ Failed: {result.get('error', 'unknown') if result else 'no response'}")

    elif action == "stats":
        result = _api_request("GET", "/api/torrents/stats")
        if result and result.get("success"):
            stats = result.get("stats", {})
            print(f"\n📊 Deluge Stats:")
            for k, v in stats.items():
                if "rate" in k:
                    print(f"  {k}: {v/1024:.1f} KB/s")
                else:
                    print(f"  {k}: {v}")
            print()

    else:
        print(f"❌ Unknown action: {action}")
        print("   Actions: add, list, pause, resume, remove, info, stats")


# ─────────────────────────────────────────────
# Main Parser
# ─────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        prog="moccha",
        description="Moccha - Download Manager for Colab",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  moccha start                          Start server
  moccha status                         Show status
  moccha service list                   List services
  moccha service start deluge           Start Deluge
  moccha torrent add "magnet:?xt=..."   Add torrent
  moccha torrent list                   List torrents
  moccha logs                           Show logs
  moccha stop                           Stop server
        """
    )

    sub = parser.add_subparsers(dest="command")

    # ── start ──
    p = sub.add_parser("start", help="Start server")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--api-key", type=str, default=None)
    p.add_argument("--workspace", type=str, default=None)
    p.add_argument("--ngrok-token", type=str, default=None,
                   help="(deprecated, ignored)")
    p.set_defaults(func=cmd_start)

    # ── stop ──
    p = sub.add_parser("stop", help="Stop server")
    p.set_defaults(func=cmd_stop)

    # ── status ──
    p = sub.add_parser("status", help="Show status")
    p.set_defaults(func=cmd_status)

    # ── restart ──
    p = sub.add_parser("restart", help="Restart server")
    p.add_argument("--port", type=int, default=5000)
    p.add_argument("--api-key", type=str, default=None)
    p.add_argument("--workspace", type=str, default=None)
    p.set_defaults(func=cmd_restart)

    # ── logs ──
    p = sub.add_parser("logs", help="Show logs")
    p.add_argument("-n", "--lines", type=int, default=50)
    p.set_defaults(func=cmd_logs)

    # ── url ──
    p = sub.add_parser("url", help="Show current URL")
    p.set_defaults(func=cmd_url)

    # ── service ──
    p = sub.add_parser("service", help="Manage services")
    p.add_argument("action", type=str,
                   choices=["list", "start", "stop", "restart", "status", "config"],
                   help="Action to perform")
    p.add_argument("name", type=str, nargs="?", default=None,
                   help="Service name (deluge, jdownloader, mega)")
    p.set_defaults(func=cmd_service)

    # ── torrent ──
    p = sub.add_parser("torrent", help="Manage torrents")
    p.add_argument("action", type=str,
                   choices=["add", "list", "pause", "resume", "remove", "info", "stats"],
                   help="Action to perform")
    p.add_argument("url", type=str, nargs="?", default=None,
                   help="Magnet link or torrent URL (for add)")
    p.add_argument("--id", dest="torrent_id", type=str, default=None,
                   help="Torrent ID (for pause/resume/remove/info)")
    p.add_argument("--remove-data", action="store_true", default=False,
                   help="Also remove downloaded data (for remove)")
    p.set_defaults(func=cmd_torrent)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    args.func(args)


if __name__ == "__main__":
    main()