@echo off
title 影藏·媒体管理器 Uninstaller
echo.
echo 影藏·媒体管理器 Uninstaller
echo =====================
echo.
echo This will remove 影藏·媒体管理器 from your system.
echo.
set INSTALL_DIR=%PROGRAMFILES%\media-manager
set SHORTCUT_DIR=%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs
set DESKTOP_DIR=%USERPROFILE%\Desktop

echo Removing files...
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"

echo Removing shortcuts...
if exist "%SHORTCUT_DIR%\影藏·媒体管理器.lnk" del "%SHORTCUT_DIR%\影藏·媒体管理器.lnk"
if exist "%DESKTOP_DIR%\影藏·媒体管理器.lnk" del "%DESKTOP_DIR%\影藏·媒体管理器.lnk"

echo.
echo 影藏·媒体管理器 has been uninstalled successfully.
echo.
pause