# i18n Quick Reference Card

## Quick Test Commands

```bash
# Test in development mode
python test_i18n.py

# Test PyInstaller simulation
python test_pyinstaller_i18n.py

# Build executable
pyinstaller src/media_manager/media_manager.spec

# Check logs (after running the app)
# Windows: type %USERPROFILE%\.media-manager\logs\app.log | findstr translator
# Linux/Mac: grep translator ~/.media-manager/logs/app.log
```

## Translation Workflow

### 1. Extract translatable strings from code
```bash
pyside6-lupdate src/media_manager/*.py src/media_manager/**/*.py \
  -ts translations/i18n/media_manager_zh_CN.ts
```

### 2. Edit translations (use Qt Linguist)
```bash
linguist translations/i18n/media_manager_zh_CN.ts
```

### 3. Compile to runtime format
```bash
pyside6-lrelease translations/i18n/media_manager_zh_CN.ts \
  -qm src/media_manager/resources/i18n/media_manager_zh_CN.qm
```

## File Locations

| File Type | Location |
|-----------|----------|
| Source translations (.ts) | `translations/i18n/media_manager_zh_CN.ts` |
| Compiled translations (.qm) | `src/media_manager/resources/i18n/media_manager_zh_CN.qm` |
| PyInstaller spec | `src/media_manager/media_manager.spec` |
| i18n code | `src/media_manager/i18n.py` |
| App logs | `~/.media-manager/logs/app.log` |

## PyInstaller Data Configuration

In the spec file, translations are bundled with:
```python
datas=[
    ('src/media_manager/resources/i18n/*.qm', 'resources/i18n'),
    (translations_path + '/qtbase_zh_CN.qm', 'PySide6/translations'),
    (translations_path + '/qt_zh_CN.qm', 'PySide6/translations'),
]
```

## Runtime Search Paths

1. **PyInstaller mode**: `{sys._MEIPASS}/resources/i18n/`
2. **Development mode**: `{package_dir}/resources/i18n/`

## Supported Languages

| Code | Language | Native Name |
|------|----------|-------------|
| en_US | English | English |
| de_DE | German | Deutsch |
| fr_FR | French | Français |
| zh_CN | Simplified Chinese | 简体中文 |

## Expected Log Output (Success)

```
INFO - Installing translators for language: zh_CN (normalized: zh_CN)
INFO - Running in PyInstaller mode: True
INFO - ✓ Successfully loaded translator from ...
INFO - Application translator loaded successfully
INFO - ✓ Loaded qtbase_zh_CN
INFO - ✓ Loaded qt_zh_CN
INFO - Total 3 translators installed
```

## Troubleshooting

| Problem | Check | Solution |
|---------|-------|----------|
| UI still in English | Log file | Verify translator loading succeeded |
| "Path does not exist" | spec file | Check datas configuration |
| "Failed to load" | .qm file | Recompile with pyside6-lrelease |
| Qt widgets in English | Qt translations | Check qtbase/qt .qm files bundled |

## Code Patterns

### Making strings translatable
```python
# In a QWidget subclass
self.button = QPushButton(self.tr("Click Me"))
self.label = QLabel(self.tr("Hello World"))
```

### Testing translation loading
```python
from media_manager.i18n import install_translators
from PySide6.QtWidgets import QApplication

app = QApplication([])
install_translators(app, "zh_CN")

# Check if successful
if hasattr(app, "_installed_translators"):
    print(f"✓ {len(app._installed_translators)} translators installed")
```

## Build Modes

| Mode | exclude_binaries | COLLECT section | Result |
|------|------------------|-----------------|--------|
| --onefile | False (or omit) | No | Single .exe |
| --onedir | True | Yes | Directory with .exe |

**Current configuration**: --onefile (single executable)

## Common Issues

### Issue: Deprecation warning about QLibraryInfo.location
**Solution**: Use `QLibraryInfo.path()` instead (already fixed)

### Issue: Translation works in dev but not in build
**Solution**: Check PyInstaller spec datas and verify files are bundled

### Issue: Console output not visible in --onefile
**Solution**: Set `console=True` in spec temporarily, or check log file

## API Reference

### Key Functions

```python
# Install translators for a language
install_translators(app: QApplication, language: str | None) -> None

# Get available language choices
get_language_choices() -> Sequence[tuple[str, str]]

# Normalize language code
normalize_language_code(language: str | None) -> str

# Get language display label
language_label(language: str) -> str
```

### Constants

```python
DEFAULT_LANGUAGE = "en_US"
SUPPORTED_LANGUAGES = ("en_US", "de_DE", "fr_FR", "zh_CN")
TRANSLATION_BASENAME = "media_manager"
```

## Testing Checklist

- [ ] `test_i18n.py` passes
- [ ] `test_pyinstaller_i18n.py` passes
- [ ] Build completes without errors
- [ ] Executable launches
- [ ] Can change language in settings
- [ ] UI changes to Chinese after restart
- [ ] Logs show "Total 3 translators installed"

## Environment Variables

```bash
# For headless testing (Linux)
export QT_QPA_PLATFORM=offscreen

# For debugging Qt
export QT_DEBUG_PLUGINS=1
```

## Additional Resources

- PySide6 i18n: https://doc.qt.io/qtforpython-6/overviews/internationalization.html
- PyInstaller: https://pyinstaller.org/en/stable/
- Qt Linguist: https://doc.qt.io/qt-6/linguist-translators.html
