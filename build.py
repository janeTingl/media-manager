import os
import shutil
import subprocess

SPEC_FILE = "media_manager.spec"
INSTALLER_FILE = "installer.nsi"

def clean_build_dirs():
    print("🧹 清理 build 和 dist ...")
    for folder in ["build", "dist"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
            print(f"删除 {folder}/")
        else:
            print(f"{folder}/ 不存在，跳过")


def run_pyinstaller():
    print("📦 运行 PyInstaller ...")
    cmd = ["pyinstaller", SPEC_FILE]
    subprocess.check_call(cmd)
    print("PyInstaller 打包完成！")


def run_nsis():
    print("📦 生成 NSIS 安装包 ...")
    if shutil.which("makensis") is None:
        print("❌ 未找到 NSIS（makensis）。请安装 NSIS 后重试。")
        return

    cmd = ["makensis", INSTALLER_FILE]
    subprocess.check_call(cmd)
    print("🎉 NSIS 安装包生成完成：MediaManager_Setup.exe")


if __name__ == "__main__":
    clean_build_dirs()
    run_pyinstaller()
    run_nsis()
