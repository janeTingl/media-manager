# Creating GitHub Release v0.1.0

This document provides step-by-step instructions for publishing Media Manager v0.1.0 on GitHub Releases.

## Prerequisites

1. ✅ Repository: `https://github.com/your-org/media-manager`
2. ✅ Branch: `release-v0.1.0-upload-media-manager-exe-e01`
3. ✅ All changes committed and pushed
4. ✅ GitHub account with repository access

## Step 1: Prepare Release Assets

### Executables to Include

#### Windows
- **File**: `media-manager.exe` (59 MB)
- **Description**: Windows 7+ (x64) portable executable
- **How to build**: See [releases/v0.1.0/BUILD_WINDOWS.md](releases/v0.1.0/BUILD_WINDOWS.md)
- **Status**: Ready to build on Windows machine

#### macOS (Optional for v0.1.0)
- **File**: `media-manager-macos-universal.dmg`
- **Platforms**: Intel (x86_64) and Apple Silicon (ARM64)
- **Status**: To be built on macOS

#### Linux (Optional for v0.1.0)
- **File**: `media-manager-linux-x64` 
- **Platform**: 64-bit GNU/Linux
- **Status**: Available in repository (releases/v0.1.0/)

### Download Files to Have Ready

```
media-manager.exe              # Windows executable
media-manager-linux-x64        # Linux executable (in repo)
GITHUB_RELEASE_NOTES_v0.1.0.md # Release notes content
```

## Step 2: Create Tag on GitHub

### Using GitHub Web Interface

