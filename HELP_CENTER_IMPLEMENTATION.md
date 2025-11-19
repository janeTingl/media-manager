# Help Center and Onboarding Implementation

This document describes the implementation of the embedded help system and first-run onboarding wizard.

## Overview

The help system provides:
- **Help Center Dialog**: Searchable documentation with navigation
- **Onboarding Wizard**: First-run setup guide
- **Context-Sensitive Help**: F1 key opens relevant help topics
- **Localization Support**: Multi-language help content

## Components

### 1. HelpCenterDialog (`help_center_dialog.py`)

A dialog that displays HTML-based help documentation with:
- **Topic Navigation**: Left sidebar with topic list
- **Content Browser**: HTML content display with QTextBrowser
- **Search Functionality**: Filter topics by keywords
- **History Navigation**: Back/forward buttons and keyboard shortcuts
- **Localization**: Supports multiple locales (defaults to `en`)

**Features:**
- Press `F1` to open help center from anywhere
- Search topics by title or keywords
- Navigate between topics with back/forward buttons
- Click internal links to jump between topics
- Keyboard shortcuts: `Ctrl+F` for search, `Alt+Left/Right` for navigation

### 2. OnboardingWizard (`onboarding_wizard.py`)

A multi-page wizard for first-run setup:

**Pages:**
1. **Welcome**: Introduction and overview
2. **Library Setup**: Create first library (optional)
3. **Provider Setup**: Configure TMDB/TVDB API keys
4. **Feature Tour**: Quick overview of key features
5. **Completion**: Next steps and help resources

**Features:**
- Only shows on first run (can be triggered manually from Help menu)
- Stores completion state in settings
- Allows skipping optional steps
- Links to help documentation

### 3. Documentation Structure (`docs/`)

Help content is organized by locale:

```
docs/
  en/
    index.json          # Topic index with metadata
    welcome.html        # Welcome page
    quick-start.html    # Quick start guide
    library-setup.html  # Library setup guide
    providers.html      # Provider configuration
    troubleshooting.html # Common issues
    ... (other topics)
  zh-CN/
    index.json          # 简体中文主题索引
    *.html              # Translated help topics (mirrors en/ structure)
```

**index.json structure:**
```json
{
  "title": "Media Manager Help",
  "version": "1.0",
  "locale": "en",
  "topics": [
    {
      "id": "welcome",
      "title": "Welcome",
      "file": "welcome.html",
      "keywords": ["introduction", "overview"]
    }
  ]
}
```

### 4. Settings Integration

New settings methods in `SettingsManager`:
- `get_language()` / `set_language()`: UI language
- `get_help_locale()` / `set_help_locale()`: Help documentation locale
- `get("onboarding_completed")`: Track onboarding completion

### 5. MainWindow Integration

**Menu Integration:**
- `Help → Help Center (F1)`: Opens help center
- `Help → Show Onboarding Wizard`: Re-runs onboarding

**Context-Sensitive Help:**
- Press `F1` to open help with relevant topic based on current tab
- Topic mapping based on active view

**First-Run Detection:**
- Checks `onboarding_completed` setting on startup
- Shows onboarding wizard if not completed
- Uses QTimer to delay display until window is fully loaded

## Usage

### Opening Help Center

```python
from src.media_manager.help_center_dialog import HelpCenterDialog

# Open with default (welcome) topic
dialog = HelpCenterDialog()
dialog.exec()

# Open with specific topic
dialog = HelpCenterDialog(initial_topic="library-setup")
dialog.exec()
```

### Triggering Onboarding

```python
from src.media_manager.onboarding_wizard import OnboardingWizard

wizard = OnboardingWizard(settings)
if wizard.exec():
    # User completed onboarding
    pass
```

### Adding New Help Topics

1. Create HTML file in `docs/zh-CN/`
2. Add topic entry to `docs/zh-CN/index.json`:
   ```json
   {
     "id": "my-topic",
     "title": "My Topic Title",
     "file": "my-topic.html",
     "keywords": ["keyword1", "keyword2"]
   }
   ```
3. Link to topic from other pages: `<a href="my-topic.html">Link text</a>`

### Adding Localization

1. Create locale directory: `docs/fr/` (for French)
2. Copy `index.json` and translate
3. Translate all HTML files
4. Set locale in settings: `settings.set_help_locale("fr")`

## Testing

Tests are in `tests/test_help_center.py`:

- **Help Center Tests**:
  - Dialog initialization
  - Topic loading and navigation
  - Search filtering
  - File existence and link validation
  
- **Onboarding Tests**:
  - Wizard initialization
  - Page navigation
  - Settings persistence
  - Skip functionality

- **Integration Tests**:
  - HTML validation
  - Index structure validation
  - Link integrity checking

Run tests:
```bash
pytest tests/test_help_center.py -v
```

## File Structure

```
src/media_manager/
  help_center_dialog.py      # Help center dialog
  onboarding_wizard.py        # Onboarding wizard
  main_window.py              # Integration with main window
  settings.py                 # Settings for locale/onboarding

docs/
  en/                         # English help content
    index.json                # Topic index
    welcome.html              # Help pages
    quick-start.html
    ... (other topics)

tests/
  test_help_center.py         # Tests for help system
```

## Future Enhancements

Possible improvements:
- PDF export of help documentation
- Full-text search within content
- Bookmarks/favorites for topics
- Video tutorials embedded in help
- Community-contributed translations
- Help content versioning
- Offline help package generation
- Context menu "What's This?" mode
- Interactive tours with highlights
