# Moccha Services Documentation

## Overview

Moccha now supports multiple download services including Deluge, JDownloader, and MEGA. This document explains how to use and configure these services.

## Services Architecture

The services are organized in a modular architecture:

```
moccha/
├── services/
│   ├── service_manager.py    # Main service manager
│   ├── deluge_service.py     # Deluge service implementation
│   ├── jdownloader_service.py # JDownloader service (placeholder)
│   └── mega_service.py       # MEGA service (placeholder)
├── models/
│   ├── service_config.py     # Configuration models
│   └── download_task.py      # Download task model (placeholder)
└── utils/
    ├── process_manager.py    # Process management utilities
    └── config_loader.py      # Configuration loader (placeholder)
```

## Deluge Service

### Features

- Start/stop Deluge daemon
- Add torrents (from URL or file)
- List and manage torrents
- Monitor download/upload stats
- Pause/resume/remove torrents
- View peer information

### Configuration

Create or edit `~/.moccha/services_config.json`:

```json
{
  "services": {
    "deluge": {
      "enabled": true,
      "host": "localhost",
      "port": 58846,
      "download_path": "/downloads/torrents",
      "max_download_speed": 0,
      "max_upload_speed": 0,
      "auto_add_folder": "/torrents/watch"
    }
  }
}
```

### API Endpoints

#### Service Management
- `GET /services` - List all services
- `GET /services/status` - Get status of all services
- `GET /services/deluge/status` - Get Deluge status
- `POST /services/deluge/start` - Start Deluge daemon
- `POST /services/deluge/stop` - Stop Deluge daemon
- `POST /services/deluge/restart` - Restart Deluge daemon

#### Torrent Management
- `GET /services/deluge/torrents` - List all torrents
- `POST /services/deluge/torrents` - Add torrent
- `GET /services/deluge/torrents/{hash}` - Get torrent details
- `POST /services/deluge/torrents/{hash}/pause` - Pause torrent
- `POST /services/deluge/torrents/{hash}/resume` - Resume torrent
- `POST /services/deluge/torrents/{hash}/remove` - Remove torrent

#### Monitoring
- `GET /services/deluge/stats` - Get download/upload stats
- `GET /services/deluge/peers/{hash}` - Get peer information

### CLI Commands

```bash
# Service management
moccha services                    # List available services
moccha services-status             # Show service status
moccha service-start deluge        # Start Deluge
moccha service-stop deluge         # Stop Deluge
moccha service-restart deluge      # Restart Deluge

# Deluge operations
moccha deluge-add "magnet:?xt=urn:btih:..."  # Add torrent
moccha deluge-list                           # List torrents
```

### Example Usage

#### Add a torrent via API
```bash
curl -X POST -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"torrent_url": "magnet:?xt=urn:btih:example"}' \
  http://localhost:5000/services/deluge/torrents
```

#### Start Deluge daemon
```bash
curl -X POST -H "X-API-Key: your-api-key" \
  http://localhost:5000/services/deluge/start
```

#### Get torrent list
```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:5000/services/deluge/torrents
```

## JDownloader Service (Coming Soon)

The JDownloader service is planned for future implementation. It will provide:

- Start/stop JDownloader daemon
- Add download links
- Manage download queue
- Browser integration support

## MEGA Service (Coming Soon)

The MEGA service is planned for future implementation. It will provide:

- Upload/download files from MEGA
- File and folder management
- Account quota monitoring
- Integration with other services

## Dependencies

For Deluge service:
```bash
pip install deluge-client
```

### Automatic Installation

The Deluge service includes automatic installation functionality. When starting the Deluge service, it will:

1. Check if `deluged` is available on the system
2. If not found, automatically install Deluge using:
   - `apt-get` (for Linux systems): Installs `deluge`, `deluged`, `deluge-web`, `deluge-console`, `python3-libtorrent`
   - `pip` as fallback: Installs `deluge` package

This ensures Deluge is available without manual installation steps.

### Manual Installation (Alternative)

If automatic installation fails, you can manually install Deluge:

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install -y deluge deluged deluge-web deluge-console python3-libtorrent
```

**Python only:**
```bash
pip install deluge deluge-client
```

For JDownloader service (future):
```bash
pip install jdownloader-api
```

For MEGA service (future):
```bash
pip install mega.py
```

## Configuration Management

### View Configuration
```bash
curl -H "X-API-Key: your-api-key" \
  http://localhost:5000/services/config
```

### Update Configuration
```bash
curl -X POST -H "X-API-Key: your-api-key" \
  -H "Content-Type: application/json" \
  -d '{"service_name": "deluge", "config": {"max_download_speed": 1000}}' \
  http://localhost:5000/services/config
```

## Error Handling

All API endpoints return JSON responses with the following structure:

```json
{
  "success": true/false,
  "message": "Optional message",
  "error": "Error description (if success=false)",
  "result": "Service-specific result data"
}
```

## Security

- All service endpoints require API key authentication
- Input validation is performed on all endpoints
- Service configuration is validated before application
- Process management includes proper cleanup and error handling

## Troubleshooting

### Deluge Service Not Starting
1. Check if Deluge is installed: `deluged --version`
2. Verify configuration in `~/.moccha/services_config.json`
3. Check logs: `tail -f /tmp/moccha.log`

### Torrent Not Adding
1. Verify Deluge daemon is running
2. Check torrent URL/file path
3. Verify download path exists and is writable

### Permission Issues
1. Ensure Moccha has permission to access download directories
2. Check if Deluge daemon has proper permissions
3. Verify API key is correct

## Future Enhancements

- Webhook support for download completion notifications
- Rate limiting for API endpoints
- Service health monitoring and auto-restart
- Dashboard for service management
- Integration with other download managers