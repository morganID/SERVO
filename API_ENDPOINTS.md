# Moccha API Endpoints Documentation

## Overview

This document provides comprehensive documentation for all Moccha API endpoints, including service management, Deluge operations, and system management endpoints.

## Authentication

All endpoints require API key authentication via header:
```
X-API-Key: your-api-key
```

## Base URL

```
http://localhost:5000
```

## Service Management Endpoints

### List All Services
```
GET /services
```

**Description**: Get list of all available services.

**Response**:
```json
{
  "success": true,
  "services": ["deluge", "jdownloader", "mega"],
  "count": 3
}
```

### Get All Services Status
```
GET /services/status
```

**Description**: Get status of all services.

**Response**:
```json
{
  "success": true,
  "services": {
    "deluge": {
      "running": true,
      "host": "localhost",
      "port": 58846,
      "download_path": "/downloads/torrents",
      "connected": true,
      "stats": {
        "upload_rate": 0,
        "download_rate": 0,
        "dht_nodes": 0
      }
    }
  }
}
```

### Get Specific Service Status
```
GET /services/{service_name}/status
```

**Description**: Get status of a specific service.

**Parameters**:
- `service_name`: Name of the service (deluge, jdownloader, mega)

**Response**:
```json
{
  "running": true,
  "host": "localhost",
  "port": 58846,
  "download_path": "/downloads/torrents",
  "connected": true
}
```

### Start Service
```
POST /services/{service_name}/start
```

**Description**: Start a specific service.

**Parameters**:
- `service_name`: Name of the service

**Response**:
```json
{
  "success": true,
  "message": "Deluge daemon started successfully",
  "result": {
    "pid": 12345,
    "host": "localhost",
    "port": 58846
  }
}
```

### Stop Service
```
POST /services/{service_name}/stop
```

**Description**: Stop a specific service.

**Parameters**:
- `service_name`: Name of the service

**Response**:
```json
{
  "success": true,
  "message": "Deluge daemon stopped"
}
```

### Restart Service
```
POST /services/{service_name}/restart
```

**Description**: Restart a specific service.

**Parameters**:
- `service_name`: Name of the service

**Response**:
```json
{
  "success": true,
  "message": "Deluge daemon restarted",
  "result": {
    "pid": 12346,
    "host": "localhost",
    "port": 58846
  }
}
```

### Get All Services Configuration
```
GET /services/config
```

**Description**: Get configuration of all services.

