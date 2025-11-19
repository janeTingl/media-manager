# 影藏·媒体管理器 Windows Build Script (PowerShell)
# This script provides a PowerShell interface for building the Windows executable

param(
    [Parameter(Mandatory=$false)]
    [ValidateSet("full", "quick", "dev", "deps", "clean", "test", "info", "help")]
    [string]$Action = "menu"
)

# Function to write colored output
function Write-ColorOutput {
    param(
        [string]$Message,
        [ConsoleColor]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Function to check if running as Administrator
function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

# Function to check Python installation
function Test-Python {
    try {
        $pythonVersion = python --version 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-ColorOutput "Python found: $pythonVersion" "Green"
            return $true
        }
    } catch {
        # Python command failed
    }
    
    Write-ColorOutput "ERROR: Python is not installed or not in PATH" "Red"
    Write-ColorOutput "Please install Python 3.8 or higher from https://python.org" "Yellow"
    return $false
}

# Function to show menu
function Show-Menu {
    Clear-Host
    Write-ColorOutput "影藏·媒体管理器 Windows Build Script (PowerShell)" "Cyan"
    Write-ColorOutput "================================================" "Cyan"
    Write-Host ""
    
    Write-Host "Select build option:"
    Write-Host "1. Full build (clean + deps + build + package)"
    Write-Host "2. Quick build (build only)"
    Write-Host "3. Development build (debug mode)"
    Write-Host "4. Install dependencies only"
    Write-Host "5. Clean build artifacts"
    Write-Host "6. Test executable"
    Write-Host "7. Show build information"
    Write-Host "8. Help"
    Write-Host "0. Exit"
    Write-Host ""
    
    $choice = Read-Host "Enter your choice (0-8)"
    
    switch ($choice) {
        "1" { Invoke-FullBuild }
        "2" { Invoke-QuickBuild }
        "3" { Invoke-DevBuild }
        "4" { Install-Dependencies }
        "5" { Invoke-Clean }
        "6" { Invoke-Test }
        "7" { Show-Info }
        "8" { Show-Help }
        "0" { exit }
        default { 
            Write-ColorOutput "Invalid choice. Please try again." "Red"
            Start-Sleep -Seconds 2
            Show-Menu
        }
    }
}

# Function to run full build
function Invoke-FullBuild {
    Write-Host ""
    Write-ColorOutput "Starting full build process..." "Yellow"
    Write-Host ""
    
    try {
        python build_windows.py
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-ColorOutput "Build completed successfully!" "Green"
            Write-ColorOutput "Check the 'package' directory for output files." "Cyan"
        } else {
            Write-Host ""
            Write-ColorOutput "Build failed! Check the error messages above." "Red"
        }
    } catch {
        Write-ColorOutput "Build failed with exception: $($_.Exception.Message)" "Red"
    }
    
    Write-Host ""
    Read-Host "Press Enter to continue"
    Show-Menu
}

# Function to run quick build
function Invoke-QuickBuild {
    Write-Host ""
    Write-ColorOutput "Starting quick build..." "Yellow"
    Write-Host ""
    
    # Clean previous builds
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    
    try {
        python -m PyInstaller --clean --noconfirm --name=media-manager --onefile --windowed --distpath=dist --workpath=build --specpath=. media-manager.spec
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-ColorOutput "Quick build completed!" "Green"
            Write-ColorOutput "Executable: dist\影藏·媒体管理器.exe" "Cyan"
        } else {
            Write-Host ""
            Write-ColorOutput "Build failed! Check the error messages above." "Red"
        }
    } catch {
        Write-ColorOutput "Build failed with exception: $($_.Exception.Message)" "Red"
    }
    
    Write-Host ""
    Read-Host "Press Enter to continue"
    Show-Menu
}

