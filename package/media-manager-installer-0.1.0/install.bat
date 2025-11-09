@echo off
title Media Manager Installer v0.1.0
echo.
echo Media Manager Installer v0.1.0
echo ================================
echo.
echo This will install Media Manager to your system.
echo.
set INSTALL_DIR=%PROGRAMFILES%\media-manager
set SHORTCUT_DIR=%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs
set DESKTOP_DIR=%USERPROFILE%\Desktop

echo Installing to: %INSTALL_DIR%
echo.

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy "files\media-manager.exe" "%INSTALL_DIR%\" >nul
copy "files\README.txt" "%INSTALL_DIR%\" >nul

echo Creating Start Menu shortcut...
powershell -command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_DIR%\Media Manager.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\media-manager.exe'; $Shortcut.Save()"

echo Creating Desktop shortcut...
powershell -command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_DIR%\Media Manager.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\media-manager.exe'; $Shortcut.Save()"

echo.
echo Installation completed successfully!
echo.
echo You can now run Media Manager from:
echo - Start Menu
echo - Desktop shortcut
echo - Directly from: %INSTALL_DIR%\media-manager.exe
echo.
pause