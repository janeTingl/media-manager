# Media Manager - Windows Executable

![Version](https://img.shields.io/badge/version-0.1.0-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows-lightgrey.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Media Manager is a comprehensive media organization tool that helps you scan, organize, and manage your media files with automatic metadata matching, poster downloading, subtitle management, and NFO file generation.

## 🚀 Quick Start

### Option 1: Portable Version (Recommended)

1. **Download** `media-manager-portable-0.1.0.zip`
2. **Extract** to any folder (e.g., `C:\MediaManager`)
3. **Run** `media-manager.exe` or `start.bat`

No installation required! The application creates all necessary files in your user profile.

### Option 2: Installer Version

1. **Download** `media-manager-installer-0.1.0.zip`
2. **Extract** to a temporary location
3. **Right-click** `install.bat` and "Run as administrator"
4. **Launch** from Start Menu or Desktop shortcut

## 📋 System Requirements

- **Windows 7** or higher
- **64-bit operating system**
- **500MB** free disk space
- **.NET Framework 4.5** or higher (usually pre-installed)

## ✨ Features

### 🎬 Media Scanning
- Intelligent file detection for movies and TV shows
- Support for all major video formats (MKV, MP4, AVI, etc.)
- Recursive directory scanning
- Customizable scan configurations

### 🔍 Automatic Matching
- Automatic metadata matching using multiple data sources
- Confidence scoring for match accuracy
- Manual search override functionality
- Support for movies and TV episodes

### 🖼️ Poster Management
- Automatic poster downloading
- Multiple poster types (poster, fanart, banner)
- Size selection and caching
- Intelligent duplicate prevention

### 📝 Subtitle Support
- Multi-language subtitle downloading
- Format support (SRT, ASS, VTT, etc.)
- Automatic subtitle placement
- Provider abstraction system

### 📄 NFO Export
- Standard NFO file generation
- Movie and TV episode schemas
- UTF-8 encoding with full Unicode support
- Custom output configuration

### 🎯 User Interface
- Modern Qt-based interface
- Non-blocking background operations
- Progress tracking and status updates
- Filter and search functionality

## 📖 Usage Guide

### First Launch

1. **Start the application** using your preferred method
2. **Welcome screen** appears with basic instructions
3. **Configure preferences** in Edit → Preferences
4. **Start scanning** your media directories

### Basic Workflow

1. **Scan Media**
   - Click "Scan Directory" in the toolbar
   - Select a folder containing video files
   - Wait for scanning to complete

2. **Review Results**
   - Switch to the "Matching" tab
   - Review detected media files
   - Use filters to find specific items

3. **Start Matching**
   - Click "Start Matching" to find automatic matches
   - Monitor progress in the status bar
   - Review confidence scores

4. **Resolve Matches**
   - Select items to review detailed information
   - Accept matches, skip items, or search manually
   - Use "Manual Search" for custom results

5. **Download Extras**
   - Enable automatic poster downloading in preferences
   - Configure subtitle languages
   - Generate NFO files for media centers

### Advanced Features

#### Custom Scanning
- **File patterns**: Configure regex patterns for file detection
- **Exclude patterns**: Skip unwanted files or directories
- **Deep scanning**: Enable recursive directory traversal

#### Matching Configuration
- **Confidence thresholds**: Set minimum confidence for auto-accept
- **Provider selection**: Choose metadata sources
- **Manual override**: Force specific matches

#### Media Processing
- **Library organization**: Rename and move files automatically
- **NFO generation**: Create metadata files for Kodi/Plex
- **Batch operations**: Process multiple items simultaneously

## ⚙️ Configuration

### Preferences Location
- **Portable**: `%APPDATA%\Media Manager\preferences.json`
- **Installed**: `%APPDATA%\Media Manager\preferences.json`

### Key Settings

#### General
- **Default scan directory**: Starting location for scans
- **Auto-refresh**: Automatic UI updates
- **Theme**: Interface appearance

#### Matching
- **Auto-accept threshold**: Minimum confidence for automatic matching
- **Provider priority**: Order of metadata sources
- **Manual review**: Require confirmation for matches

#### Posters
- **Auto-download**: Automatically download posters
- **Preferred sizes**: Select image quality
- **Cache location**: Local storage for downloaded images

#### Subtitles
- **Preferred languages**: Language priority order
- **Auto-download**: Get subtitles automatically
- **Format preference**: SRT, ASS, VTT, etc.

#### NFO Export
- **Enabled**: Generate NFO files
- **Target location**: Output directory
- **Custom templates**: Customize NFO format

## 🔧 Troubleshooting

### Common Issues

#### Application Won't Start
**Symptoms**: Double-clicking does nothing or error message appears

**Solutions**:
1. **Check .NET Framework**: Ensure .NET Framework 4.5+ is installed
2. **Run as Administrator**: Right-click and "Run as administrator"
3. **Antivirus**: Add to antivirus exclusions
4. **Windows Update**: Install latest Windows updates

#### Scanning Issues
**Symptoms**: No files found or scanning stops

**Solutions**:
1. **Check permissions**: Ensure read access to directories
2. **File formats**: Verify video files are supported
3. **Network drives**: Try local directories first
4. **Large libraries**: Increase timeout in preferences

#### Matching Problems
**Symptoms**: No matches found or incorrect results

**Solutions**:
1. **Internet connection**: Check network connectivity
2. **Filename format**: Use standard naming conventions
3. **Manual search**: Override automatic matching
4. **Provider status**: Check if metadata services are available

#### Download Failures
**Symptoms**: Posters or subtitles not downloading

**Solutions**:
1. **Firewall**: Allow application through firewall
2. **Disk space**: Ensure sufficient storage
3. **Cache location**: Check write permissions
4. **Retry settings**: Increase retry count in preferences

### Debug Mode

For advanced troubleshooting, you can run the development build:
1. Download the source code
2. Install Python dependencies
3. Run `python build_windows.py --backend pyinstaller --skip-dependency-install --skip-packages --skip-tests`

### Log Files

Application logs are stored in:
- **Windows**: `%USERPROFILE%\.media-manager\logs\`
- **Files**: `app.log`, `demo.log`, `error.log`

### Getting Help

1. **Check logs**: Review error messages in log files
2. **Documentation**: Read the full user guide
3. **Community**: Visit the project forums
4. **Issues**: Report bugs on the project repository

## 📁 File Locations

### Application Files
- **Portable**: Extracted location
- **Installed**: `C:\Program Files\Media Manager\`

### User Data
- **Configuration**: `%USERPROFILE%\.media-manager\`
- **Cache**: `%USERPROFILE%\.media-manager\cache\`
- **Logs**: `%USERPROFILE%\.media-manager\logs\`
- **Settings**: `%APPDATA%\Media Manager\`

### Temporary Files
- **Extraction**: `%TEMP%\_MEIxxxxx\` (during runtime)
- **Downloads**: `%USERPROFILE%\.media-manager\downloads\`

## 🔒 Security

### File Integrity
Verify downloaded files using the SHA-256 hashes provided in `RELEASE_INFO.txt`:
```cmd
certutil -hashfile media-manager.exe SHA256
```

### Privacy
- **No telemetry**: The application does not collect personal data
- **Local processing**: All operations are performed locally
- **No internet tracking**: No analytics or tracking software

### Antivirus
If your antivirus flags the application:
1. **False positive**: Windows executables are sometimes flagged
2. **Add exclusion**: Add to antivirus safe list
3. **Verify integrity**: Check file hashes
4. **Report issue**: Notify antivirus vendor

## 📚 Documentation

### User Documentation
- **Quick Start Guide**: Basic setup and first use
- **User Manual**: Complete feature documentation
- **Troubleshooting**: Common issues and solutions
- **FAQ**: Frequently asked questions

### Developer Documentation
- **API Reference**: Technical documentation
- **Architecture**: System design and patterns
- **Contributing**: Development guidelines
- **Source Code**: Available on project repository

## 🆕 Version History

### v0.1.0 (Current)
- Initial Windows executable release
- Complete media management functionality
- Portable and installer packages
- Comprehensive documentation

### Upcoming Features
- Automatic updates
- Plugin system
- Cloud storage integration
- Advanced filtering options

## 📄 License

Media Manager is released under the MIT License. See the LICENSE file for details.

## 🤝 Contributing

We welcome contributions! Please see the CONTRIBUTING.md file for guidelines on:
- Bug reports
- Feature requests
- Code contributions
- Documentation improvements

## 📞 Support

### Getting Help
1. **Documentation**: Check included guides and manuals
2. **Community**: Join our user forums
3. **Issues**: Report bugs on GitHub
4. **Email**: Contact support team

### Reporting Issues
When reporting issues, please include:
- **Windows version**: e.g., Windows 10 64-bit
- **Application version**: v0.1.0
- **Error messages**: Full text of any error dialogs
- **Steps to reproduce**: Detailed reproduction steps
- **Log files**: Relevant log file excerpts

---

**Thank you for using Media Manager!** 

We hope this application helps you organize and enjoy your media collection. If you find the software useful, please consider rating it or contributing to the project.