**Response**:
```json
{
  "success": true,
  "config": {
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

### Get Specific Service Configuration
```
GET /services/config/{service_name}
```

**Description**: Get configuration of a specific service.

**Parameters**:
- `service_name`: Name of the service

**Response**:
```json
{
  "success": true,
  "service": "deluge",
  "config": {
    "enabled": true,
    "host": "localhost",
    "port": 58846,
    "download_path": "/downloads/torrents",
    "max_download_speed": 0,
    "max_upload_speed": 0,
    "auto_add_folder": "/torrents/watch"
  }
}
```

### Update Service Configuration
```
POST /services/config
```

**Description**: Update configuration for a service.

**Request Body**:
```json
{
  "service_name": "deluge",
  "config": {
    "max_download_speed": 1000,
    "download_path": "/new/downloads"
  }
}
```

**Response**:
```json
{
  "success": true,
  "message": "Configuration updated for deluge"
}
```

## Deluge Service Endpoints

### List All Torrents
```
GET /services/deluge/torrents
```

**Description**: Get list of all torrents in Deluge.

**Response**:
```json
{
  "success": true,
  "torrents": [
    {
      "id": "abc123...",
      "name": "example.torrent",
      "progress": 75.5,
      "state": "Downloading",
      "download_rate": 1024000,
      "upload_rate": 512000,
      "seeds": 15,
      "peers": 8,
      "total_wanted": 1000000000,
      "total_done": 755000000,
      "eta": 120,
      "ratio": 0.5
    }
  ],
  "count": 1
}
```

### Add Torrent
```
POST /services/deluge/torrents
```

**Description**: Add a torrent to Deluge.

**Request Body**:
```json
{
  "torrent_url": "magnet:?xt=urn:btih:example",
  "torrent_file": "/path/to/torrent/file.torrent"
}
```

**Note**: Use either `torrent_url` or `torrent_file`, not both.

**Response**:
```json
{
  "success": true,
  "message": "Torrent added successfully",
  "torrent_id": "abc123..."
}
```

### Get Torrent Details
```
GET /services/deluge/torrents/{torrent_id}
```

**Description**: Get detailed information about a specific torrent.

**Parameters**:
- `torrent_id`: Torrent hash/ID

**Response**:
```json
{
  "success": true,
  "torrent": {
    "id": "abc123...",
    "name": "example.torrent",
    "progress": 75.5,
    "state": "Downloading",
    "download_rate": 1024000,
    "upload_rate": 512000,
    "seeds": 15,
    "peers": 8,
    "total_wanted": 1000000000,
    "total_done": 755000000,
    "eta": 120,
    "ratio": 0.5,
    "files": [
      {
        "index": 0,
        "path": "file1.mp4",
        "size": 500000000,
        "offset": 0
      }
    ],
    "trackers": [
      {
        "url": "udp://tracker.example.com:80",
        "tier": 0
      }
    ],
    "peers": [
      {
        "peer_id": "peer123",
        "ip": "192.168.1.100",
        "progress": 0.8,
        "down_speed": 100000,
        "up_speed": 50000
      }
    ]
  }
}
```

### Pause Torrent
```
POST /services/deluge/torrents/{torrent_id}/pause
```

**Description**: Pause a specific torrent.

**Parameters**:
- `torrent_id`: Torrent hash/ID

**Response**:
```json
{
  "success": true,
  "message": "Torrent abc123... paused"
}
```

### Resume Torrent
```
POST /services/deluge/torrents/{torrent_id}/resume
```

**Description**: Resume a specific torrent.

**Parameters**:
- `torrent_id`: Torrent hash/ID

**Response**:
```json
{
  "success": true,
  "message": "Torrent abc123... resumed"
}
```

### Remove Torrent
```
POST /services/deluge/torrents/{torrent_id}/remove
```

**Description**: Remove a specific torrent.

**Parameters**:
- `torrent_id`: Torrent hash/ID

**Request Body**:
```json
{
  "remove_data": false
}
```

**Response**:
```json
{
  "success": true,
  "message": "Torrent abc123... removed"
}
```

### Get Deluge Statistics
```
GET /services/deluge/stats
```

**Description**: Get Deluge daemon statistics.

**Response**:
```json
{
  "success": true,
  "stats": {
    "upload_rate": 1024000,
    "download_rate": 2048000,
    "dht_nodes": 150,
    "num_peers": 50,
    "num_connections": 100,
    "payload_upload_rate": 900000,
    "payload_download_rate": 1800000
  }
}
```

### Get Torrent Peers
```
GET /services/deluge/peers/{torrent_id}
```

**Description**: Get peer information for a specific torrent.

**Parameters**:
- `torrent_id`: Torrent hash/ID

**Response**:
```json
{
  "success": true,
  "peers": [
    {
      "peer_id": "peer123",
      "ip": "192.168.1.100",
      "progress": 0.8,
      "down_speed": 100000,
      "up_speed": 50000,
      "client": "qBittorrent"
    }
  ],
  "count": 1
}
```

## System Management Endpoints

### Get Server Status
```
GET /status
```

**Description**: Get server status and system information.

**Response**:
```json
{
  "uptime": "0:30:45.123456",
  "cpu_pct": 25.5,
  "cpu_count": 4,
  "ram_total_gb": 15.6,
  "ram_used_gb": 8.2,
  "ram_pct": 52.6,
  "disk_total_gb": 500.0,
  "disk_free_gb": 300.0,
  "gpu": {
    "name": "NVIDIA GeForce RTX 3080",
    "mem_used_mb": 2048,
    "mem_total_mb": 10240,
    "util_pct": 45
  },
  "executions": 150,
  "variables": 10
}
```

### Execute Python Code
```
POST /execute
```

**Description**: Execute Python code on the server.

**Request Body**:
```json
{
  "code": "print('Hello World')\nresult = 2 + 2"
}
```

**Response**:
```json
{
  "output": "Hello World\n",
  "error": "",
  "variables": {
    "result": 4
  },
  "success": true
}
```

### Execute Shell Command
```
POST /shell
```

**Description**: Execute shell command on the server.

**Request Body**:
```json
{
  "command": "ls -la",
  "timeout": 30
}
```

**Response**:
```json
{
  "stdout": "total 24\n-rw-r--r-- 1 user user  1234 Jan 1 12:00 file1.txt\n...",
  "stderr": "",
  "code": 0,
  "success": true
}
```

### Install Python Package
```
POST /install
```

**Description**: Install Python package using pip.

**Request Body**:
```json
{
  "package": "requests"
}
```

**Response**:
```json
{
  "package": "requests",
  "success": true,
  "output": "Collecting requests...",
  "error": ""
}
```

### List Files
```
GET /files?path=/path/to/directory
```

**Description**: List files in a directory.

**Parameters**:
- `path`: Directory path (optional, defaults to workspace)

**Response**:
```json
{
  "path": "/content",
  "items": [
    {
      "name": "file1.txt",
      "type": "file",
      "size": 1024,
      "modified": "2023-01-01T12:00:00"
    },
    {
      "name": "directory1",
      "type": "dir",
      "size": 4096,
      "modified": "2023-01-01T12:00:00"
    }
  ]
}
```

### Upload File
```
POST /upload
```

**Description**: Upload file to server.

**Form Data**:
- `file`: File to upload
- `path`: Destination directory (optional)

**Response**:
```json
{
  "filename": "uploaded_file.txt",
  "path": "/content/uploaded_file.txt",
  "size": 1024,
  "success": true
}
```

### Download File
```
GET /download/{filepath}
```

**Description**: Download file from server.

**Parameters**:
- `filepath`: Path to file

**Response**: File download (binary)

### Execute Async Code
```
POST /async-execute
```

**Description**: Execute code asynchronously.

**Request Body**:
```json
{
  "code": "import time\ntime.sleep(10)\nprint('Done')"
}
```

**Response**:
```json
{
  "task_id": "abc123",
  "status": "running"
}
```

### Get Async Task Status
```
GET /task/{task_id}
```

**Description**: Get status of async task.

**Parameters**:
- `task_id`: Task ID from async-execute

**Response**:
```json
{
  "status": "done",
  "result": "Done\n",
  "created": "2023-01-01T12:00:00",
  "finished": "2023-01-01T12:00:10"
}
```

### Get Variables
```
GET /variables
```

**Description**: Get all persistent variables.

**Response**:
```json
{
  "variable1": "value1",
  "variable2": 42,
  "variable3": [1, 2, 3]
}
```

### Delete Variable
```
DELETE /variables/{variable_name}
```

**Description**: Delete a persistent variable.

**Parameters**:
- `variable_name`: Name of variable to delete

**Response**:
```json
{
  "deleted": "variable1"
}
```

### Get Execution History
```
GET /history?limit=50
```

**Description**: Get execution history.

**Parameters**:
- `limit`: Number of entries to return (optional, default: 20)

**Response**:
```json
[
  {
    "id": "abc123",
    "type": "execute",
    "time": "2023-01-01T12:00:00",
    "input": "print('Hello')",
    "success": true
  }
]
```

## Error Handling

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": "Error description",
  "message": "Optional additional message"
}
```

