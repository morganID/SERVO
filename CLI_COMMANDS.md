# Moccha CLI Commands Documentation

## Overview

This document provides comprehensive documentation for all Moccha CLI commands, including service management, Deluge operations, and system management commands.

## Basic Usage

```bash
moccha [command] [options]
```

## System Commands

### Start Moccha Server
```bash
moccha start --token=<ngrok-token> [options]
```

**Options**:
- `--port <port>`: Port to run server on (default: 5000)
- `--token <token>`: Ngrok authentication token (required)
- `--key <key>`: API key (optional, auto-generated if not provided)
- `--workspace <path>`: Workspace directory (default: /content)

**Example**:
```bash
moccha start --token=1234567890abcdef --port=8080 --workspace=/my/workspace
```

### Stop Moccha Server
```bash
moccha stop
```

**Description**: Stops the running Moccha server daemon.

### Check Server Status
```bash
moccha status
```

**Description**: Shows current server status.

**Output**:
```
🟢 RUNNING (PID: 12345)
   URL: https://example.ngrok.io
   Key: your-api-key
```

### Get Server Information
```bash
moccha info
```

**Description**: Displays detailed server information.

**Output**:
```
=======================================================
  ✅ SERVER INFO
=======================================================
  🌍 URL : https://example.ngrok.io
  🔑 Key : your-api-key
  📍 Port: 5000
  📂 PID : 12345
=======================================================

  📋 Test:
  curl -H "X-API-Key: your-api-key" https://example.ngrok.io/status
```

### Restart Server
```bash
moccha restart --token=<ngrok-token> [options]
```

**Options**: Same as `start` command

**Description**: Stops and restarts the server with new configuration.

## Service Management Commands

### List Available Services
```bash
moccha services
```

**Description**: Lists all available services.

**Output**:
```
Available services:
  - deluge
  - jdownloader
  - mega
```

### Check Services Status
```bash
moccha services-status
```

**Description**: Shows status of all services.

**Output**:
```
Service status:
  ✅ deluge: Running
  ❌ jdownloader: Not running
  ❌ mega: Not running
```

### Start Service
```bash
moccha service-start <service-name>
```

**Description**: Starts a specific service.

**Example**:
```bash
moccha service-start deluge
```

**Output**:
```
✅ deluge started successfully
```

### Stop Service
```bash
moccha service-stop <service-name>
```

**Description**: Stops a specific service.

**Example**:
```bash
moccha service-stop deluge
```

**Output**:
```
✅ deluge stopped successfully
```

### Restart Service
```bash
moccha service-restart <service-name>
```

**Description**: Restarts a specific service.

**Example**:
```bash
moccha service-restart deluge
```

**Output**:
```
✅ deluge restarted successfully
```

## Deluge Commands

### Add Torrent
```bash
moccha deluge-add <torrent-url>
```

**Description**: Adds a torrent to Deluge using magnet URL or direct link.

**Example**:
```bash
moccha deluge-add "magnet:?xt=urn:btih:example"
```

**Output**:
```
✅ Torrent added successfully: abc123def456...
```

### List Torrents
```bash
moccha deluge-list
```

**Description**: Lists all torrents in Deluge.

**Output**:
```
Found 2 torrents:
  - Ubuntu 20.04 ISO (75.5%) - Downloading
  - Python Tutorial (100.0%) - Seeding
```

## Configuration

### Service Configuration File

Services are configured via JSON file at `~/.moccha/services_config.json`:

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
    },
    "jdownloader": {
      "enabled": true,
      "host": "localhost",
      "port": 3129,
      "download_path": "/downloads/jdownloader"
    },
    "mega": {
      "enabled": true,
      "email": "user@example.com",
      "password": "password",
      "download_path": "/downloads/mega"
    }
  }
}
```

### Creating Configuration Directory
```bash
mkdir -p ~/.moccha
```

### Example Deluge Configuration
```json
{
  "services": {
    "deluge": {
      "enabled": true,
      "host": "localhost",
      "port": 58846,
      "download_path": "/home/user/downloads/torrents",
      "max_download_speed": 1000,
      "max_upload_speed": 500,
      "auto_add_folder": "/home/user/torrents/watch"
    }
  }
}
```

## Advanced Usage

### Running Multiple Services
```bash
# Start all services
moccha service-start deluge
moccha service-start jdownloader
moccha service-start mega

