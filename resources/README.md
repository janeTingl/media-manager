# Resources Directory

This directory contains resources used by the Media Manager application and build process.

## Icons

- `icon.png` - High-resolution PNG icon (512x512)
- `icon.ico` - Windows icon file
- `icon.icns` - macOS icon file

## Other Resources

- Any additional images, sounds, or data files needed by the application

## Icon Creation

To create proper icons for distribution:

1. Create a 512x512 PNG image
2. Convert to platform-specific formats:
   - Windows: Use GIMP or online converter to create .ico file
   - macOS: Use `iconutil` command to create .icns file:
     ```bash
     mkdir icon.iconset
     sips -z 16 16 icon.png --out icon.iconset/icon_16x16.png
     sips -z 32 32 icon.png --out icon.iconset/icon_16x16@2x.png
     sips -z 32 32 icon.png --out icon.iconset/icon_32x32.png
     sips -z 64 64 icon.png --out icon.iconset/icon_32x32@2x.png
     sips -z 128 128 icon.png --out icon.iconset/icon_128x128.png
     sips -z 256 256 icon.png --out icon.iconset/icon_128x128@2x.png
     sips -z 256 256 icon.png --out icon.iconset/icon_256x256.png
     sips -z 512 512 icon.png --out icon.iconset/icon_256x256@2x.png
     sips -z 512 512 icon.png --out icon.iconset/icon_512x512.png
     iconutil -c icns icon.iconset
     ```

## Current Status

For now, the build process will work without icons, but will show default system icons.