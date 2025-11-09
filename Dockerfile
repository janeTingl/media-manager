# Use Python 3.11 slim image for smaller size
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

# Install system dependencies for GUI applications
RUN apt-get update && apt-get install -y \
    xvfb \
    x11-utils \
    x11-xserver-utils \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libfontconfig1 \
    libxkbcommon0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render-util0 \
    libxcb-xinerama0 \
    libxcb-xfixes0 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .

# Copy application source
COPY src/ ./src/
COPY README.md LICENSE CHANGELOG.md ./

# Create non-root user
RUN useradd --create-home --shell /bin/bash media \
    && chown -R media:media /app
USER media

# Create volume for media files and configuration
VOLUME ["/media", "/config"]

# Set environment variables for media paths
ENV MEDIA_MANAGER_MEDIA_DIR=/media \
    MEDIA_MANAGER_CONFIG_DIR=/config \
    DISPLAY=:99

# Expose port for potential web interface (future feature)
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import media_manager; print('OK')" || exit 1

# Default command - start with virtual X server
CMD ["sh", "-c", "Xvfb :99 -screen 0 1024x768x24 > /dev/null 2>&1 & media-manager-demo"]