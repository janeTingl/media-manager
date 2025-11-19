#!/usr/bin/env python3
"""
Create placeholder icons for 影藏·媒体管理器 builds.

This script creates simple placeholder icons for Windows and macOS builds
when proper icons are not available.
"""

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def create_placeholder_icon(size=(256, 256), output_path="icon.png"):
    """Create a simple placeholder icon."""
    # Create a simple square icon with "MM" text
    img = Image.new('RGBA', size, (70, 130, 180, 255))  # Steel blue background
    draw = ImageDraw.Draw(img)

    # Try to use a nice font, fallback to default
    try:
        font = ImageFont.truetype("Arial.ttf", size[0] // 4)
    except OSError:
        font = ImageFont.load_default()

    # Draw "MM" for 影藏·媒体管理器
    text = "MM"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x = (size[0] - text_width) // 2
    y = (size[1] - text_height) // 2

    draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)

    # Save the image
    img.save(output_path)
    print(f"Created placeholder icon: {output_path}")


def create_all_placeholder_icons():
    """Create placeholder icons for all platforms."""
    resources_dir = Path("resources")
    resources_dir.mkdir(exist_ok=True)

    # Create PNG icon
    png_path = resources_dir / "icon.png"
    create_placeholder_icon((512, 512), str(png_path))

    # Create Windows ICO (if PIL supports it)
    try:
        ico_path = resources_dir / "icon.ico"
        # Create multiple sizes for ICO
        sizes = [16, 32, 48, 64, 128, 256]
        images = []

        for size in sizes:
            img = Image.new('RGBA', (size, size), (70, 130, 180, 255))
            draw = ImageDraw.Draw(img)

            # Scale font size
            font_size = max(8, size // 4)
            try:
                font = ImageFont.truetype("Arial.ttf", font_size)
            except OSError:
                font = ImageFont.load_default()

            text = "MM"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]

            x = (size - text_width) // 2
            y = (size - text_height) // 2

            draw.text((x, y), text, fill=(255, 255, 255, 255), font=font)
            images.append(img)

        # Save as ICO
        images[0].save(ico_path, format='ICO', sizes=[(img.width, img.height) for img in images])
        print(f"Created placeholder Windows icon: {ico_path}")

    except Exception as e:
        print(f"Could not create ICO file: {e}")

    # Create macOS ICNS placeholder (will be converted by build script)
    icns_path = resources_dir / "icon.icns"
    if not icns_path.exists():
        # Just copy the PNG as placeholder
        import shutil
        shutil.copy2(png_path, icns_path)
        print(f"Created placeholder macOS icon: {icns_path}")


if __name__ == "__main__":
    print("Creating placeholder icons...")
    create_all_placeholder_icons()
    print("Done!")