1. Go to [Releases page](https://github.com/your-org/media-manager/releases)
2. Click "Create a new release"
3. Enter:
   - **Tag**: `v0.1.0`
   - **Target**: `release-v0.1.0-upload-media-manager-exe-e01` branch
   - **Title**: `Media Manager v0.1.0 - MVP Release`

### Using Git Command Line

```bash
# Tag the current commit
git tag -a v0.1.0 -m "Media Manager v0.1.0 MVP Release"

# Push tag to GitHub
git push origin v0.1.0
```

## Step 3: Upload Release Assets

### File Details

#### media-manager.exe (Windows)
- **Platform**: Windows 7+, 64-bit
- **Size**: ~59 MB
- **Type**: Single executable file
- **Installation**: Direct run, no installation needed
- **System Requirements**: .NET Framework 4.5+ (pre-installed on most Windows)

#### media-manager-linux-x64 (Linux)
- **Platform**: Linux x86_64
- **Size**: ~59 MB
- **Type**: ELF binary executable
- **Installation**: Run directly or copy to PATH
- **System Requirements**: glibc 2.17+, Qt6 libraries

### Upload Steps

1. **On Release Page**:
   - Click "Attach binaries" or "Attach files" section
   - Or drag and drop files

2. **For Each Executable**:
   - Upload file
   - Set display name
   - Verify file size and integrity

3. **Checksum Information** (optional but recommended):
   - Calculate SHA-256: `sha256sum filename`
   - Include in release notes

## Step 4: Write Release Notes

### Copy from Template

Use content from [GITHUB_RELEASE_NOTES_v0.1.0.md](GITHUB_RELEASE_NOTES_v0.1.0.md)

Key sections to include:

1. **Headline**: "🎉 Initial MVP Release"

2. **Key Features**: 
   - Media scanning & detection
   - Media matching
   - Poster management
   - Subtitle support
   - NFO metadata export
   - Modern GUI

3. **Installation**:
   - Windows: Download and run .exe
   - Other platforms: Build from source or pip install

4. **System Requirements**:
   - Windows 7+, x64
   - 500 MB disk space
   - Optional internet for downloads

5. **Documentation Links**:
   - Quick Start Guide
   - Installation Guide
   - User Manual
   - API Reference

6. **Known Limitations**:
   - Mock data (real API in v0.2.0)
   - No database (JSON files)
   - Desktop application only

## Step 5: Publish Release

### Draft vs Published

1. **Save as Draft**: Keep working on release notes
2. **Publish Release**: Make public and notify followers
   - Click "Publish release"
   - Release becomes available for download

### Verification Checklist

- [ ] Tag created: `v0.1.0`
- [ ] Branch correct: `release-v0.1.0-upload-media-manager-exe-e01`
- [ ] Executables uploaded:
  - [ ] `media-manager.exe` (Windows)
  - [ ] `media-manager-linux-x64` (Linux)
- [ ] Release notes complete and clear
- [ ] System requirements documented
- [ ] Installation instructions included
- [ ] Links to documentation working
- [ ] No broken links or typos

## Step 6: Verify Release

### Download and Test

1. **Download Files**:
   - Click on executable from release page
   - Verify download completes
   - Check file size matches

2. **Test Executable** (on relevant platform):
   - Windows: Download and run `media-manager.exe`
   - Linux: Download and run `media-manager-linux-x64`
   - macOS: Install from source or pip

3. **Verify Information**:
   - Help → About shows version 0.1.0
   - Application functions correctly
   - No error messages

### File Integrity Verification

**Windows**:
```cmd
certutil -hashfile media-manager.exe SHA256
```

**Linux/macOS**:
```bash
sha256sum media-manager.exe
shasum -a 256 media-manager-linux-x64
```

## Step 7: Announce Release

### Where to Announce

1. **GitHub**:
   - Publish release
   - Create milestone (optional)
   - Close related issues

2. **Documentation**:
   - Update README.md with download link
   - Update CHANGELOG.md with release info
   - Update version numbers

3. **External** (if applicable):
   - Social media announcements
   - Project blog post
   - Mailing list notification

## Complete Release Notes Example

```markdown
# 🎉 Media Manager v0.1.0 - Initial MVP Release

**Download**: [Get the executable](https://github.com/your-org/media-manager/releases/download/v0.1.0/media-manager.exe)

## What's New in v0.1.0

### ✨ Core Features
- 📁 Media scanning with intelligent detection
- 🔍 Automatic and manual media matching
- 🎨 Poster and artwork management
- 📝 Subtitle download support (10 languages)
- 📄 NFO metadata generation
- 🖥️ Modern Qt6 user interface

### 📊 Release Information
- **Version**: 0.1.0 (MVP)
- **Release Date**: November 2024
- **Python Support**: 3.8 - 3.12
- **Status**: ✅ Stable

## Installation

### Windows (Easiest)
1. Download `media-manager.exe`
2. Double-click to run
3. No installation needed!

### Other Platforms
- **PyPI**: `pip install media-manager`
- **Source**: Clone repository and run `pip install -e .`

## System Requirements
- **Windows 7+** (x64)
- **500 MB** free disk space
- **Optional**: Internet for downloads

## Documentation
- [Quick Start](https://github.com/your-org/media-manager/blob/main/QUICK_START.md)
- [Installation Guide](https://github.com/your-org/media-manager/blob/main/INSTALLATION.md)
- [User Manual](https://github.com/your-org/media-manager/blob/main/USAGE.md)

## Known Limitations
- Mock data for demonstration (real API in v0.2.0)
- No database backend (JSON storage)
- Desktop application only

---

Built with ❤️ using PySide6 and PyInstaller

[See full release notes](link-to-full-notes)
```

## File Checklist

### Source Files (In Repository)
- ✅ [GITHUB_RELEASE_NOTES_v0.1.0.md](GITHUB_RELEASE_NOTES_v0.1.0.md)
- ✅ [releases/v0.1.0/RELEASE_SUMMARY.md](releases/v0.1.0/RELEASE_SUMMARY.md)
- ✅ [releases/v0.1.0/INSTALL.md](releases/v0.1.0/INSTALL.md)
- ✅ [releases/v0.1.0/BUILD_WINDOWS.md](releases/v0.1.0/BUILD_WINDOWS.md)
- ✅ [releases/v0.1.0/media-manager-linux-x64](releases/v0.1.0/media-manager-linux-x64)

### Build Artifacts (Not in Git, Build When Needed)
- ⚠️ `media-manager.exe` - Build on Windows: `python build_windows.py`
- ⚠️ `media-manager-macos-universal.dmg` - Build on macOS (optional)

## Troubleshooting

### Release Won't Publish
- Check tag exists: `git tag -l`
- Verify branch is current: `git status`
- Try creating tag on GitHub web interface

### Files Won't Upload
- Check file size (GitHub has limits)
- Verify file format is correct
- Try uploading one at a time
- Check internet connection

### Links Are Broken
- Verify repository name
- Check branch names
- Test links before publishing
- Update relative paths if needed

## Next Steps After Release

1. **Merge to Main**: 
   ```bash
   git checkout main
   git merge release-v0.1.0-upload-media-manager-exe-e01
   git push origin main
   ```

2. **Update Documentation**:
   - Update README.md with download links
   - Update CHANGELOG.md
   - Add to documentation index

3. **Create Next Development Branch**:
   ```bash
   git checkout -b develop-v0.2.0
   ```

4. **Plan v0.2.0**:
   - Real API integration
   - Database backend
   - Additional features

## Support

For help with GitHub Releases:
- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases)
- [Creating Releases](https://docs.github.com/en/repositories/releasing-projects-on-github/managing-releases-in-a-repository)

---

**Created**: November 2024
**Version**: 0.1.0
**Status**: Ready for Release
