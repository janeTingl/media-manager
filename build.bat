@echo off
REM Media Manager Windows Build Script
REM This script provides a simple interface for building the Windows executable

setlocal enabledelayedexpansion

echo Media Manager Windows Build Script
echo ==================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8 or higher from https://python.org
    pause
    exit /b 1
)

REM Show menu
:menu
echo Select build option:
echo 1. Full build (clean + deps + build + package)
echo 2. Quick build (build only)
echo 3. Development build (debug mode)
echo 4. Install dependencies only
echo 5. Clean build artifacts
echo 6. Test executable
echo 7. Show build information
echo 8. Help
echo 0. Exit
echo.

set /p choice="Enter your choice (0-8): "

if "%choice%"=="1" goto full_build
if "%choice%"=="2" goto quick_build
if "%choice%"=="3" goto dev_build
if "%choice%"=="4" goto install_deps
if "%choice%"=="5" goto clean
if "%choice%"=="6" goto test
if "%choice%"=="7" goto info
if "%choice%"=="8" goto help
if "%choice%"=="0" goto exit

echo Invalid choice. Please try again.
echo.
goto menu

:full_build
echo.
echo Starting full build process...
echo.
python build_windows.py
if errorlevel 1 (
    echo.
    echo Build failed! Check the error messages above.
    pause
    goto menu
) else (
    echo.
    echo Build completed successfully!
    echo Check the 'package' directory for output files.
    pause
    goto menu
)

:quick_build
echo.
echo Starting quick build...
echo.
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
python -m PyInstaller --clean --noconfirm --name=media-manager --onefile --windowed --distpath=dist --workpath=build --specpath=. media-manager.spec
if errorlevel 1 (
    echo.
    echo Build failed! Check the error messages above.
    pause
    goto menu
) else (
    echo.
    echo Quick build completed!
    echo Executable: dist\media-manager.exe
    pause
    goto menu
)

:dev_build
echo.
echo Starting development build (debug mode)...
echo.
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
python -m PyInstaller --clean --noconfirm --name=media-manager-dev --onedir --windowed --debug=all --distpath=dist --workpath=build --specpath=. media-manager.spec
if errorlevel 1 (
    echo.
    echo Development build failed! Check the error messages above.
    pause
    goto menu
) else (
    echo.
    echo Development build completed!
    echo Executable directory: dist\media-manager-dev\
    pause
    goto menu
)

:install_deps
echo.
echo Installing build dependencies...
echo.
python -m pip install -r build-requirements.txt
if errorlevel 1 (
    echo.
    echo Dependency installation failed!
    pause
    goto menu
) else (
    echo.
    echo Dependencies installed successfully!
    pause
    goto menu
)

:clean
echo.
echo Cleaning build artifacts...
echo.
if exist build (
    echo Removing build directory...
    rmdir /s /q build
)
if exist dist (
    echo Removing dist directory...
    rmdir /s /q dist
)
if exist package (
    echo Removing package directory...
    rmdir /s /q package
)
if exist *.spec (
    echo Removing spec files...
    del /q *.spec
)
echo.
echo Clean completed!
pause
goto menu

:test
echo.
echo Testing executable...
echo.
if exist dist\media-manager.exe (
    echo Running basic test...
    dist\media-manager.exe --help
    if errorlevel 1 (
        echo Note: --help option not supported (this is normal)
        echo Running basic startup test...
        timeout /t 2 >nul
        start "" /B dist\media-manager.exe
        timeout /t 5 >nul
        taskkill /f /im media-manager.exe >nul 2>&1
        echo Basic startup test completed.
    )
    echo.
    echo Test completed!
) else (
    echo ERROR: Executable not found!
    echo Please build the executable first.
)
pause
goto menu

:info
echo.
echo Media Manager Build Information
echo ===============================
echo.
echo Project: Media Manager
echo Version: 0.1.0
echo Python:
python --version
echo.
echo PyInstaller:
python -m PyInstaller --version
echo.
echo Build Directories:
echo   Build: %CD%\build
echo   Dist:  %CD%\dist
echo   Package: %CD%\package
echo.
echo Output Files:
if exist dist\media-manager.exe (
    echo   Executable: dist\media-manager.exe
    for %%I in (dist\media-manager.exe) do echo   Size: %%~zI bytes
) else (
    echo   Executable: Not found
)
if exist package (
    echo   Package directory: package\
    dir package /b
) else (
    echo   Package directory: Not found
)
echo.
pause
goto menu

:help
echo.
echo Media Manager Build Script Help
echo ===============================
echo.
echo This script helps you build the Media Manager Windows executable.
echo.
echo Build Options:
echo --------------
echo 1. Full build - Complete build process including dependencies and packaging
echo 2. Quick build - Build executable only (faster for testing)
echo 3. Development build - Debug version with console output
echo 4. Install dependencies - Install required Python packages
echo 5. Clean - Remove all build artifacts
echo 6. Test - Test the built executable
echo 7. Information - Show build information and file sizes
echo 8. Help - Show this help message
echo.
echo Output Files:
echo -------------
echo - Executable: dist\media-manager.exe
echo - Portable package: package\media-manager-portable-0.1.0\
echo - Installer package: package\media-manager-installer-0.1.0\
echo - ZIP files: package\*.zip
echo - Release info: package\RELEASE_INFO.txt
echo.
echo Troubleshooting:
echo ----------------
echo - If build fails, check that Python and all dependencies are installed
echo - Ensure you have sufficient disk space (2GB recommended)
echo - Run as Administrator if you encounter permission errors
echo - Antivirus software may interfere with the build process
echo.
echo For detailed documentation, see: PACKAGING_GUIDE.md
echo.
pause
goto menu

:exit
echo.
echo Thank you for using Media Manager Build Script!
echo.
pause
exit /b 0