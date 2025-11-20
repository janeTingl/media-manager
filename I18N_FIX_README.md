# i18n Translation Fix for PyInstaller --onefile Builds

## Overview

This fix resolves the issue where Simplified Chinese (zh_CN) translations were not loading in PyInstaller --onefile builds, despite the translation files being present and correctly configured.

## Quick Start

### Verify the Fix Works

```bash
# 1. Run tests
python test_i18n.py
python test_pyinstaller_i18n.py

# 2. Build executable
pyinstaller src/media_manager/media_manager.spec

# 3. Test the executable
# - Launch the app
# - Go to Settings → Language
# - Select "简体中文"
# - Save and restart
# - Verify UI is in Chinese
```

## What Was Fixed

### Problem
- Language setting was saved correctly as "zh_CN"
- Translation file (media_manager_zh_CN.qm) was present (16KB)
- UI remained in English after restart in --onefile builds

### Root Causes
1. **Incorrect spec file**: Used `exclude_binaries=True` with COLLECT section (creates --onedir, not --onefile)
2. **No debugging**: No logging to diagnose translation loading failures
3. **Deprecated API**: Used `QLibraryInfo.location()` instead of `QLibraryInfo.path()`

### Solution
1. **Fixed spec file**: Proper --onefile configuration without COLLECT section
2. **Added logging**: Comprehensive debug logging throughout translation loading
3. **Updated API**: Use modern `QLibraryInfo.path()` API

## Changes Made

### Modified Files
1. `src/media_manager/i18n.py`
   - Added comprehensive debug logging
   - Updated to use `QLibraryInfo.path()`
   
2. `src/media_manager/media_manager.spec`
   - Fixed --onefile configuration
   - Updated to use `QLibraryInfo.path()`

### New Files
1. `test_i18n.py` - Development mode test
2. `test_pyinstaller_i18n.py` - PyInstaller simulation test
3. Documentation files (see below)

## Documentation

| File | Purpose |
|------|---------|
| `I18N_PYINSTALLER_FIX.md` | Technical explanation of the problem and solution |
| `TESTING_I18N_FIX.md` | Comprehensive testing procedures |
| `CHANGES_SUMMARY.md` | Detailed summary of all changes |
| `I18N_QUICK_REFERENCE.md` | Quick reference card for developers |
| `FIX_VERIFICATION_CHECKLIST.md` | Step-by-step verification checklist |
| `IMPLEMENTATION_SUMMARY.txt` | Plain text summary of implementation |
| `I18N_FIX_README.md` | This file |

## Testing

### Automated Tests

```bash
# Test in development mode
python test_i18n.py
# Expected: "Total 3 translators installed"

# Test PyInstaller simulation
python test_pyinstaller_i18n.py
# Expected: "✓ SUCCESS: 3 translators installed"
```

### Manual Testing

1. **Build the executable**
   ```bash
   pyinstaller src/media_manager/media_manager.spec
   ```

2. **Run and test language switching**
   - Launch `dist/影藏·媒体管理器.exe`
   - Change language to "简体中文"
   - Restart the app
   - Verify UI is in Chinese

3. **Check the logs**
   - Windows: `%USERPROFILE%\.media-manager\logs\app.log`
   - Linux/Mac: `~/.media-manager/logs/app.log`
   - Look for: "Total 3 translators installed"

## Expected Behavior

### User Perspective
1. Select "简体中文" in Settings
2. Save and restart
3. UI displays in Simplified Chinese
4. All menus, buttons, dialogs are translated

### Log Output (Success Case)
```
Installing translators for language: zh_CN (normalized: zh_CN)
Running in PyInstaller mode: True
PyInstaller _MEIPASS path: C:\Users\...\AppData\Local\Temp\_MEI123456
✓ Successfully loaded translator from ...
Application translator loaded successfully
✓ Loaded qtbase_zh_CN
✓ Loaded qt_zh_CN
Total 3 translators installed
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| UI still in English | Check log file for translation loading errors |
| "Path does not exist" in logs | Verify spec file datas configuration |
| "Failed to load translator" | Recompile .qm file with pyside6-lrelease |
| Qt widgets in English | Check Qt translation files are bundled |

For detailed troubleshooting, see `TESTING_I18N_FIX.md`.

## Technical Details

### Translation Loading Process

1. **Build Time**
   - PyInstaller bundles .qm files per spec file configuration
   - Files copied to: `{_MEIPASS}/resources/i18n/`

2. **Runtime**
   - App detects PyInstaller mode via `sys._MEIPASS`
   - Searches for translations in `{_MEIPASS}/resources/i18n/`
   - Loads application translations (media_manager_zh_CN.qm)
   - Loads Qt translations (qtbase_zh_CN.qm, qt_zh_CN.qm)
   - All steps are logged for debugging

### File Locations

| Mode | Path |
|------|------|
| Development | `src/media_manager/resources/i18n/media_manager_zh_CN.qm` |
| PyInstaller | `{_MEIPASS}/resources/i18n/media_manager_zh_CN.qm` |
| Qt translations | `{_MEIPASS}/PySide6/translations/*.qm` |

## Supported Languages

- `en_US` - English (default)
- `de_DE` - Deutsch (German)
- `fr_FR` - Français (French)
- `zh_CN` - 简体中文 (Simplified Chinese)

## Build Configuration

### Correct --onefile Spec

```python
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    name='影藏·媒体管理器',
    debug=False,
    console=False,
    # ... other options
)
# No COLLECT section for --onefile!
```

### Translation Files in Spec

```python
datas=[
    ('src/media_manager/resources/i18n/*.qm', 'resources/i18n'),
    (translations_path + '/qtbase_zh_CN.qm', 'PySide6/translations'),
    (translations_path + '/qt_zh_CN.qm', 'PySide6/translations'),
]
```

## Performance

- **Size impact**: Minimal (~16KB per language)
- **Startup time**: No noticeable delay
- **Runtime**: No impact (one-time loading)

## Compatibility

- **Python**: 3.8+
- **PySide6**: 6.5.0+
- **PyInstaller**: 5.0.0+
- **Platforms**: Windows, Linux, macOS

## Additional Resources

- [PySide6 Internationalization](https://doc.qt.io/qtforpython-6/overviews/internationalization.html)
- [PyInstaller Documentation](https://pyinstaller.org/en/stable/)
- [Qt Linguist Guide](https://doc.qt.io/qt-6/linguist-translators.html)

## Support

For issues or questions:
1. Check the log file: `~/.media-manager/logs/app.log`
2. Review `TESTING_I18N_FIX.md` for detailed troubleshooting
3. Use the verification checklist in `FIX_VERIFICATION_CHECKLIST.md`

## Summary

This fix ensures that:
- ✅ Translations load correctly in --onefile PyInstaller builds
- ✅ Comprehensive logging helps diagnose issues
- ✅ Modern Qt APIs are used (no deprecation warnings)
- ✅ All tests pass successfully
- ✅ No breaking changes or regressions
- ✅ Extensive documentation is provided

**Status**: ✅ Ready for deployment
