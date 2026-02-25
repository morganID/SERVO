# Moccha

Moccha is a Python-based SSH tunneling application that provides secure, encrypted connections to remote servers. It's designed to be simple to use while offering powerful tunneling capabilities.

## Features

- **Secure SSH Tunneling**: Establish encrypted connections to remote servers
- **Daemon Mode**: Run as a background service for persistent connections
- **Command Line Interface**: Easy-to-use CLI for managing tunnels
- **Cross-Platform**: Works on any platform that supports Python

## Installation

### Prerequisites

- Python 3.6 or higher
- pip package manager

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Install Moccha

```bash
pip install .
```

## Usage

### Basic Usage

Start Moccha with the default configuration:

```bash
moccha
```

### Command Line Options

- `--daemon`: Run Moccha as a daemon
- `--config`: Specify a custom configuration file
- `--verbose`: Enable verbose logging
- `--help`: Show help message

### Examples

Start Moccha in daemon mode:

```bash
moccha --daemon
```

Start with a custom configuration:

```bash
moccha --config /path/to/config.yaml
```

## Configuration

Moccha uses a configuration file to define tunnel settings. The default configuration file is located at `~/.moccha/config.yaml`.

Example configuration:

```yaml
tunnels:
  - name: my-tunnel
    local_port: 8080
    remote_host: example.com
    remote_port: 22
    ssh_host: ssh.example.com
    ssh_port: 22
    ssh_user: username
    ssh_key: /path/to/private/key
```

## Development

### Running Tests

```bash
python -m pytest tests/
```

### Building Documentation

```bash
python -m sphinx docs/ docs/_build/
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for more information.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

If you encounter any issues or have questions, please [open an issue](https://github.com/morganID/moccha/issues) on our GitHub repository.