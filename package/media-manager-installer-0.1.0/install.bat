@echo off
title 影藏·媒体管理器 Installer v0.1.0
echo.
echo 影藏·媒体管理器 Installer v0.1.0
echo ================================
echo.
echo This will install 影藏·媒体管理器 to your system.
echo.
set INSTALL_DIR=%PROGRAMFILES%\media-manager
set SHORTCUT_DIR=%PROGRAMDATA%\Microsoft\Windows\Start Menu\Programs
set DESKTOP_DIR=%USERPROFILE%\Desktop

echo Installing to: %INSTALL_DIR%
echo.

if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"
copy "files\影藏·媒体管理器.exe" "%INSTALL_DIR%\" >nul
copy "files\README.txt" "%INSTALL_DIR%\" >nul

echo Creating Start Menu shortcut...
powershell -command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%SHORTCUT_DIR%\影藏·媒体管理器.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\影藏·媒体管理器.exe'; $Shortcut.Save()"

echo Creating Desktop shortcut...
powershell -command "$WshShell = New-Object -comObject WScript.Shell; $Shortcut = $WshShell.CreateShortcut('%DESKTOP_DIR%\影藏·媒体管理器.lnk'); $Shortcut.TargetPath = '%INSTALL_DIR%\影藏·媒体管理器.exe'; $Shortcut.Save()"

echo.
echo Installation completed successfully!
echo.
echo You can now run 影藏·媒体管理器 from:
echo - Start Menu
echo - Desktop shortcut
echo - Directly from: %INSTALL_DIR%\影藏·媒体管理器.exe
echo.
pause