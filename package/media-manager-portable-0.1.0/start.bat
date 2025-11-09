@echo off
title Media Manager
echo Starting Media Manager...
echo.
"media-manager.exe"
if errorlevel 1 (
    echo.
    echo Application exited with an error.
    pause
)