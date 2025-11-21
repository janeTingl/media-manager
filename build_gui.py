import os
import shutil
import subprocess
import sys
from datetime import datetime
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLabel, QTextEdit, QFileDialog, QMessageBox
)
from PySide6.QtCore import Qt

SPEC_FILE = "media_manager.spec"
NSI_FILE = "installer.nsi"
VERSION_FILE = "version.txt"


def log(text, box):
    box.append(text)
    QApplication.processEvents()


def ensure_python(box):
    """检查 Python 是否可用"""
    try:
        subprocess.check_output(["python", "--version"])
        log("✔ Python 环境正常", box)
        return True
    except Exception:
        log("❌ 未检测到 Python，请检查环境变量。", box)
        return False


def ensure_pyinstaller(box):
    """自动检测并安装 PyInstaller"""
    try:
        subprocess.check_output(["pyinstaller", "--version"])
        log("✔ 已安装 PyInstaller", box)
    except Exception:
        log("⚠ 未安装 PyInstaller，正在安装...", box)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        log("✔ PyInstaller 安装完成", box)


def ensure_i18n_dir(box):
    """自动创建 i18n 目录并检查中文 qm 文件"""
    i18n_path = "src/media_manager/resources/i18n"
    os.makedirs(i18n_path, exist_ok=True)

    qm_file = os.path.join(i18n_path, "media_manager_zh_CN.qm")
    if not os.path.exists(qm_file):
        log(f"⚠ 未找到 {qm_file}，请确认翻译文件已生成！", box)
    else:
        log("✔ i18n 目录存在，中文 QM 文件正常", box)


def auto_version(box):
    """自动生成版本号"""
    if os.path.exists(VERSION_FILE):
        with open(VERSION_FILE, "r", encoding="utf-8") as f:
            old = f.read().strip()
    else:
        old = "0.0.0"

    # 自动递增最后一位
    parts = old.split(".")
    parts[-1] = str(int(parts[-1]) + 1)
    new = ".".join(parts)

    with open(VERSION_FILE, "w", encoding="utf-8") as f:
        f.write(new)

    log(f"✔ 自动版本号: {new}", box)
    return new


def clean(box):
    """清理 dist / build"""
    for folder in ["dist", "build"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            log(f"🧹 已删除 {folder}/", box)
        else:
            log(f"🧹 {folder}/ 不存在，跳过", box)


def run_pyinstaller(box):
    """执行 PyInstaller 打包"""
    log("📦 正在运行 PyInstaller ...", box)
    subprocess.check_call(["pyinstaller", SPEC_FILE])
    log("✔ PyInstaller 打包完成！", box)


def run_nsis(box):
    """生成安装包"""
    log("📦 正在生成 NSIS 安装包...", box)

    if shutil.which("makensis") is None:
        log("❌ 未检测到 NSIS，请先安装 NSIS。", box)
        return False

    subprocess.check_call(["makensis", NSI_FILE])
    log("🎉 安装包已生成：MediaManager_Setup.exe", box)
    return True


class BuildGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("影藏·媒体管理器 — 打包构建工具")
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        self.logbox = QTextEdit()
        self.logbox.setReadOnly(True)

        btn = QPushButton("开始一键构建")
        btn.clicked.connect(self.start_build)

        layout.addWidget(QLabel("影藏·媒体管理器 自动构建系统"))
        layout.addWidget(btn)
        layout.addWidget(self.logbox)

    def start_build(self):
        box = self.logbox
        box.clear()

        log("🔍 开始检测 Python 环境...", box)
        if not ensure_python(box):
            return

        ensure_pyinstaller(box)
        ensure_i18n_dir(box)

        version = auto_version(box)

        clean(box)
        run_pyinstaller(box)
        run_nsis(box)

        log("\n🎉 全部任务完成！", box)
        QMessageBox.information(self, "完成", f"所有任务执行完成！\n版本号：{version}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = BuildGUI()
    gui.show()
    sys.exit(app.exec())
