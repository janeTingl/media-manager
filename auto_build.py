#!/usr/bin/env python3
# type: ignore
"""
影藏·媒体管理器 - 自动构建和打包脚本
Automatic Build and Packaging Script with Complete Logging

功能 (Features):
1. 自动检查环境 - Automatic environment checking
2. 自动安装 PyInstaller - Automatic PyInstaller installation
3. 自动生成版本号 - Automatic version number generation
4. 自动清理旧构建 - Automatic cleanup of old builds
5. 自动构建中文UI - Automatic build with Chinese UI
6. 自动打包 - Automatic packaging
7. 自动生成安装包 - Automatic installer generation
8. 全过程有日志 - Complete logging throughout the process
"""

import hashlib
import json
import logging
import platform
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

# ===== 配置 Configuration =====
PROJECT_ROOT = Path(__file__).parent.absolute()
SRC_DIR = PROJECT_ROOT / "src"
BUILD_DIR = PROJECT_ROOT / "build"
DIST_DIR = PROJECT_ROOT / "dist"
PACKAGE_DIR = PROJECT_ROOT / "package"
LOG_DIR = PROJECT_ROOT / "build_logs"

APP_NAME = "影藏·媒体管理器"
APP_NAME_EN = "MediaManager"
SPEC_FILE = SRC_DIR / "media_manager" / "media_manager.spec"

# 确保日志目录存在
LOG_DIR.mkdir(exist_ok=True)

# ===== 日志配置 Logging Configuration =====
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
log_file = LOG_DIR / f"build_{timestamp}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_file, encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger(__name__)


class BuildError(Exception):
    """构建错误"""

    pass


