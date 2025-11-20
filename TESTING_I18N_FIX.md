# Testing the i18n Translation Fix

This document describes how to test that the zh_CN translation loading fix works correctly in both development and PyInstaller --onefile builds.

## Quick Test Summary

### 1. Development Mode Test (Source Code)
```bash
# Run the test script
python test_i18n.py

# Expected output should show:
# - "Application translator loaded successfully"
# - "Total 3 translators installed"
# - No errors or warnings
```

### 2. Simulated PyInstaller Test
```bash
# Run the PyInstaller simulation test
python test_pyinstaller_i18n.py

# Expected output should show:
# - "Running in PyInstaller mode: True"
# - "✓ Successfully loaded translator from /tmp/_MEI.../resources/i18n"
# - "✓ SUCCESS: 3 translators installed"
```

### 3. Actual PyInstaller Build Test
```bash
# Build the executable
pyinstaller src/media_manager/media_manager.spec

# Run the executable and check logs
# Windows: Check %USERPROFILE%\.media-manager\logs\app.log
# Linux/Mac: Check ~/.media-manager/logs/app.log

# The log should contain:
# - "Installing translators for language: zh_CN"
# - "Running in PyInstaller mode: True"
# - "Successfully loaded translator from ..."
# - "Total 3 translators installed"
```

## Detailed Testing Procedure

### Pre-Build Verification

1. **Verify translation file exists:**
   ```bash
   ls -lh src/media_manager/resources/i18n/media_manager_zh_CN.qm
   # Should show ~16KB file
   ```

2. **Verify spec file is correct:**
   ```bash
   cat src/media_manager/media_manager.spec | grep -A 5 "datas="
   # Should show:
   # ('src/media_manager/resources/i18n/*.qm', 'resources/i18n'),
   ```

3. **Run development tests:**
   ```bash
   python test_i18n.py
   python test_pyinstaller_i18n.py
   ```

### Build Procedure

1. **Clean previous builds:**
   ```bash
   rm -rf build/ dist/
   ```

2. **Build with PyInstaller:**
   ```bash
   pyinstaller src/media_manager/media_manager.spec
   ```

3. **Verify the executable was created:**
   ```bash
   # Windows
   ls -lh "dist/影藏·媒体管理器.exe"
   
   # Linux/Mac
   ls -lh "dist/影藏·媒体管理器"
   ```

### Post-Build Verification

1. **Extract and inspect bundled files (optional):**
   ```bash
   # Windows (requires 7-Zip)
   7z x "dist/影藏·媒体管理器.exe" -o"temp_extract"
   dir temp_extract\resources\i18n
   dir temp_extract\PySide6\translations
   
   # Linux/Mac (PyInstaller creates a bootloader, harder to extract)
   # Better to rely on runtime logging
   ```

2. **Test the executable:**
   
   a. **First run (default English):**
      - Launch the executable
      - Verify it starts without errors
      - UI should be in English
   
   b. **Switch to Chinese:**
      - Open Settings/Preferences
      - Find Language setting
      - Select "简体中文" (Simplified Chinese)
      - Save settings
      - Close the application
   
   c. **Second run (Chinese):**
      - Launch the executable again
      - UI should now be in Chinese
      - Check menus, buttons, dialogs are all in Chinese

3. **Check the logs:**
   
   **Windows:**
   ```powershell
   type %USERPROFILE%\.media-manager\logs\app.log | findstr /i "translator"
   ```
   
   **Linux/Mac:**
   ```bash
   grep -i "translator" ~/.media-manager/logs/app.log
   ```
   
   **Expected log entries:**
   ```
   Installing translators for language: zh_CN (normalized: zh_CN)
   Running in PyInstaller mode: True
   PyInstaller _MEIPASS path: C:\Users\...\AppData\Local\Temp\_MEI123456
   Loading app translator for locale: zh_CN, basename: media_manager
   ✓ Successfully loaded translator from ...
   Application translator loaded successfully
   ✓ Loaded qtbase_zh_CN
   ✓ Loaded qt_zh_CN
   Total 3 translators installed
   ```

