# i18n Translation Loading Fix for PyInstaller --onefile Build

## Problem Summary
In the --onefile PyInstaller build, the zh_CN translation file was not being loaded despite being included in the executable. The UI remained in English even after switching to Simplified Chinese and restarting the app.

## Root Cause Analysis
1. **Spec File Configuration Issue**: The original spec file had `exclude_binaries=True` with a COLLECT section, which creates a --onedir build instead of a true --onefile build.
2. **Lack of Debugging**: No logging was present to diagnose translation loading failures in production builds.

## Changes Made

### 1. Fixed PyInstaller Spec File (`src/media_manager/media_manager.spec`)
Changed from a --onedir configuration to a proper --onefile configuration:

**Before:**
```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='影藏·媒体管理器',
    console=False,
    icon=None,
    exclude_binaries=True,  # This was the problem!
    strip=False,
    upx=False,
    runtime_tmpdir=None
)

coll = COLLECT(  # This shouldn't exist for --onefile
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    ...
)
```

**After:**
```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='影藏·媒体管理器',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=None,
    disable_windowed_traceback=False,
)
# No COLLECT section for --onefile builds
```

### 2. Added Comprehensive Debug Logging (`src/media_manager/i18n.py`)
Added detailed logging throughout the translation loading process:

- **install_translators()**: Logs language settings, PyInstaller mode detection, and locale information
- **_load_app_translator()**: Logs search paths, file existence checks, and load success/failure
- **_load_qt_translators()**: Logs Qt translation loading attempts and results
- **_iter_translation_search_paths()**: Logs candidate paths and existence checks
- **_qt_translations_path()**: Logs which Qt translations path is being used

## How the Fix Works

### In Development Mode (no PyInstaller)
1. Translations are loaded from `src/media_manager/resources/i18n/`
2. Qt translations are loaded from the PySide6 installation path
3. Logging shows the paths being searched

### In PyInstaller --onefile Mode
1. PyInstaller extracts all resources to a temporary `sys._MEIPASS` directory
2. The spec file ensures .qm files are copied to `{_MEIPASS}/resources/i18n/`
3. The i18n.py code detects `sys._MEIPASS` and searches there first
4. Qt translations are loaded from `{_MEIPASS}/PySide6/translations/`
5. All loading attempts are logged for debugging

## Testing the Fix

### Build the Executable
```bash
# On Windows (from project root)
pyinstaller src/media_manager/media_manager.spec

# The executable will be in: dist/影藏·媒体管理器.exe
```

### Verify Translation Loading
1. Run the executable
2. Check the log file at `%USERPROFILE%\.media-manager\logs\app.log`
3. Look for these log entries:
   ```
   Installing translators for language: zh_CN (normalized: zh_CN)
   Running in PyInstaller mode: True
   PyInstaller _MEIPASS path: C:\Users\...\AppData\Local\Temp\_MEI123456
   Successfully loaded translator from ...
   Application translator loaded successfully
   ```

### Test Translation Switching
1. Launch the app
2. Go to Settings → Language
3. Select "简体中文" (Simplified Chinese)
4. Click Save and restart the app
5. Verify the UI is now in Chinese
6. Check the logs confirm translation loading

## Key Points

### Translation File Paths in PyInstaller
The spec file maps source paths to bundled paths:
```python
datas=[
    ('src/media_manager/resources/i18n/*.qm', 'resources/i18n'),
    #  ^--- source path                        ^--- bundled path (relative to _MEIPASS)
]
```

### Search Order in i18n.py
1. If `sys._MEIPASS` exists: `{_MEIPASS}/resources/i18n/`
2. Always try: `{package_dir}/resources/i18n/` (fallback for dev mode)

### Qt Translation Files
The spec file also includes Qt's own translation files:
```python
(translations_path + '/qtbase_zh_CN.qm', 'PySide6/translations'),
(translations_path + '/qt_zh_CN.qm', 'PySide6/translations'),
```

These provide translations for Qt's built-in widgets (buttons, dialogs, etc.).

## Debugging Tips

### Enable Console for Debugging
If translations still don't work, temporarily enable console output:
```python
# In spec file:
console=True,  # Change from False
```
This will show console output when the app runs.

### Check Bundled Files
After building, verify files are included:
```bash
# Extract the executable to inspect (Windows)
7z x "dist/影藏·媒体管理器.exe" -o"temp_extract"

# Check for translation files
dir temp_extract\resources\i18n
dir temp_extract\PySide6\translations
```

### Increase Logging Detail
The logging is already comprehensive, but you can make it even more verbose by checking individual .qm file properties:
```python
# In _load_app_translator(), add:
logger.info(f"  File size: {(path / expected_filename).stat().st_size} bytes")
```

