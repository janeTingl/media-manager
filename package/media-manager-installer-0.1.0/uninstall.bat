@echo off
title Media Manager Uninstaller
echo.
echo Media Manager Uninstaller
echo =====================
echo.
echo This will remove Media Manager from your system.
echo.
set INSTALL_DIR=%PROGRAMFILES%\media-manager
set SHORTCUT_DIR=%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs
set DESKTOP_DIR=%USERPROFILE%\Desktop

echo Removing files...
if exist "%INSTALL_DIR%" rmdir /s /q "%INSTALL_DIR%"

echo Removing shortcuts...
if exist "%SHORTCUT_DIR%\Media Manager.lnk" del "%SHORTCUT_DIR%\Media Manager.lnk"
if exist "%DESKTOP_DIR%\Media Manager.lnk" del "%DESKTOP_DIR%\Media Manager.lnk"

echo.
echo Media Manager has been uninstalled successfully.
echo.
pause