class AutoBuildSystem:
    """自动构建系统"""

    def __init__(self):
        self.version = self.get_version()
        self.build_info = {
            "version": self.version,
            "build_time": datetime.now().isoformat(),
            "platform": platform.system(),
            "python_version": sys.version,
            "steps": [],
        }

    def log_step(self, step_name: str, status: str = "started", details: str = ""):
        """记录构建步骤"""
        step_info = {
            "name": step_name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "details": details,
        }
        self.build_info["steps"].append(step_info)

        if status == "started":
            logger.info(f"{'='*60}")
            logger.info(f"开始: {step_name}")
            logger.info(f"{'='*60}")
        elif status == "completed":
            logger.info(f"✓ 完成: {step_name}")
            if details:
                logger.info(f"  详情: {details}")
        elif status == "failed":
            logger.error(f"✗ 失败: {step_name}")
            if details:
                logger.error(f"  错误: {details}")

    def run_command(self, cmd, cwd=None, check=True):
        """执行命令并记录输出"""
        logger.info(f"执行命令: {' '.join(str(c) for c in cmd)}")
        if cwd:
            logger.info(f"工作目录: {cwd}")

        try:
            result = subprocess.run(
                cmd, cwd=cwd, capture_output=True, text=True, check=check
            )

            if result.stdout:
                logger.debug(f"STDOUT:\n{result.stdout}")
            if result.stderr:
                logger.debug(f"STDERR:\n{result.stderr}")

            return result
        except subprocess.CalledProcessError as e:
            logger.error(f"命令执行失败: {e}")
            if e.stdout:
                logger.error(f"STDOUT:\n{e.stdout}")
            if e.stderr:
                logger.error(f"STDERR:\n{e.stderr}")
            raise

    def get_version(self):
        """获取版本号"""
        # 首先尝试从 __init__.py 获取
        init_file = SRC_DIR / "media_manager" / "__init__.py"
        try:
            with open(init_file, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("__version__"):
                        version = line.split("=")[1].strip().strip('"').strip("'")
                        logger.info(f"从 __init__.py 获取版本号: {version}")
                        return version
        except Exception as e:
            logger.warning(f"无法从 __init__.py 读取版本号: {e}")

        # 尝试从 git 标签获取
        try:
            result = self.run_command(
                ["git", "describe", "--tags", "--abbrev=0"], check=False
            )
            if result.returncode == 0:
                version = result.stdout.strip()
                logger.info(f"从 git 标签获取版本号: {version}")
                return version
        except Exception as e:
            logger.warning(f"无法从 git 获取版本号: {e}")

        # 使用默认版本号
        version = "0.1.0"
        logger.info(f"使用默认版本号: {version}")
        return version

    def check_environment(self):
        """1. 检查环境"""
        self.log_step("检查环境", "started")

        try:
            # 检查 Python 版本
            py_version = sys.version_info
            logger.info(
                f"Python 版本: {py_version.major}.{py_version.minor}.{py_version.micro}"
            )
            if py_version < (3, 8):
                raise BuildError("需要 Python 3.8 或更高版本")

            # 检查 pip
            try:
                self.run_command([sys.executable, "-m", "pip", "--version"])
                logger.info("✓ pip 可用")
            except Exception as e:
                raise BuildError(f"pip 不可用: {e}") from e

            # 检查必需的包
            required_packages = {
                "PySide6": "PySide6-Essentials",
                "sqlalchemy": "sqlalchemy",
                "sqlmodel": "sqlmodel",
                "requests": "requests",
            }

            missing_packages = []
            for module, package in required_packages.items():
                try:
                    __import__(module)
                    logger.info(f"✓ {module} 已安装")
                except ImportError:
                    logger.warning(f"✗ {module} 未安装")
                    missing_packages.append(package)

            if missing_packages:
                logger.info(f"需要安装的包: {', '.join(missing_packages)}")
                self.run_command(
                    [sys.executable, "-m", "pip", "install"] + missing_packages
                )

            # 检查项目结构
            if not (SRC_DIR / "media_manager" / "main.py").exists():
                raise BuildError("找不到主程序文件 main.py")

            logger.info("✓ 项目结构正确")

            self.log_step("检查环境", "completed", "环境检查通过")
            return True

        except Exception as e:
            self.log_step("检查环境", "failed", str(e))
            raise

    def install_pyinstaller(self):
        """2. 安装/更新 PyInstaller"""
        self.log_step("安装 PyInstaller", "started")

        try:
            # 检查是否已安装
            try:
                import PyInstaller

                version = PyInstaller.__version__
                logger.info(f"PyInstaller 已安装，版本: {version}")

                # 检查是否需要更新
                result = self.run_command(
                    [sys.executable, "-m", "pip", "list", "--outdated"], check=False
                )

                if "pyinstaller" in result.stdout.lower():
                    logger.info("PyInstaller 有更新可用，正在更新...")
                    self.run_command(
                        [
                            sys.executable,
                            "-m",
                            "pip",
                            "install",
                            "--upgrade",
                            "pyinstaller",
                        ]
                    )

            except ImportError:
                logger.info("PyInstaller 未安装，正在安装...")
                self.run_command(
                    [sys.executable, "-m", "pip", "install", "pyinstaller"]
                )

            # 验证安装
            import PyInstaller

            version = PyInstaller.__version__
            logger.info(f"✓ PyInstaller 版本: {version}")

            self.log_step("安装 PyInstaller", "completed", f"版本 {version}")
            return True

        except Exception as e:
            self.log_step("安装 PyInstaller", "failed", str(e))
            raise

    def update_version(self):
        """3. 更新版本号"""
        self.log_step("更新版本号", "started")

        try:
            logger.info(f"当前版本号: {self.version}")

            # 更新 __init__.py 中的版本号
            init_file = SRC_DIR / "media_manager" / "__init__.py"
            if init_file.exists():
                with open(init_file, encoding="utf-8") as f:
                    content = f.read()

                # 只在版本号不同时更新
                if f'__version__ = "{self.version}"' not in content:
                    import re

                    new_content = re.sub(
                        r'__version__\s*=\s*["\'].*?["\']',
                        f'__version__ = "{self.version}"',
                        content,
                    )
                    with open(init_file, "w", encoding="utf-8") as f:
                        f.write(new_content)
                    logger.info(f"✓ 更新 __init__.py 版本号为 {self.version}")
                else:
                    logger.info(f"✓ __init__.py 版本号已是 {self.version}")

            self.log_step("更新版本号", "completed", f"版本: {self.version}")
            return True

        except Exception as e:
            self.log_step("更新版本号", "failed", str(e))
            raise

    def clean_old_builds(self):
        """4. 清理旧构建"""
        self.log_step("清理旧构建", "started")

        try:
            dirs_to_clean = [BUILD_DIR, DIST_DIR, PACKAGE_DIR]

            for dir_path in dirs_to_clean:
                if dir_path.exists():
                    logger.info(f"清理目录: {dir_path}")
                    shutil.rmtree(dir_path)
                    logger.info(f"✓ 已清理: {dir_path}")
                else:
                    logger.info(f"目录不存在，跳过: {dir_path}")

            # 创建新的目录
            for dir_path in dirs_to_clean:
                dir_path.mkdir(exist_ok=True)
                logger.info(f"✓ 创建目录: {dir_path}")

            # 清理 __pycache__
            pycache_count = 0
            for pycache in PROJECT_ROOT.rglob("__pycache__"):
                shutil.rmtree(pycache)
                pycache_count += 1

            if pycache_count > 0:
                logger.info(f"✓ 清理了 {pycache_count} 个 __pycache__ 目录")

            self.log_step(
                "清理旧构建", "completed", f"清理了 {len(dirs_to_clean)} 个目录"
            )
            return True

        except Exception as e:
            self.log_step("清理旧构建", "failed", str(e))
            raise

    def build_executable(self):
        """6. 构建可执行文件"""
        self.log_step("构建可执行文件", "started")

        try:
            # 检查 spec 文件
            if not SPEC_FILE.exists():
                raise BuildError(f"找不到 spec 文件: {SPEC_FILE}")

            logger.info(f"使用 spec 文件: {SPEC_FILE}")

            # 运行 PyInstaller
            logger.info("开始 PyInstaller 构建...")
            self.run_command(
                [
                    sys.executable,
                    "-m",
                    "PyInstaller",
                    "--clean",
                    "--noconfirm",
                    str(SPEC_FILE),
                ],
                cwd=PROJECT_ROOT,
            )

            # 检查生成的可执行文件
            if platform.system() == "Windows":
                exe_name = f"{APP_NAME_EN}.exe"
            elif platform.system() == "Darwin":
                exe_name = f"{APP_NAME}.app"
            else:
                exe_name = APP_NAME_EN

            exe_path = DIST_DIR / exe_name
            if not exe_path.exists():
                raise BuildError(f"未找到生成的可执行文件: {exe_path}")

            # 获取文件大小
            file_size = exe_path.stat().st_size / (1024 * 1024)  # MB
            logger.info(f"✓ 可执行文件生成成功: {exe_name}")
            logger.info(f"  大小: {file_size:.2f} MB")
            logger.info(f"  路径: {exe_path}")

            self.log_step(
                "构建可执行文件", "completed", f"{exe_name} ({file_size:.2f} MB)"
            )
            return exe_path

        except Exception as e:
            self.log_step("构建可执行文件", "failed", str(e))
            raise

    def create_portable_package(self, exe_path):
        """7a. 创建便携版包"""
        self.log_step("创建便携版包", "started")

        try:
            portable_dir = PACKAGE_DIR / f"{APP_NAME_EN}-Portable-{self.version}"
            portable_dir.mkdir(parents=True, exist_ok=True)

            # 复制可执行文件
            exe_name = exe_path.name
            shutil.copy2(exe_path, portable_dir / exe_name)
            logger.info(f"✓ 复制可执行文件: {exe_name}")

            # 创建 README
            readme_content = f"""# {APP_NAME} - 便携版

版本: {self.version}
构建时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

## 使用说明

1. 双击 {exe_name} 运行程序
2. 首次运行会在用户目录创建配置文件
3. 数据库和日志文件保存在: %USERPROFILE%\\.media-manager\\

## 系统要求

- Windows 7 或更高版本 (64位)
- 至少 4GB 内存
- 至少 100MB 可用磁盘空间

## 特点

✓ 无需安装
✓ 可从 USB 驱动器运行
✓ 不修改系统注册表
✓ 完整的中文界面

## 技术支持

如有问题，请查看日志文件: %USERPROFILE%\\.media-manager\\logs\\app.log

---
{APP_NAME} - 影视媒体管理专家
"""

            with open(portable_dir / "README.txt", "w", encoding="utf-8") as f:
                f.write(readme_content)
            logger.info("✓ 创建 README.txt")

            # 创建启动脚本
            if platform.system() == "Windows":
                start_script = f"""@echo off
chcp 65001 >nul
echo 正在启动 {APP_NAME}...
start "" "{exe_name}"
"""
                with open(portable_dir / "启动.bat", "w", encoding="utf-8") as f:
                    f.write(start_script)
                logger.info("✓ 创建 启动.bat")

            # 创建压缩包
            zip_path = PACKAGE_DIR / f"{APP_NAME_EN}-Portable-{self.version}.zip"
            shutil.make_archive(
                str(zip_path.with_suffix("")),
                "zip",
                portable_dir.parent,
                portable_dir.name,
            )
            logger.info(f"✓ 创建压缩包: {zip_path.name}")

            # 计算哈希
            sha256 = self.calculate_file_hash(zip_path)
            logger.info(f"  SHA256: {sha256}")

            self.log_step("创建便携版包", "completed", f"{zip_path.name}")
            return zip_path

        except Exception as e:
            self.log_step("创建便携版包", "failed", str(e))
            raise

    def create_installer_package(self, exe_path):
        """7b. 创建安装包"""
        self.log_step("创建安装包", "started")

        try:
            # 检查是否在 Windows 上
            if platform.system() != "Windows":
                logger.info("非 Windows 系统，跳过安装包创建")
                self.log_step("创建安装包", "completed", "仅支持 Windows")
                return None

            # 创建 Inno Setup 脚本
            iss_file = self.create_inno_setup_script(exe_path)
            logger.info(f"✓ 创建 Inno Setup 脚本: {iss_file}")

            # 尝试使用 Inno Setup 编译
            try:
                # 查找 Inno Setup 编译器
                iscc_paths = [
                    r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe",
                    r"C:\Program Files\Inno Setup 6\ISCC.exe",
                    r"C:\Program Files (x86)\Inno Setup 5\ISCC.exe",
                    r"C:\Program Files\Inno Setup 5\ISCC.exe",
                ]

                iscc_exe = None
                for path in iscc_paths:
                    if Path(path).exists():
                        iscc_exe = path
                        break

                if iscc_exe:
                    logger.info(f"找到 Inno Setup: {iscc_exe}")
                    self.run_command([iscc_exe, str(iss_file)])

                    # 检查生成的安装程序
                    installer_path = (
                        PACKAGE_DIR / f"{APP_NAME_EN}-Setup-{self.version}.exe"
                    )
                    if installer_path.exists():
                        logger.info(f"✓ 安装程序创建成功: {installer_path.name}")

                        # 计算哈希
                        sha256 = self.calculate_file_hash(installer_path)
                        logger.info(f"  SHA256: {sha256}")

                        self.log_step(
                            "创建安装包", "completed", f"{installer_path.name}"
                        )
                        return installer_path
                else:
                    logger.warning("未找到 Inno Setup，无法创建安装程序")
                    logger.info(
                        "请从 https://jrsoftware.org/isdl.php 下载并安装 Inno Setup"
                    )
                    self.log_step("创建安装包", "completed", "需要安装 Inno Setup")
                    return iss_file

            except Exception as e:
                logger.warning(f"Inno Setup 编译失败: {e}")
                logger.info(f"已创建脚本文件: {iss_file}")
                logger.info("请手动运行 Inno Setup 编译器")
                self.log_step("创建安装包", "completed", "脚本已创建，需手动编译")
                return iss_file

        except Exception as e:
            self.log_step("创建安装包", "failed", str(e))
            # 不抛出异常，允许构建继续
            logger.warning("安装包创建失败，但构建已完成")
            return None

    def create_inno_setup_script(self, exe_path):
        """创建 Inno Setup 脚本"""
        iss_content = f"""; {APP_NAME} 安装脚本
; 使用 Inno Setup 创建

#define MyAppName "{APP_NAME}"
#define MyAppNameEn "{APP_NAME_EN}"
#define MyAppVersion "{self.version}"
#define MyAppPublisher "{APP_NAME}团队"
#define MyAppURL "https://github.com/yourusername/media-manager"
#define MyAppExeName "{exe_path.name}"

[Setup]
AppId={{{{B8E9F3A1-8C2D-4F5E-9B7A-3D6C8E1F4A2B}}}}
AppName={{#MyAppName}}
AppVersion={{#MyAppVersion}}
AppPublisher={{#MyAppPublisher}}
AppPublisherURL={{#MyAppURL}}
AppSupportURL={{#MyAppURL}}
AppUpdatesURL={{#MyAppURL}}
DefaultDirName={{autopf}}\\{{#MyAppName}}
DefaultGroupName={{#MyAppName}}
AllowNoIcons=yes
LicenseFile={PROJECT_ROOT}\\LICENSE
OutputDir={PACKAGE_DIR}
OutputBaseFilename={{#MyAppNameEn}}-Setup-{{#MyAppVersion}}
Compression=lzma
SolidCompression=yes
WizardStyle=modern
SetupIconFile={PROJECT_ROOT}\\icon.ico
UninstallDisplayIcon={{app}}\\{{#MyAppExeName}}
VersionInfoVersion={{#MyAppVersion}}
ArchitecturesAllowed=x64
ArchitecturesInstallIn64BitMode=x64

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Languages\\ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "{{cm:CreateDesktopIcon}}"; GroupDescription: "{{cm:AdditionalIcons}}"

[Files]
Source: "{exe_path}"; DestDir: "{{app}}"; Flags: ignoreversion

[Icons]
Name: "{{group}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"
Name: "{{group}}\\{{cm:UninstallProgram,{{#MyAppName}}}}"; Filename: "{{uninstallexe}}"
Name: "{{autodesktop}}\\{{#MyAppName}}"; Filename: "{{app}}\\{{#MyAppExeName}}"; Tasks: desktopicon

[Run]
Filename: "{{app}}\\{{#MyAppExeName}}"; Description: "{{cm:LaunchProgram,{{#StringChange(MyAppName, '&', '&&')}}}}"; Flags: nowait postinstall skipifsilent

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
  if IsWin64 = False then
  begin
    MsgBox('此程序仅支持 64 位 Windows 系统。', mbError, MB_OK);
    Result := False;
  end;
end;
"""

        iss_file = PACKAGE_DIR / f"{APP_NAME_EN}-Setup.iss"
        with open(
            iss_file, "w", encoding="utf-8-sig"
        ) as f:  # UTF-8 with BOM for Inno Setup
            f.write(iss_content)

        return iss_file

    def calculate_file_hash(self, file_path):
        """计算文件 SHA256 哈希"""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def generate_build_report(self, exe_path, portable_path, installer_path):
        """8. 生成构建报告"""
        self.log_step("生成构建报告", "started")

        try:
            report_file = PACKAGE_DIR / f"BUILD_REPORT_{timestamp}.txt"

            report = f"""{'='*70}
{APP_NAME} - 构建报告
{'='*70}

构建信息:
  版本号: {self.version}
  构建时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
  平台: {platform.system()} {platform.release()}
  Python 版本: {sys.version.split()[0]}

生成文件:
"""

            # 可执行文件信息
            if exe_path and exe_path.exists():
                file_size = exe_path.stat().st_size / (1024 * 1024)
                file_hash = self.calculate_file_hash(exe_path)
                report += f"""
  1. 可执行文件:
     文件名: {exe_path.name}
     路径: {exe_path}
     大小: {file_size:.2f} MB
     SHA256: {file_hash}
"""

            # 便携版信息
            if portable_path and portable_path.exists():
                file_size = portable_path.stat().st_size / (1024 * 1024)
                file_hash = self.calculate_file_hash(portable_path)
                report += f"""
  2. 便携版包:
     文件名: {portable_path.name}
     路径: {portable_path}
     大小: {file_size:.2f} MB
     SHA256: {file_hash}
"""

            # 安装包信息
            if installer_path:
                if isinstance(installer_path, Path) and installer_path.exists():
                    if installer_path.suffix == ".exe":
                        file_size = installer_path.stat().st_size / (1024 * 1024)
                        file_hash = self.calculate_file_hash(installer_path)
                        report += f"""
  3. 安装程序:
     文件名: {installer_path.name}
     路径: {installer_path}
     大小: {file_size:.2f} MB
     SHA256: {file_hash}
"""
                    else:
                        report += f"""
  3. 安装脚本:
     文件名: {installer_path.name}
     路径: {installer_path}
     说明: 请使用 Inno Setup 编译此脚本
"""

            # 构建步骤
            report += """
构建步骤:
"""
            for i, step in enumerate(self.build_info["steps"], 1):
                status_icon = {"completed": "✓", "failed": "✗", "started": "→"}.get(
                    step["status"], "?"
                )

                report += f"  {i}. {status_icon} {step['name']} - {step['status']}\n"
                if step.get("details"):
                    report += f"     {step['details']}\n"

            # 日志文件
            report += f"""
日志文件:
  构建日志: {log_file}

使用说明:
  1. 便携版: 解压后直接运行 {exe_path.name if exe_path else APP_NAME_EN}
  2. 安装版: 运行安装程序，按提示安装

系统要求:
  - Windows 7 或更高版本 (64位)
  - 至少 4GB 内存
  - 至少 100MB 可用磁盘空间

{'='*70}
构建完成
{'='*70}
"""

            with open(report_file, "w", encoding="utf-8") as f:
                f.write(report)

            logger.info(f"✓ 构建报告已生成: {report_file}")

            # 同时保存 JSON 格式
            json_file = PACKAGE_DIR / f"BUILD_INFO_{timestamp}.json"
            with open(json_file, "w", encoding="utf-8") as f:
                json.dump(self.build_info, f, indent=2, ensure_ascii=False)

            logger.info(f"✓ JSON 信息已保存: {json_file}")

            # 输出报告到控制台
            print("\n" + report)

            self.log_step("生成构建报告", "completed", str(report_file))
            return report_file

        except Exception as e:
            self.log_step("生成构建报告", "failed", str(e))
            raise

    def run(self):
        """运行完整的构建流程"""
        logger.info("")
        logger.info("=" * 70)
        logger.info(f"{APP_NAME} - 自动构建系统")
        logger.info("=" * 70)
        logger.info(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"项目目录: {PROJECT_ROOT}")
        logger.info(f"日志文件: {log_file}")
        logger.info("=" * 70)
        logger.info("")

        exe_path = None
        portable_path = None
        installer_path = None

        try:
            # 1. 检查环境
            self.check_environment()

            # 2. 安装 PyInstaller
            self.install_pyinstaller()

            # 3. 更新版本号
            self.update_version()

            # 4. 清理旧构建
            self.clean_old_builds()

            # 5. 构建可执行文件
            exe_path = self.build_executable()

            # 7a. 创建便携版包
            portable_path = self.create_portable_package(exe_path)

            # 7b. 创建安装包
            installer_path = self.create_installer_package(exe_path)

            # 8. 生成构建报告
            self.generate_build_report(exe_path, portable_path, installer_path)

            logger.info("")
            logger.info("=" * 70)
            logger.info("✓ 构建流程完成！")
            logger.info("=" * 70)
            logger.info("")
            logger.info("生成的文件:")
            logger.info(f"  - 可执行文件: {exe_path}")
            logger.info(f"  - 便携版包: {portable_path}")
            if installer_path:
                logger.info(f"  - 安装包: {installer_path}")
            logger.info("")
            logger.info(f"所有文件位于: {PACKAGE_DIR}")
            logger.info(f"完整日志: {log_file}")
            logger.info("")

            return True

        except KeyboardInterrupt:
            logger.error("")
            logger.error("=" * 70)
            logger.error("构建被用户中断")
            logger.error("=" * 70)
            return False

        except Exception as e:
            logger.error("")
            logger.error("=" * 70)
            logger.error(f"构建失败: {e}")
            logger.error("=" * 70)
            logger.error("")
            logger.error(f"请查看日志文件获取详细信息: {log_file}")
            return False

        finally:
            end_time = datetime.now()
            logger.info(f"结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")


def main():
    """主函数"""
    print(
        f"""
{'='*70}
{APP_NAME} - 自动构建和打包系统
Automatic Build and Packaging System
{'='*70}

功能:
  1. ✓ 自动检查环境
  2. ✓ 自动安装 PyInstaller
  3. ✓ 自动生成版本号
  4. ✓ 自动清理旧构建
  5. ✓ 自动构建可执行文件
  6. ✓ 自动创建安装包
  7. ✓ 全过程日志记录

{'='*70}
"""
    )

    try:
        builder = AutoBuildSystem()
        success = builder.run()

        return 0 if success else 1

    except Exception as e:
        logger.error(f"发生未预期的错误: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
