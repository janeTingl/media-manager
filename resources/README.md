# 资源目录

本目录包含影藏·媒体管理器应用程序和构建过程使用的资源。

## 图标

- `icon.png` - 高分辨率 PNG 图标（512x512）
- `icon.ico` - Windows 图标文件
- `icon.icns` - macOS 图标文件

## 其他资源

- 应用程序所需的任何额外图片、声音或数据文件

## 图标创建

为发布版本创建适当的图标：

1. 创建 512x512 PNG 图像
2. 转换为特定平台格式：
   - Windows：使用 GIMP 或在线转换器创建 .ico 文件
   - macOS：使用 `iconutil` 命令创建 .icns 文件：
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

## 当前状态

目前，构建过程在没有图标的情况下也能工作，但会显示默认的系统图标。
