@echo off
chcp 65001 >nul
title 影藏·媒体管理器 - 自动构建系统

echo ====================================================================
echo 影藏·媒体管理器 - 自动构建系统
echo MediaManager - Automatic Build System
echo ====================================================================
echo.
echo 正在启动构建流程...
echo.

REM 检查 Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.8 或更高版本
    echo.
    echo 下载地址: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [信息] 检测到 Python 环境
python --version
echo.

REM 运行构建脚本
echo [信息] 开始构建流程...
echo.
python auto_build.py

if errorlevel 1 (
    echo.
    echo ====================================================================
    echo [失败] 构建过程出现错误
    echo ====================================================================
    echo.
    echo 请查看日志文件获取详细信息
    pause
    exit /b 1
) else (
    echo.
    echo ====================================================================
    echo [成功] 构建完成！
    echo ====================================================================
    echo.
    echo 生成的文件位于 package 目录
    echo.
    pause
)
