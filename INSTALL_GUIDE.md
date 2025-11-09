# Media Manager v0.1.0 安装指南

本指南说明如何在支持的操作系统上安装并启动 Media Manager v0.1.0。

## 系统要求
- Python 3.9 或更高版本
- 已更新的 `pip`（建议使用 `pip >= 21.0`）
- 支持 Qt 的操作系统（Windows、macOS、主流 Linux 发行版）

## 安装方式

### 1. 从预构建 wheel 安装
```bash
pip install media-manager-0.1.0-py3-none-any.whl
```

### 2. 从 GitHub PyPI 镜像直接安装
```bash
pip install media-manager
```

> ⚠️ 提示：如果同时存在旧版本，请先执行 `pip uninstall media-manager` 卸载旧版。

## 运行应用
安装完成后，可以使用提供的命令启动应用：

```bash
media-manager
```

应用将启动图形界面。如果在无图形界面的环境中运行，请配置 `QT_QPA_PLATFORM=offscreen` 以避免 Qt 报错。

## 验证安装
1. 执行 `media-manager`，确认应用程序窗口可以启动。
2. 打开应用后检查扫描、匹配及海报下载等核心功能。

## 故障排查
- 如果出现 Qt 相关错误，请确认系统已安装桌面环境或将 `QT_QPA_PLATFORM` 设置为 `offscreen`。
- 如果安装过程失败，可尝试升级 `pip`、`setuptools`、`wheel`：
  ```bash
  python -m pip install --upgrade pip setuptools wheel
  ```
- 仍有问题时，请参考仓库中的 `INSTALLATION.md` 获取更详细的指导。