# Function to run development build
function Invoke-DevBuild {
    Write-Host ""
    Write-ColorOutput "Starting development build (debug mode)..." "Yellow"
    Write-Host ""
    
    # Clean previous builds
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    
    try {
        python -m PyInstaller --clean --noconfirm --name=media-manager-dev --onedir --windowed --debug=all --distpath=dist --workpath=build --specpath=. media-manager.spec
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-ColorOutput "Development build completed!" "Green"
            Write-ColorOutput "Executable directory: dist\media-manager-dev\" "Cyan"
        } else {
            Write-Host ""
            Write-ColorOutput "Development build failed! Check the error messages above." "Red"
        }
    } catch {
        Write-ColorOutput "Development build failed with exception: $($_.Exception.Message)" "Red"
    }
    
    Write-Host ""
    Read-Host "Press Enter to continue"
    Show-Menu
}

# Function to install dependencies
function Install-Dependencies {
    Write-Host ""
    Write-ColorOutput "Installing build dependencies..." "Yellow"
    Write-Host ""
    
    try {
        python -m pip install -r build-requirements.txt
        if ($LASTEXITCODE -eq 0) {
            Write-Host ""
            Write-ColorOutput "Dependencies installed successfully!" "Green"
        } else {
            Write-Host ""
            Write-ColorOutput "Dependency installation failed!" "Red"
        }
    } catch {
        Write-ColorOutput "Dependency installation failed with exception: $($_.Exception.Message)" "Red"
    }
    
    Write-Host ""
    Read-Host "Press Enter to continue"
    Show-Menu
}

# Function to clean build artifacts
function Invoke-Clean {
    Write-Host ""
    Write-ColorOutput "Cleaning build artifacts..." "Yellow"
    Write-Host ""
    
    $itemsToRemove = @("build", "dist", "package", "*.spec")
    
    foreach ($item in $itemsToRemove) {
        if (Test-Path $item) {
            Write-Host "Removing $item..."
            Remove-Item -Recurse -Force $item -ErrorAction SilentlyContinue
        }
    }
    
    Write-Host ""
    Write-ColorOutput "Clean completed!" "Green"
    Write-Host ""
    Read-Host "Press Enter to continue"
    Show-Menu
}

# Function to test executable
function Invoke-Test {
    Write-Host ""
    Write-ColorOutput "Testing executable..." "Yellow"
    Write-Host ""
    
    $exePath = "dist\影藏·媒体管理器.exe"
    
    if (Test-Path $exePath) {
        Write-ColorOutput "Running basic test..." "Cyan"
        
        try {
            & $exePath --help
            if ($LASTEXITCODE -ne 0) {
                Write-Host "Note: --help option not supported (this is normal)" "Yellow"
                Write-Host "Running basic startup test..." "Cyan"
                
                $process = Start-Process -FilePath $exePath -PassThru
                Start-Sleep -Seconds 5
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
                
                Write-Host "Basic startup test completed." "Green"
            }
        } catch {
            Write-ColorOutput "Test failed: $($_.Exception.Message)" "Red"
        }
        
        Write-Host ""
        Write-ColorOutput "Test completed!" "Green"
    } else {
        Write-ColorOutput "ERROR: Executable not found!" "Red"
        Write-ColorOutput "Please build the executable first." "Yellow"
    }
    
    Write-Host ""
    Read-Host "Press Enter to continue"
    Show-Menu
}

# Function to show build information
function Show-Info {
    Write-Host ""
    Write-ColorOutput "影藏·媒体管理器 Build Information" "Cyan"
    Write-ColorOutput "===============================" "Cyan"
    Write-Host ""
    
    Write-Host "Project: 影藏·媒体管理器"
    Write-Host "Version: 0.1.0"
    Write-Host "PowerShell: $($PSVersionTable.PSVersion)"
    Write-Host ""
    
    if (Test-Python) {
        Write-Host "Python:"
        python --version
        Write-Host ""
        
        Write-Host "PyInstaller:"
        try {
            python -m PyInstaller --version
        } catch {
            Write-Host "PyInstaller not found" "Red"
        }
        Write-Host ""
    }
    
    Write-Host "Build Directories:"
    Write-Host "  Build: $PWD\build"
    Write-Host "  Dist:  $PWD\dist"
    Write-Host "  Package: $PWD\package"
    Write-Host ""
    
    Write-Host "Output Files:"
    $exePath = "dist\影藏·媒体管理器.exe"
    if (Test-Path $exePath) {
        $fileInfo = Get-Item $exePath
        Write-Host "  Executable: $exePath"
        Write-Host "  Size: $($fileInfo.Length) bytes ($([math]::Round($fileInfo.Length / 1MB, 2)) MB)"
    } else {
        Write-Host "  Executable: Not found" "Red"
    }
    
    if (Test-Path "package") {
        Write-Host "  Package directory: package\"
        Get-ChildItem "package" | ForEach-Object { Write-Host "    $($_.Name)" }
    } else {
        Write-Host "  Package directory: Not found" "Red"
    }
    
    Write-Host ""
    Read-Host "Press Enter to continue"
    Show-Menu
}