## Verification Checklist

- [x] Spec file configured for --onefile build
- [x] Translation files included in spec datas
- [x] Qt translation files included in spec datas
- [x] i18n.py checks for sys._MEIPASS
- [x] i18n.py searches correct bundled paths
- [x] Comprehensive logging added
- [x] Logging initialized before translator loading
- [x] No circular import issues with logging

## Expected Log Output (Success Case)

```
2025-11-20 16:45:25,170 - media_manager.i18n - INFO - Installing translators for language: zh_CN (normalized: zh_CN)
2025-11-20 16:45:25,170 - media_manager.i18n - INFO - Running in PyInstaller mode: True
2025-11-20 16:45:25,170 - media_manager.i18n - INFO - PyInstaller _MEIPASS path: C:\Users\...\AppData\Local\Temp\_MEI123456
2025-11-20 16:45:25,170 - media_manager.i18n - INFO - QLocale name: zh_CN
2025-11-20 16:45:25,171 - media_manager.i18n - INFO - Loading app translator for locale: zh_CN, basename: media_manager
2025-11-20 16:45:25,171 - media_manager.i18n - INFO - PyInstaller mode detected, _MEIPASS: C:\Users\...\AppData\Local\Temp\_MEI123456
2025-11-20 16:45:25,171 - media_manager.i18n - INFO - Added PyInstaller candidate path: C:\Users\...\AppData\Local\Temp\_MEI123456\resources\i18n
2025-11-20 16:45:25,171 - media_manager.i18n - INFO - Checking candidate path: C:\Users\...\AppData\Local\Temp\_MEI123456\resources\i18n
2025-11-20 16:45:25,171 - media_manager.i18n - INFO -   Exists: True
2025-11-20 16:45:25,171 - media_manager.i18n - INFO -   Already seen: False
2025-11-20 16:45:25,171 - media_manager.i18n - INFO -   → Yielding this path
2025-11-20 16:45:25,171 - media_manager.i18n - INFO - Translation search paths: [WindowsPath('C:/Users/.../AppData/Local/Temp/_MEI123456/resources/i18n')]
2025-11-20 16:45:25,171 - media_manager.i18n - INFO - Trying to load translation from: C:\Users\...\AppData\Local\Temp\_MEI123456\resources\i18n
2025-11-20 16:45:25,172 - media_manager.i18n - INFO -   Path exists. QM files found: ['media_manager_zh_CN.qm']
2025-11-20 16:45:25,172 - media_manager.i18n - INFO -   Looking for file: media_manager_zh_CN.qm
2025-11-20 16:45:25,173 - media_manager.i18n - INFO -   ✓ Successfully loaded translator from C:\Users\...\AppData\Local\Temp\_MEI123456\resources\i18n
2025-11-20 16:45:25,173 - media_manager.i18n - INFO - Application translator loaded successfully
2025-11-20 16:45:25,173 - media_manager.i18n - INFO - Checking for bundled Qt translations at: C:\Users\...\AppData\Local\Temp\_MEI123456\PySide6\translations
2025-11-20 16:45:25,173 - media_manager.i18n - INFO -   Exists: True
2025-11-20 16:45:25,173 - media_manager.i18n - INFO - Using bundled Qt translations path: C:\Users\...\AppData\Local\Temp\_MEI123456\PySide6\translations
2025-11-20 16:45:25,173 - media_manager.i18n - INFO - Loading Qt translators from: C:\Users\...\AppData\Local\Temp\_MEI123456\PySide6\translations
2025-11-20 16:45:25,173 - media_manager.i18n - INFO -   Trying to load Qt translator: qtbase_zh_CN
2025-11-20 16:45:25,175 - media_manager.i18n - INFO -   ✓ Loaded qtbase_zh_CN
2025-11-20 16:45:25,175 - media_manager.i18n - INFO -   Trying to load Qt translator: qt_zh_CN
2025-11-20 16:45:25,178 - media_manager.i18n - INFO -   ✓ Loaded qt_zh_CN
2025-11-20 16:45:25,178 - media_manager.i18n - INFO - Loaded 2 Qt translators
2025-11-20 16:45:25,178 - media_manager.i18n - INFO - Total 3 translators installed
```

## Files Modified

1. `src/media_manager/media_manager.spec` - Fixed --onefile configuration
2. `src/media_manager/i18n.py` - Added comprehensive debug logging

## No Changes Required To

- Translation source files (`.ts` files) - Already correct
- Compiled translation files (`.qm` files) - Already exist and are correct
- Main application code - Already calls `install_translators()` correctly
- Settings system - Already saves/loads language preference correctly
