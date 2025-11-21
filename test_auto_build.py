#!/usr/bin/env python3
# type: ignore
"""
测试自动构建系统
Test script for auto build system
"""

import sys
from pathlib import Path


def test_imports():
    """测试必需的导入"""
    print("测试 Python 导入...")

    try:
        import hashlib  # noqa: F401
        import json  # noqa: F401
        import logging  # noqa: F401
        import os  # noqa: F401
        import platform  # noqa: F401
        import shutil  # noqa: F401

        print("✓ 标准库导入成功")
        return True
    except ImportError as e:
        print(f"✗ 导入失败: {e}")
        return False


def test_project_structure():
    """测试项目结构"""
    print("\n测试项目结构...")

    project_root = Path(__file__).parent
    required_paths = [
        project_root / "src" / "media_manager" / "main.py",
        project_root / "src" / "media_manager" / "__init__.py",
        project_root / "src" / "media_manager" / "media_manager.spec",
    ]

    all_exist = True
    for path in required_paths:
        if path.exists():
            print(f"✓ {path.relative_to(project_root)}")
        else:
            print(f"✗ 缺失: {path.relative_to(project_root)}")
            all_exist = False

    return all_exist


def test_python_version():
    """测试 Python 版本"""
    print("\n测试 Python 版本...")

    version = sys.version_info
    print(f"Python 版本: {version.major}.{version.minor}.{version.micro}")

    if version >= (3, 8):
        print("✓ Python 版本符合要求 (>= 3.8)")
        return True
    else:
        print("✗ Python 版本过低，需要 3.8 或更高")
        return False


def test_auto_build_script():
    """测试自动构建脚本"""
    print("\n测试自动构建脚本...")

    script_path = Path(__file__).parent / "auto_build.py"

    if not script_path.exists():
        print(f"✗ 脚本不存在: {script_path}")
        return False

    print(f"✓ 脚本存在: {script_path}")

    # 测试脚本语法
    try:
        with open(script_path, encoding="utf-8") as f:
            compile(f.read(), script_path, "exec")
        print("✓ 脚本语法正确")
        return True
    except SyntaxError as e:
        print(f"✗ 脚本语法错误: {e}")
        return False


def test_version_detection():
    """测试版本号检测"""
    print("\n测试版本号检测...")

    init_file = Path(__file__).parent / "src" / "media_manager" / "__init__.py"

    try:
        with open(init_file, encoding="utf-8") as f:
            for line in f:
                if line.startswith("__version__"):
                    version = line.split("=")[1].strip().strip('"').strip("'")
                    print(f"✓ 检测到版本号: {version}")
                    return True

        print("✗ 未找到版本号定义")
        return False
    except Exception as e:
        print(f"✗ 读取版本号失败: {e}")
        return False


def main():
    """运行所有测试"""
    print("=" * 70)
    print("自动构建系统 - 测试")
    print("=" * 70)

    tests = [
        ("Python 导入", test_imports),
        ("项目结构", test_project_structure),
        ("Python 版本", test_python_version),
        ("构建脚本", test_auto_build_script),
        ("版本检测", test_version_detection),
    ]

    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n✗ {name} 测试出错: {e}")
            results.append((name, False))

    # 汇总结果
    print("\n" + "=" * 70)
    print("测试结果汇总")
    print("=" * 70)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for name, result in results:
        status = "✓ 通过" if result else "✗ 失败"
        print(f"{status}: {name}")

    print("\n" + "=" * 70)
    print(f"测试完成: {passed}/{total} 通过")
    print("=" * 70)

    if passed == total:
        print("\n✓ 所有测试通过！可以运行构建系统")
        print("\n运行构建:")
        print("  Windows: 一键构建.bat")
        print("  Linux/macOS: ./auto_build.sh")
        print("  或直接运行: python auto_build.py")
        return 0
    else:
        print("\n✗ 部分测试失败，请修复后再运行构建")
        return 1


if __name__ == "__main__":
    sys.exit(main())