# Check status
moccha services-status
```

### Service Dependencies
Some services may have dependencies:
- Deluge requires `deluged` daemon (installed automatically)
- JDownloader requires Java runtime
- MEGA requires network access

### Troubleshooting

#### Service Won't Start
```bash
# Check if service is enabled in config
cat ~/.moccha/services_config.json

# Check logs
tail -f /tmp/moccha.log

# Verify dependencies
which deluged  # For Deluge
java -version  # For JDownloader
```

#### Permission Issues
```bash
# Ensure download directories exist and are writable
mkdir -p /downloads/torrents
chmod 755 /downloads/torrents
```

#### Port Conflicts
```bash
# Check if port is in use
netstat -tlnp | grep :58846

# Change port in configuration
# Edit ~/.moccha/services_config.json
```

## Command Reference Table

| Command | Description | Example |
|---------|-------------|---------|
| `moccha start` | Start Moccha server | `moccha start --token=abc123` |
| `moccha stop` | Stop Moccha server | `moccha stop` |
| `moccha status` | Check server status | `moccha status` |
| `moccha info` | Get server info | `moccha info` |
| `moccha restart` | Restart server | `moccha restart --token=abc123` |
| `moccha services` | List available services | `moccha services` |
| `moccha services-status` | Check services status | `moccha services-status` |
| `moccha service-start <name>` | Start service | `moccha service-start deluge` |
| `moccha service-stop <name>` | Stop service | `moccha service-stop deluge` |
| `moccha service-restart <name>` | Restart service | `moccha service-restart deluge` |
| `moccha deluge-add <url>` | Add torrent | `moccha deluge-add "magnet:..."` |
| `moccha deluge-list` | List torrents | `moccha deluge-list` |

## Environment Variables

### Ngrok Token
Instead of passing token via command line, you can set environment variable:
```bash
export NGROK_TOKEN=your-token-here
moccha start
```

### API Key
Set custom API key:
```bash
export MOCHA_API_KEY=your-custom-key
moccha start
```

### Workspace Directory
Set default workspace:
```bash
export MOCHA_WORKSPACE=/path/to/workspace
moccha start
```

## Integration Examples

### With Shell Scripts
```bash
#!/bin/bash
# Start Moccha with Deluge
moccha start --token=$NGROK_TOKEN &
sleep 5
moccha service-start deluge
echo "Moccha with Deluge is running!"
```

### With Cron Jobs
```bash
# Add to crontab to auto-start on boot
@reboot /usr/local/bin/moccha start --token=your-token
```

### With Docker
```bash
docker run -d \
  -p 5000:5000 \
  -e NGROK_TOKEN=your-token \
  -v ~/.moccha:/root/.moccha \
  your-moccha-image
```

## Error Codes and Messages

### Common Errors

| Error | Description | Solution |
|-------|-------------|----------|
| "Service not found" | Service not enabled in config | Enable service in config file |
| "Failed to connect" | Service daemon not running | Start service daemon |
| "Permission denied" | Insufficient permissions | Check file/directory permissions |
| "Port in use" | Port already occupied | Change port in configuration |
| "Invalid API key" | Wrong API key | Use correct API key from `moccha info` |

### Debug Mode
For detailed debugging, check the log file:
```bash
tail -f /tmp/moccha.log
```

## Best Practices

1. **Security**: Never share your API key publicly
2. **Configuration**: Keep configuration files backed up
3. **Monitoring**: Regularly check service status
4. **Updates**: Keep Moccha and services updated
5. **Logs**: Monitor logs for errors and issues

## Support

For additional help:
- Check the API documentation: `API_ENDPOINTS.md`
- Review service-specific documentation: `README_SERVICES.md`
- Check logs: `/tmp/moccha.log`
- Report issues on GitHub repository