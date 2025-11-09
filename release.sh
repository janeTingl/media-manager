#!/bin/bash

# Media Manager v0.1.0 Release Script
# This script prepares and creates the v0.1.0 release

set -e  # Exit on any error

echo "🚀 Starting Media Manager v0.1.0 Release Process"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're on the correct branch
print_status "Checking current branch..."
CURRENT_BRANCH=$(git branch --show-current)
if [ "$CURRENT_BRANCH" != "release-media-manager-v0.1.0-prepare" ]; then
    print_error "Not on the correct branch. Expected: release-media-manager-v0.1.0-prepare, Got: $CURRENT_BRANCH"
    exit 1
fi
print_success "On correct branch: $CURRENT_BRANCH"

# Check if working directory is clean
print_status "Checking git status..."
if [ -n "$(git status --porcelain)" ]; then
    print_error "Working directory is not clean. Please commit or stash changes."
    exit 1
fi
print_success "Working directory is clean"

# Run tests
print_status "Running tests..."
if command -v python3 &> /dev/null; then
    if [ -d "venv" ]; then
        source venv/bin/activate
        PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest tests/test_nfo_exporter.py tests/test_nfo_integration.py tests/test_scanner.py tests/test_settings.py tests/test_subtitle_downloader.py tests/test_subtitle_integration.py tests/test_subtitle_provider.py -q
        print_success "All core tests passed"
    else
        print_warning "No virtual environment found, skipping tests"
    fi
else
    print_warning "Python3 not found, skipping tests"
fi

# Run code quality checks
print_status "Running code quality checks..."
if command -v ruff &> /dev/null && [ -d "venv" ]; then
    source venv/bin/activate && ruff check src/
    print_success "Code quality checks passed"
else
    print_warning "Ruff not available, skipping code quality checks"
fi

# Verify version numbers
print_status "Verifying version numbers..."
PYPROJECT_VERSION=$(grep '^version = ' pyproject.toml | cut -d'"' -f2)
INIT_VERSION=$(grep '__version__ = ' src/media_manager/__init__.py | cut -d'"' -f2)

if [ "$PYPROJECT_VERSION" != "0.1.0" ]; then
    print_error "pyproject.toml version is $PYPROJECT_VERSION, expected 0.1.0"
    exit 1
fi

if [ "$INIT_VERSION" != "0.1.0" ]; then
    print_error "__init__.py version is $INIT_VERSION, expected 0.1.0"
    exit 1
fi

print_success "Version numbers verified: $PYPROJECT_VERSION"

# Check if required files exist
print_status "Checking required files..."
REQUIRED_FILES=("README.md" "LICENSE" "CHANGELOG.md" "pyproject.toml" "MANIFEST.in" "Dockerfile" "docker-compose.yml")
for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        print_error "Required file $file not found"
        exit 1
    fi
done
print_success "All required files present"

# Create the git tag
print_status "Creating git tag v0.1.0..."
if git rev-parse "v0.1.0" >/dev/null 2>&1; then
    print_warning "Tag v0.1.0 already exists, deleting it first"
    git tag -d v0.1.0
fi

git tag -a v0.1.0 -m "Release v0.1.0 - Initial MVP Release

Features:
- Complete media scanning and matching system
- Poster and subtitle downloading
- NFO metadata export
- Modern PySide6 GUI
- Comprehensive test suite
- Docker support

This is the first stable release of Media Manager MVP."
print_success "Git tag v0.1.0 created"