# Function to show help
function Show-Help {
    Write-Host ""
    Write-ColorOutput "影藏·媒体管理器 Build Script Help (PowerShell)" "Cyan"
    Write-ColorOutput "=============================================" "Cyan"
    Write-Host ""
    Write-Host "This script helps you build the 影藏·媒体管理器 Windows executable."
    Write-Host ""
    Write-Host "Usage:"
    Write-Host "  .\build.ps1                    # Show interactive menu"
    Write-Host "  .\build.ps1 -Action full       # Full build"
    Write-Host "  .\build.ps1 -Action quick      # Quick build"
    Write-Host "  .\build.ps1 -Action dev        # Development build"
    Write-Host "  .\build.ps1 -Action deps       # Install dependencies"
    Write-Host "  .\build.ps1 -Action clean       # Clean artifacts"
    Write-Host "  .\build.ps1 -Action test       # Test executable"
    Write-Host "  .\build.ps1 -Action info       # Show information"
    Write-Host "  .\build.ps1 -Action help       # Show this help"
    Write-Host ""
    Write-Host "Build Options:"
    Write-Host "--------------"
    Write-Host "1. Full build - Complete build process including dependencies and packaging"
    Write-Host "2. Quick build - Build executable only (faster for testing)"
    Write-Host "3. Development build - Debug version with console output"
    Write-Host "4. Install dependencies - Install required Python packages"
    Write-Host "5. Clean - Remove all build artifacts"
    Write-Host "6. Test - Test the built executable"
    Write-Host "7. Information - Show build information and file sizes"
    Write-Host "8. Help - Show this help message"
    Write-Host ""
    Write-Host "Output Files:"
    Write-Host "-------------"
    Write-Host "- Executable: dist\影藏·媒体管理器.exe"
    Write-Host "- Portable package: package\media-manager-portable-0.1.0\"
    Write-Host "- Installer package: package\media-manager-installer-0.1.0\"
    Write-Host "- ZIP files: package\*.zip"
    Write-Host "- Release info: package\RELEASE_INFO.txt"
    Write-Host ""
    Write-Host "Troubleshooting:"
    Write-Host "----------------"
    Write-Host "- If build fails, check that Python and all dependencies are installed"
    Write-Host "- Ensure you have sufficient disk space (2GB recommended)"
    Write-Host "- Run as Administrator if you encounter permission errors"
    Write-Host "- Antivirus software may interfere with the build process"
    Write-Host ""
    Write-Host "For detailed documentation, see: PACKAGING_GUIDE.md"
    Write-Host ""
    Read-Host "Press Enter to continue"
    Show-Menu
}

# Main execution
if (-not (Test-Python)) {
    Read-Host "Press Enter to exit"
    exit 1
}

# Check if running with specific action
if ($Action -ne "menu") {
    switch ($Action) {
        "full" { Invoke-FullBuild }
        "quick" { Invoke-QuickBuild }
        "dev" { Invoke-DevBuild }
        "deps" { Install-Dependencies }
        "clean" { Invoke-Clean }
        "test" { Invoke-Test }
        "info" { Show-Info }
        "help" { Show-Help }
    }
} else {
    # Show interactive menu
    Show-Menu
}