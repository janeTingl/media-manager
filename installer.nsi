!define APP_NAME "影藏·媒体管理器"
!define APP_EXE "MediaManager.exe"
!define INSTALL_DIR "$PROGRAMFILES\\影藏媒体管理器"

Outfile "MediaManager_Setup.exe"
InstallDir "${INSTALL_DIR}"

Page directory
Page instfiles

Section "Install"
    SetOutPath "$INSTDIR"
    File "dist\\MediaManager.exe"
    File /r "dist\\*"

    CreateShortCut "$DESKTOP\\影藏·媒体管理器.lnk" "$INSTDIR\\${APP_EXE}"
SectionEnd
