"""
CLI entry point — fully non-blocking.

Usage:
    moccha start --token=xxx
    moccha stop
    moccha status
    moccha info
"""

import os
import sys
import json
import uuid
import argparse
import subprocess
import time

from .daemon import PID_FILE, INFO_FILE, load_info, stop_daemon
from .services.service_manager import ServiceManager


def main():
    parser = argparse.ArgumentParser(prog='moccha')
    sub = parser.add_subparsers(dest='command')

    p_start = sub.add_parser('start')
    p_start.add_argument('--port', type=int, default=5000)
    p_start.add_argument('--token', required=True)
    p_start.add_argument('--key', default=None)
    p_start.add_argument('--workspace', default='/content')

    sub.add_parser('stop')
    sub.add_parser('status')
    sub.add_parser('info')

    p_restart = sub.add_parser('restart')
    p_restart.add_argument('--port', type=int, default=5000)
    p_restart.add_argument('--token', required=True)
    p_restart.add_argument('--key', default=None)
    p_restart.add_argument('--workspace', default='/content')

    # Service management commands
    p_services = sub.add_parser('services')
    p_services_status = sub.add_parser('services-status')
    p_service_start = sub.add_parser('service-start')
    p_service_start.add_argument('service_name')
    p_service_stop = sub.add_parser('service-stop')
    p_service_stop.add_argument('service_name')
    p_service_restart = sub.add_parser('service-restart')
    p_service_restart.add_argument('service_name')

    # Deluge commands
    p_deluge_add = sub.add_parser('deluge-add')
    p_deluge_add.add_argument('torrent_url')
    p_deluge_list = sub.add_parser('deluge-list')

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        return

    # ══════════════════════════════════════════════════════
    if args.command == 'start':
        if os.path.exists(PID_FILE):
            info = load_info()
            if info:
                print(f"⚠️  Sudah jalan!")
                print(f"   URL: {info.get('url')}")
                print(f"   Key: {info.get('api_key')}")
                return

        api_key = args.key or str(uuid.uuid4())

        cmd = [
            sys.executable, '-c',
            f"""
import sys, os
sys.path.insert(0, '{os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}')
from moccha.daemon import run_daemon
run_daemon(
    port={args.port},
    ngrok_token="{args.token}",
    api_key="{api_key}",
    workspace="{args.workspace}",
)
"""
        ]

        # ━━━ SPAWN & EXIT IMMEDIATELY ━━━━━━━━━━━━━━━━━━━
        log = open('/tmp/moccha.log', 'w')
        subprocess.Popen(
            cmd,
            stdout=log,
            stderr=log,
            stdin=subprocess.DEVNULL,      # no stdin
            start_new_session=True,        # detach completely
        )
        log.close()                        # parent lepas file handle

        # LANGSUNG PRINT & RETURN — ZERO SLEEP
        print("🚀 Flying to the moon!")
     
        return  # ← CELL LANGSUNG SELESAI

    # ══════════════════════════════════════════════════════
    elif args.command == 'stop':
        print("🛑 Stopping...")
        if stop_daemon():
            print("✅ Stopped.")
        else:
            print("⚠️  Tidak sedang jalan.")

    # ══════════════════════════════════════════════════════
    elif args.command == 'status':
        info = load_info()
        if info and os.path.exists(PID_FILE):
            try:
                os.kill(info['pid'], 0)
                print(f"🟢 RUNNING (PID: {info['pid']})")
                print(f"   URL: {info['url']}")
                print(f"   Key: {info['api_key']}")
            except OSError:
                print("🔴 STOPPED (stale PID)")
        else:
            print("🔴 STOPPED")

    # ══════════════════════════════════════════════════════
    elif args.command == 'info':
        info = load_info()
        if info:
            print("=" * 55)
            print("  ✅ SERVER INFO")
            print("=" * 55)
            print(f"  🌍 URL : {info['url']}")
            print(f"  🔑 Key : {info['api_key']}")
            print(f"  📍 Port: {info['port']}")
            print(f"  📂 PID : {info['pid']}")
            print("=" * 55)
            print()
            print("  📋 Test:")
            print(f'  curl -H "X-API-Key: {info["api_key"]}" {info["url"]}/status')
        else:
            print("❌ Belum jalan. Start dulu: moccha start --token=xxx")

    # ══════════════════════════════════════════════════════
    elif args.command == 'restart':
        stop_daemon()
        time.sleep(2)
        os.execvp(sys.executable, [
            sys.executable, '-m', 'moccha.cli',
            'start',
            '--port', str(args.port),
            '--token', args.token,
            '--key', args.key or str(uuid.uuid4()),
            '--workspace', args.workspace,
        ])

    # ══════════════════════════════════════════════════════
    # Service Management Commands
    # ══════════════════════════════════════════════════════
    
    elif args.command == 'services':
        service_manager = ServiceManager()
        services = service_manager.list_services()
        print("Available services:")
        for service in services:
            print(f"  - {service}")
    
    elif args.command == 'services-status':
        service_manager = ServiceManager()
        status = service_manager.get_all_services_status()
        print("Service status:")
        for service, info in status.items():
            if isinstance(info, dict) and info.get("running"):
                print(f"  ✅ {service}: Running")
            else:
                print(f"  ❌ {service}: Not running")
    
    elif args.command == 'service-start':
        service_name = args.service_name
        service_manager = ServiceManager()
        result = service_manager.start_service(service_name)
        if result.get("success"):
            print(f"✅ {service_name} started successfully")
        else:
            print(f"❌ Failed to start {service_name}: {result.get('error')}")
    
    elif args.command == 'service-stop':
        service_name = args.service_name
        service_manager = ServiceManager()
        result = service_manager.stop_service(service_name)
        if result.get("success"):
            print(f"✅ {service_name} stopped successfully")
        else:
            print(f"❌ Failed to stop {service_name}: {result.get('error')}")
    
    elif args.command == 'service-restart':
        service_name = args.service_name
        service_manager = ServiceManager()
        result = service_manager.restart_service(service_name)
        if result.get("success"):
            print(f"✅ {service_name} restarted successfully")
        else:
            print(f"❌ Failed to restart {service_name}: {result.get('error')}")
    
    elif args.command == 'deluge-add':
        torrent_url = args.torrent_url
        service_manager = ServiceManager()
        deluge_service = service_manager.get_service("deluge")
        if not deluge_service:
            print("❌ Deluge service not found or not enabled")
            return
        
        result = deluge_service.add_torrent(torrent_url=torrent_url)
        if result.get("success"):
            print(f"✅ Torrent added successfully: {result.get('torrent_id')}")
        else:
            print(f"❌ Failed to add torrent: {result.get('error')}")
    
    elif args.command == 'deluge-list':
        service_manager = ServiceManager()
        deluge_service = service_manager.get_service("deluge")
        if not deluge_service:
            print("❌ Deluge service not found or not enabled")
            return
        
        result = deluge_service.list_torrents()
        if result.get("success"):
            torrents = result.get("torrents", [])
            print(f"Found {len(torrents)} torrents:")
            for torrent in torrents:
                print(f"  - {torrent['name']} ({torrent['progress']:.1f}%) - {torrent['state']}")
        else:
            print(f"❌ Failed to list torrents: {result.get('error')}")


if __name__ == '__main__':
    main()
