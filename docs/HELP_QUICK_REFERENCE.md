# Help System Quick Reference

## User Guide

### Accessing Help

| Action | Method |
|--------|--------|
| Open Help Center | Press **F1** or select **Help → Help Center** |
| Context-Sensitive Help | Press **F1** while on any screen |
| Run Onboarding | Select **Help → Show Onboarding Wizard** |

### Navigation

| Key | Action |
|-----|--------|
| **F1** | Open help center |
| **Ctrl+F** | Focus search box |
| **Alt+Left** or **Back** | Navigate back |
| **Alt+Right** or **Forward** | Navigate forward |
| **Esc** | Close help center |

### Search Tips

- Search by topic title
- Search by keywords
- Search is case-insensitive
- Clear search to show all topics

## Developer Guide

### File Structure

```
docs/
  en/                      # English locale
    index.json            # Topic index
    *.html                # Help pages
  fr/                     # French locale (example)
    index.json
    *.html

src/media_manager/
  help_center_dialog.py   # Help center implementation
  onboarding_wizard.py    # Onboarding wizard

tests/
  test_help_center.py     # Tests
```

### Adding a New Help Topic

1. **Create HTML file** in `docs/en/`:
   ```html
   <!DOCTYPE html>
   <html>
   <head>
       <meta charset="UTF-8">
       <title>Your Topic</title>
       <style>
           body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; }
           h1 { color: #2c3e50; }
       </style>
   </head>
   <body>
       <h1>Your Topic</h1>
       <p>Content here...</p>
       <a href="other-topic.html">Link to other topic</a>
   </body>
   </html>
   ```

2. **Add to index.json**:
   ```json
   {
     "id": "your-topic",
     "title": "Your Topic",
     "file": "your-topic.html",
     "keywords": ["keyword1", "keyword2"]
   }
   ```

3. **Link from other pages**:
   ```html
   <a href="your-topic.html">Your Topic</a>
   ```

### Adding a Translation

1. **Create locale directory**:
   ```bash
   mkdir docs/fr
   ```

2. **Copy and translate files**:
   ```bash
   cp docs/en/index.json docs/fr/
   cp docs/en/*.html docs/fr/
   # Edit files to translate
   ```

3. **Update locale in index.json**:
   ```json
   {
     "locale": "fr",
     ...
   }
   ```

### Testing

```bash
# Validate help system
python3 validate_help.py

# Run tests
pytest tests/test_help_center.py -v

# Compile check
python3 -m py_compile src/media_manager/help_center_dialog.py
python3 -m py_compile src/media_manager/onboarding_wizard.py
```

### Context Mapping

Edit `main_window.py` to add/modify context mappings:

```python
topic_map = {
    0: "library-setup",      # Library tab
    1: "search",             # Search tab  
    2: "welcome",            # Dashboard tab
    3: "metadata-editing",   # Metadata editor tab
    4: "scanning",           # Matching/scan queue tab
}
```

## API Reference

### HelpCenterDialog

```python
from src.media_manager.help_center_dialog import HelpCenterDialog

# Open with default topic
dialog = HelpCenterDialog()
dialog.exec()

# Open with specific topic
dialog = HelpCenterDialog(initial_topic="library-setup")
dialog.exec()

# Show topic programmatically
dialog.show_topic("providers")

# Change locale
dialog.set_locale("fr")
```

### OnboardingWizard

```python
from src.media_manager.onboarding_wizard import OnboardingWizard

wizard = OnboardingWizard(settings)
if wizard.exec():
    # User completed wizard
    pass
```

### Settings

```python
from src.media_manager.settings import get_settings

settings = get_settings()

# Language settings
locale = settings.get_language()           # Get UI language
settings.set_language("fr")                # Set UI language

# Help locale
help_locale = settings.get_help_locale()   # Get help locale
settings.set_help_locale("fr")             # Set help locale

# Onboarding
completed = settings.get("onboarding_completed", False)
settings.set("onboarding_completed", True)
```

## Troubleshooting

### Help files not loading

**Problem**: Help center shows "Error" or blank content

**Solution**:
1. Check that `docs/en/` directory exists
2. Verify `index.json` is valid JSON
3. Ensure HTML files exist and are readable
4. Run `python3 validate_help.py`

### Onboarding not showing on first run

**Problem**: Onboarding wizard doesn't appear

**Solution**:
1. Delete or clear settings file
2. Or set `onboarding_completed` to `false` in settings
3. Restart application

### Context help shows wrong topic

**Problem**: F1 opens incorrect help topic

**Solution**:
1. Check topic mapping in `main_window.py`
2. Verify topic ID exists in `index.json`
3. Update `_open_context_help()` method

### Broken links in help

**Problem**: Clicking links shows "not found"

**Solution**:
1. Run `python3 validate_help.py` to check links
2. Verify target file exists in `docs/en/`
3. Ensure filename matches exactly (case-sensitive)
4. Check that target is listed in `index.json`

## Common Customizations

### Change help window size

Edit `help_center_dialog.py`:
```python
self.resize(900, 700)  # width, height
```

### Add custom CSS to help pages

Add to HTML `<style>` section:
```html
<style>
    body { font-family: Arial, sans-serif; }
    .custom-class { color: blue; }
</style>
```

### Modify onboarding pages

Edit `onboarding_wizard.py`:
- Modify existing pages: `WelcomePage`, `LibrarySetupPage`, etc.
- Add new pages: Create new `QWizardPage` subclass
- Change order: Adjust `addPage()` calls in `__init__`

### Skip onboarding on first run

In `main_window.py`, comment out:
```python
# self._check_first_run()
```

Or in settings, set:
```python
settings.set("onboarding_completed", True)
```

## Best Practices

### For Documentation Authors

1. **Keep it simple**: Use clear, concise language
2. **Add keywords**: Help users find topics via search
3. **Use examples**: Show practical usage
4. **Link related topics**: Help users discover related content
5. **Test links**: Run validation script regularly

### For Developers

1. **Validate changes**: Run `validate_help.py` after modifications
2. **Test navigation**: Ensure all links work
3. **Update tests**: Add tests for new topics
4. **Document context**: Update context mappings
5. **Maintain index**: Keep `index.json` synchronized

### For Translators

1. **Preserve structure**: Keep HTML structure intact
2. **Maintain links**: Don't change link targets
3. **Update keywords**: Translate keywords in index
4. **Test display**: Verify formatting in help center
5. **Keep consistent**: Use consistent terminology
