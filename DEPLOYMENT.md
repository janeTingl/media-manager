# Media Manager v0.1.0 Deployment Guide

This guide covers various deployment options for Media Manager v0.1.0.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation Methods](#installation-methods)
3. [Docker Deployment](#docker-deployment)
4. [System Integration](#system-integration)
5. [Configuration](#configuration)
6. [Troubleshooting](#troubleshooting)
7. [Production Considerations](#production-considerations)

## Prerequisites

### System Requirements

- **Operating System**: Linux, macOS, or Windows
- **Python**: 3.8 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended for large libraries)
- **Storage**: 500MB for application + space for media files
- **Display**: Graphical display server (X11/Wayland on Linux)

### Dependencies

- **PySide6**: Qt6 GUI framework (automatically installed)
- **Python packages**: All dependencies listed in `pyproject.toml`

### Optional Dependencies

- **Docker**: For containerized deployment
- **X11 Server**: Required for GUI on headless systems

## Installation Methods

### Method 1: PyPI Installation (Recommended)

```bash
# Install from PyPI
pip install media-manager

# Or install with development dependencies
pip install "media-manager[dev]"

# Verify installation
python -c "import media_manager; print(media_manager.__version__)"
```

### Method 2: Source Installation

```bash
# Clone the repository
git clone https://github.com/your-org/media-manager.git
cd media-manager

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install in development mode
pip install -e ".[dev]"

# Run tests to verify
pytest
```

### Method 3: Using the Installation Script

```bash
# Download and run the installation script
curl -fsSL https://raw.githubusercontent.com/your-org/media-manager/v0.1.0/install.sh | bash
```

## Docker Deployment

### Quick Start

```bash
# Using Docker Compose (recommended)
git clone https://github.com/your-org/media-manager.git
cd media-manager
docker-compose up -d

# Or using Docker directly
docker build -t media-manager:0.1.0 .
docker run -d \
  --name media-manager \
  -e DISPLAY=:99 \
  -v $(pwd)/media:/media:ro \
  -v $(pwd)/config:/config \
  media-manager:0.1.0
```

### Docker Configuration

#### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DISPLAY` | `:99` | X11 display server |
| `MEDIA_MANAGER_MEDIA_DIR` | `/media` | Media files directory |
| `MEDIA_MANAGER_CONFIG_DIR` | `/config` | Configuration directory |

#### Volume Mounts

- `/media`: Your media library (read-only recommended)
- `/config`: Persistent configuration and settings
- `/tmp/.X11-unix`: X11 socket (for local display)

#### Docker Compose Customization

```yaml
version: '3.8'

services:
  media-manager:
    build: .
    container_name: media-manager
    restart: unless-stopped
    environment:
      - DISPLAY=:99
      - MEDIA_MANAGER_MEDIA_DIR=/media
      - MEDIA_MANAGER_CONFIG_DIR=/config
    volumes:
      - /path/to/your/media:/media:ro
      - ./config:/config
      - /tmp/.X11-unix:/tmp/.X11-unix:rw
    ports:
      - "8080:8080"  # Future web interface
    networks:
      - media-network

networks:
  media-network:
    driver: bridge
```

## System Integration

### Linux

#### Desktop Integration

```bash
# Create desktop entry
cat > ~/.local/share/applications/media-manager.desktop << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=Media Manager
Comment=A modern media management application
Exec=media-manager-demo
Icon=media-manager
Terminal=false
Categories=AudioVideo;Video;
EOF

# Update desktop database
update-desktop-database ~/.local/share/applications/
```

#### Systemd Service (Headless)

```ini
# /etc/systemd/system/media-manager.service
[Unit]
Description=Media Manager
After=graphical-session.target

[Service]
Type=simple
User=media-manager
Environment=DISPLAY=:1
ExecStart=/usr/local/bin/media-manager-demo
Restart=on-failure
RestartSec=5

[Install]
WantedBy=graphical-session.target
```

Enable and start:
```bash
sudo systemctl enable media-manager
sudo systemctl start media-manager
```

### macOS

#### Homebrew Installation

```bash
# Create Homebrew formula
cat > media-manager.rb << 'EOF'
class MediaManager < Formula
  desc "A modern media management application"
  homepage "https://github.com/your-org/media-manager"
  url "https://pypi.org/packages/source/m/media-manager/media-manager-0.1.0.tar.gz"
  sha256 "..."  # Add actual SHA256
  
  depends_on "python@3.11"
  
  def install
    system "python3", "-m", "pip", "install", *std_pip_args(build_isolation: true), "."
  end
  
  test do
    system "python3", "-c", "import media_manager; print(media_manager.__version__)"
  end
end
EOF

# Install
brew install media-manager.rb
```

### Windows

#### PowerShell Installation Script

```powershell
# install-media-manager.ps1
param(
    [string]$InstallPath = "$env:LOCALAPPDATA\MediaManager"
)

Write-Host "Installing Media Manager to $InstallPath"

# Create directory
New-Item -ItemType Directory -Path $InstallPath -Force

# Download and install
Invoke-WebRequest -Uri "https://pypi.org/pypi/media-manager/0.1.0/json" -OutFile "package-info.json"
# Extract download URL and download package

# Create shortcut
$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("$env:PUBLIC\Desktop\Media Manager.lnk")
$Shortcut.TargetPath = "$InstallPath\Scripts\media-manager-demo.exe"
$Shortcut.Save()

Write-Host "Installation complete!"
```

## Configuration

### Default Configuration Files

- **Linux**: `~/.config/media-manager/settings.json`
- **macOS**: `~/Library/Application Support/Media Manager/settings.json`
- **Windows**: `%APPDATA%\Media Manager\settings.json`

### Environment Variables

| Variable | Description |
|----------|-------------|
| `MEDIA_MANAGER_CONFIG_DIR` | Override configuration directory |
| `MEDIA_MANAGER_LOG_LEVEL` | Set logging level (DEBUG, INFO, WARNING, ERROR) |
| `MEDIA_MANAGER_MEDIA_DIR` | Default media directory |

### Configuration Example

```json
{
  "scan_paths": ["/media/movies", "/media/tv"],
  "target_folder": "/media/organized",
  "poster_settings": {
    "auto_download": true,
    "enabled_types": ["poster", "fanart"],
    "cache_dir": "~/.media-manager/poster-cache"
  },
  "subtitle_settings": {
    "enabled_languages": ["EN", "ES", "FR"],
    "auto_download": false,
    "format": "srt"
  },
  "nfo_settings": {
    "enabled": true,
    "target_subfolder": ""
  }
}
```

## Troubleshooting

### Common Issues

#### 1. GUI Not Displaying on Linux

```bash
# Check display server
echo $DISPLAY

# For headless systems, use Xvfb
Xvfb :99 -screen 0 1024x768x24 &
export DISPLAY=:99
media-manager-demo
```

#### 2. Permission Errors

```bash
# Ensure proper permissions for media directories
chmod -R 755 /path/to/media
chown -R $USER:$USER /path/to/media
```

#### 3. Missing Dependencies

```bash
# On Ubuntu/Debian
sudo apt update
sudo apt install python3-pip python3-venv libgl1-mesa-glx

# On CentOS/RHEL
sudo yum install python3-pip python3-venv mesa-libGL
```

#### 4. Docker Issues

```bash
# Check container logs
docker logs media-manager

# Run with interactive terminal for debugging
docker run -it --rm media-manager:0.1.0 /bin/bash
```

### Performance Optimization

#### Large Libraries

1. **Increase Memory**: Allocate more RAM to the application
2. **SSD Storage**: Use SSD for media files and cache
3. **Background Scanning**: Use batch processing for large libraries
4. **Database Optimization**: Future versions will include database backend

#### Network Storage

1. **Local Cache**: Enable local caching for posters and subtitles
2. **Timeout Settings**: Increase network timeouts
3. **Concurrent Operations**: Limit concurrent file operations

### Log Analysis

Logs are located at:
- **Linux**: `~/.local/share/media-manager/logs/`
- **macOS**: `~/Library/Logs/Media Manager/`
- **Windows**: `%LOCALAPPDATA%\Media Manager\logs\`

Key log files:
- `app.log`: Main application log
- `scan.log`: Scanning operations
- `download.log`: Poster and subtitle downloads

## Production Considerations

### Security

1. **File Permissions**: Ensure proper permissions on media files
2. **Network Access**: Configure firewall rules for API access
3. **User Isolation**: Run with limited user privileges
4. **Input Validation**: Validate file paths and user inputs

### Backup and Recovery

1. **Configuration Backup**: Regularly backup `settings.json`
2. **Media Metadata**: Export NFO files for metadata backup
3. **Cache Management**: Implement cache cleanup policies
4. **Disaster Recovery**: Document restore procedures

### Monitoring

1. **Application Logs**: Monitor error logs and warnings
2. **Performance Metrics**: Track memory usage and scan times
3. **Storage Monitoring**: Monitor disk space for cache and logs
4. **Health Checks**: Implement application health monitoring

### Scaling

1. **Horizontal Scaling**: Multiple instances for different media types
2. **Load Balancing**: Distribute scanning operations
3. **Database Backend**: Plan for database integration (v0.2.0)
4. **API Services**: REST API for remote management (future)

### Maintenance

1. **Regular Updates**: Keep dependencies updated
2. **Cache Cleanup**: Periodic cache and log cleanup
3. **Security Patches**: Apply security updates promptly
4. **Performance Tuning**: Regular performance reviews

## Migration Guide

### From Alpha/Beta Versions

1. **Backup Settings**: Export current configuration
2. **Clean Install**: Fresh installation of v0.1.0
3. **Import Settings**: Restore configuration
4. **Re-scan Media**: Full library re-scan recommended

### Future Version Upgrades

1. **Check Changelog**: Review breaking changes
2. **Backup Data**: Export metadata and settings
3. **Test Migration**: Test in non-production environment
4. **Rollback Plan**: Prepare rollback procedures

## Support

### Documentation

- [Quick Start Guide](QUICK_START.md)
- [User Manual](USAGE.md)
- [API Reference](API.md)
- [Architecture Guide](ARCHITECTURE.md)

### Community

- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share experiences
- **Wiki**: Community-maintained documentation

### Professional Support

For enterprise deployments and professional support:
- Contact: support@media-manager.dev
- Documentation: https://docs.media-manager.dev
- Status Page: https://status.media-manager.dev

---

For additional help or questions, please refer to the [main documentation](README.md) or open an issue on GitHub.