## Rate Limiting

- System endpoints: 100 requests/minute
- Service endpoints: 60 requests/minute
- Deluge endpoints: 30 requests/minute

## Examples

### Complete Deluge Workflow
```bash
# 1. Start Deluge service
curl -X POST -H "X-API-Key: your-key" \
  http://localhost:5000/services/deluge/start

# 2. Add torrent
curl -X POST -H "X-API-Key: your-key" \
  -H "Content-Type: application/json" \
  -d '{"torrent_url": "magnet:?xt=urn:btih:example"}' \
  http://localhost:5000/services/deluge/torrents

# 3. Monitor progress
curl -H "X-API-Key: your-key" \
  http://localhost:5000/services/deluge/torrents

# 4. Get detailed info
curl -H "X-API-Key: your-key" \
  http://localhost:5000/services/deluge/torrents/abc123...

# 5. Pause torrent
curl -X POST -H "X-API-Key: your-key" \
  http://localhost:5000/services/deluge/torrents/abc123.../pause
```

### Service Management
```bash
# Check all services
curl -H "X-API-Key: your-key" \
  http://localhost:5000/services/status

# Start multiple services
curl -X POST -H "X-API-Key: your-key" \
  http://localhost:5000/services/deluge/start

curl -X POST -H "X-API-Key: your-key" \
  http://localhost:5000/services/jdownloader/start