## Troubleshooting

### Issue: UI Still in English After Switching to Chinese

**Check 1: Settings saved correctly?**
```bash
# Windows
type %USERPROFILE%\.media-manager\settings.json | findstr language

# Linux/Mac
grep language ~/.media-manager/settings.json
```
Should show: `"language": "zh_CN"`

**Check 2: Logs show translation loading?**
Look for these in the log file:
- `Installing translators for language: zh_CN`
- `Successfully loaded translator`

**Check 3: Translation file included in build?**
If using 7-Zip on Windows:
```bash
7z l "dist/影藏·媒体管理器.exe" | findstr /i "media_manager_zh_CN.qm"
```
Should show the file exists in the archive.

### Issue: "Path does not exist!" in Logs

This means the translation file wasn't bundled correctly.

**Fix:**
1. Verify spec file has correct datas entry
2. Verify source file exists before building
3. Clean and rebuild

### Issue: "Failed to load translator" Despite File Existing

This could mean:
1. File is corrupted - rebuild the .qm file:
   ```bash
   pyside6-lrelease translations/i18n/media_manager_zh_CN.ts -qm src/media_manager/resources/i18n/media_manager_zh_CN.qm
   ```

2. QLocale mismatch - check logs for the locale being used

3. File permissions - ensure .qm file is readable

### Issue: Qt Widgets Still in English

This means Qt translations (qtbase_zh_CN.qm, qt_zh_CN.qm) aren't loaded.

**Check:**
1. Spec file includes Qt translation files
2. `translations_path` variable is correct in spec file
3. Log shows `Loaded qtbase_zh_CN` and `Loaded qt_zh_CN`

## Validation Checklist

- [ ] Development mode test passes (`python test_i18n.py`)
- [ ] PyInstaller simulation test passes (`python test_pyinstaller_i18n.py`)
- [ ] Build completes without errors
- [ ] Executable launches without errors
- [ ] Settings allow changing language to "简体中文"
- [ ] After restart with zh_CN setting, UI displays in Chinese
- [ ] Logs show "Successfully loaded translator"
- [ ] Logs show "Total 3 translators installed"
- [ ] All major UI elements are translated (menus, buttons, dialogs)
- [ ] Qt standard widgets are translated (OK/Cancel buttons, etc.)
- [ ] No regression in other languages (EN, DE, FR)

## Test Coverage

The fix addresses translation loading for:
- ✅ Application-specific strings (media_manager_zh_CN.qm)
- ✅ Qt framework strings (qtbase_zh_CN.qm, qt_zh_CN.qm)
- ✅ PyInstaller --onefile builds
- ✅ Development mode (source code execution)
- ✅ Settings persistence (language preference saved)
- ✅ Dynamic language switching (change language without rebuild)

## Known Limitations

1. **Restart Required**: Language changes require an application restart to take effect. This is by design, as translators must be installed before UI widgets are created.

2. **Log File Only**: In --onefile builds with `console=False`, the debug logging only goes to the log file, not to a console window. To see console output during debugging, temporarily set `console=True` in the spec file.

3. **Temporary Directory**: PyInstaller extracts files to a temporary directory that's deleted when the app closes. This is normal and expected.

## Success Criteria

The fix is successful if:

1. **Log Confirmation**: Logs show translator loading succeeds
2. **Visual Confirmation**: UI displays in Chinese when zh_CN is selected
3. **Settings Persistence**: Language preference persists across restarts
4. **No Errors**: No error messages or warnings in logs related to translation loading
5. **Complete Translation**: All user-facing strings are translated (not just some)

## Additional Notes

- The logging is intentionally verbose to help diagnose issues in production builds
- Translation files are ~16KB each, minimal impact on executable size
- The fix supports all languages (en_US, de_DE, fr_FR, zh_CN) configured in LANGUAGE_MAP
- To add more languages, add .qm files to the resources/i18n directory and update the spec file datas
