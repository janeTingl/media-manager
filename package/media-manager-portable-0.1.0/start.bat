@echo off
title 影藏·媒体管理器
echo Starting 影藏·媒体管理器...
echo.
"影藏·媒体管理器.exe"
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)