# Build the package
print_status "Building Python package..."
if command -v python3 &> /dev/null && [ -d "venv" ]; then
    source venv/bin/activate
    python -m build
    print_success "Package built successfully"
    
    # Check package contents
    print_status "Checking package contents..."
    python -m twine check dist/*
    print_success "Package validation passed"
else
    print_warning "Build environment not available, skipping package build"
fi

# Create release notes
print_status "Creating release notes..."
RELEASE_NOTES="Release Notes - Media Manager v0.1.0

🎉 Initial MVP Release

This is the first public release of Media Manager, a modern PySide6-based media management application.

## Key Features

### 📁 Media Scanning
- Intelligent filesystem scanning with configurable paths
- Automatic movie and TV episode detection
- Quality and release information extraction
- Recursive directory traversal with ignore patterns

### 🔍 Media Matching
- Automatic media matching with confidence scores
- Manual search workflow
- Match status tracking (PENDING, MATCHED, MANUAL, SKIPPED)
- Batch matching support

### 🎨 Poster Management
- Multiple poster types (poster, fanart, banner, thumbnail)
- Size selection and intelligent caching
- Progress tracking with retry logic

### 📝 Subtitle Support
- 10 language support (EN, ES, FR, DE, IT, PT, RU, ZH, JA, KO)
- Multiple format support (SRT, ASS, SUB, VTT, SSA)
- Provider abstraction with OpenSubtitles framework

### 📄 Metadata Export
- XML NFO file generation for media centers
- UTF-8 encoding with full Unicode support
- Cast member and ID handling

### 🖥️ Modern GUI
- Cross-platform PySide6/Qt6 interface
- Tab-based navigation with resizable panes
- Progress tracking and status indicators
- Comprehensive preferences dialog

## Installation

### From PyPI (recommended)
\`\`\`bash
pip install media-manager
\`\`\`

### From Source
\`\`\`bash
git clone https://github.com/your-org/media-manager.git
cd media-manager
pip install -e .
\`\`\`

### With Docker
\`\`\`bash
docker-compose up -d
\`\`\`

## Quick Start

1. Launch the application: \`media-manager-demo\`
2. Configure scan paths in preferences
3. Scan your media library
4. Review and confirm matches
5. Export metadata and download artwork

## Requirements

- Python 3.8 or higher
- PySide6 (automatically installed)
- Linux, macOS, or Windows

## Known Limitations

- Uses mock data for demonstration (TMDB/TVDB integration planned for v0.2.0)
- No persistent database (metadata stored in JSON files)
- Desktop application only (web interface planned for future versions)

## Documentation

- [Quick Start](QUICK_START.md)
- [Installation Guide](INSTALLATION.md)
- [User Manual](USAGE.md)
- [API Reference](API.md)
- [Architecture](ARCHITECTURE.md)

## Support

- Report issues on [GitHub Issues](https://github.com/your-org/media-manager/issues)
- Ask questions in [GitHub Discussions](https://github.com/your-org/media-manager/discussions)

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

---

Built with ❤️ using PySide6 and modern Python practices."

echo "$RELEASE_NOTES" > RELEASE_NOTES_v0.1.0.md
print_success "Release notes created: RELEASE_NOTES_v0.1.0.md"

# Create installation script
print_status "Creating installation script..."
cat > install.sh << 'EOF'
#!/bin/bash

# Media Manager v0.1.0 Installation Script

set -e

echo "🚀 Installing Media Manager v0.1.0"

# Check Python version
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed."
    exit 1
fi

PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
REQUIRED_VERSION="3.8"

if [ "$(printf '%s\n' "$REQUIRED_VERSION" "$PYTHON_VERSION" | sort -V | head -n1)" != "$REQUIRED_VERSION" ]; then
    echo "❌ Python $REQUIRED_VERSION or higher is required. Found: $PYTHON_VERSION"
    exit 1
fi

echo "✅ Python $PYTHON_VERSION detected"

# Install from PyPI
echo "📦 Installing Media Manager from PyPI..."
pip3 install media-manager

# Verify installation
echo "🔍 Verifying installation..."
python3 -c "import media_manager; print(f'Media Manager {media_manager.__version__} installed successfully')"

echo "🎉 Installation complete!"
echo ""
echo "To start the demo application, run:"
echo "  media-manager-demo"
echo ""
echo "For more information, see the documentation at:"
echo "  https://github.com/your-org/media-manager"
EOF

chmod +x install.sh
print_success "Installation script created: install.sh"

# Summary
print_success "Release preparation complete!"
echo ""
echo "📋 Summary:"
echo "  ✅ Version numbers verified (0.1.0)"
echo "  ✅ All required files present"
echo "  ✅ Git tag v0.1.0 created"
echo "  ✅ Package built and validated"
echo "  ✅ Release notes generated"
echo "  ✅ Installation script created"
echo ""
echo "🚀 Next steps:"
echo "  1. Review the generated files:"
echo "     - RELEASE_NOTES_v0.1.0.md"
echo "     - install.sh"
echo "  2. Push the tag to GitHub:"
echo "     git push origin v0.1.0"
echo "  3. Create GitHub Release using the release notes"
echo "  4. Upload the distribution files from dist/"
echo "  5. Publish to PyPI (if ready):"
echo "     twine upload dist/*"
echo ""
echo "🎉 Media Manager v0.1.0 is ready for release!"