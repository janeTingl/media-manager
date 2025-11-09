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
