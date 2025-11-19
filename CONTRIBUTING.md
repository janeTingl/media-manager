# Contributing to 影藏·媒体管理器

Thank you for your interest in contributing to 影藏·媒体管理器! This document provides guidelines and instructions for contributing.

## Table of Contents

1. [Code of Conduct](#code-of-conduct)
2. [Getting Started](#getting-started)
3. [Development Workflow](#development-workflow)
4. [Code Style](#code-style)
5. [Testing](#testing)
6. [Documentation](#documentation)
7. [Commit Messages](#commit-messages)
8. [Pull Requests](#pull-requests)
9. [Reporting Issues](#reporting-issues)

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment for all contributors. We pledge to:

- Be respectful and inclusive
- Welcome diverse perspectives
- Focus on what is best for the community
- Be patient and supportive with others

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing opinions and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community

### Unacceptable Behavior

- Harassment, discrimination, or intimidation
- Insulting or derogatory comments
- Public or private harassment
- Publishing others' private information

## Getting Started

### Prerequisites

- Python 3.8 or higher
- Git
- Virtual environment (venv, poetry, etc.)

### Setting Up Your Development Environment

1. **Fork the repository**
   ```bash
   # On GitHub: Click "Fork" button
   ```

2. **Clone your fork**
   ```bash
   git clone https://github.com/your-username/media-manager.git
   cd media-manager
   ```

3. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. **Install development dependencies**
   ```bash
   pip install -e ".[dev]"
   ```

5. **Verify setup**
   ```bash
   pytest tests/test_smoke.py -v
   black --check src/ tests/
   ruff check src/ tests/
   mypy src/
   ```

## Development Workflow

### Creating a Feature Branch

1. **Update main branch**
   ```bash
   git checkout main
   git pull upstream main
   ```

2. **Create feature branch**
   ```bash
   git checkout -b feature/my-feature-name
   ```

3. **Push to your fork**
   ```bash
   git push origin feature/my-feature-name
   ```

### Making Changes

#### Before You Start

- Check existing issues and PRs
- Discuss large changes first
- Write tests alongside code

#### During Development

- Make focused, logical commits
- Test frequently
- Follow code style guidelines
- Update relevant documentation

#### Before Submitting

- Run all tests
- Format code with Black
- Check with Ruff
- Type check with MyPy
- Update documentation

## Code Style

### Python Style Guide

We follow PEP 8 with Black formatting:

```python
# Good
def process_video(path: Path) -> VideoMetadata:
    """Process a video file and extract metadata.
    
    Args:
        path: Path to video file
        
    Returns:
        VideoMetadata with extracted information
    """
    if not path.exists():
        raise FileNotFoundError(f"Video not found: {path}")
    
    metadata = parser.parse(path)
    return metadata


# Bad - Too many blank lines, inconsistent formatting
def process_video( path ):
    """Process video"""


    if not path.exists( ):
        raise FileNotFoundError( "Video not found: {0}".format(path) )
    
    
    
    metadata = parser.parse( path )
    return metadata
```

### Formatting

**Black Configuration:**
- Line length: 88 characters
- Use double quotes for strings
- Trailing commas in multi-line

**Run formatter:**
```bash
black src/ tests/
```

### Linting

**Ruff Configuration:**
- Check: E, W, F, I, B, C4, UP
- Ignore: E501 (handled by black), B008

**Run linter:**
```bash
ruff check src/ tests/
ruff check --fix src/ tests/  # Auto-fix
```

### Type Hints

**Always include type hints:**

```python
# Good
def scan(
    config: ScanConfig,
    callback: Optional[Callable[[VideoMetadata], None]] = None
) -> List[VideoMetadata]:
    """Scan directory with config."""
    results: List[VideoMetadata] = []
    # ...
    return results


# Bad - Missing type hints
def scan(config, callback=None):
    """Scan directory with config."""
    results = []
    # ...
    return results
```

**Run type checker:**
```bash
mypy src/
```

### Docstrings

Use NumPy-style docstrings:

```python
def extract_year(filename: str) -> Optional[int]:
    """Extract year from filename.
    
    Looks for 4-digit patterns matching years 1900-2099.
    
    Args:
        filename: The filename to parse
        
    Returns:
        Year as integer, or None if not found
        
    Raises:
        ValueError: If filename is empty
        
    Examples:
        >>> extract_year("Movie.2020.1080p.mkv")
        2020
        >>> extract_year("No Year Here.mkv")
        None
    """
    if not filename:
        raise ValueError("Filename cannot be empty")
    
    match = YEAR_PATTERN.search(filename)
    return int(match.group(1)) if match else None
```

### Naming Conventions

**Classes:**
```python
class VideoMetadata:      # PascalCase
class ScanEngine:
class MatchWorker:
```

**Functions/Methods:**
```python
def extract_metadata():   # snake_case
def scan_directory():
def process_video():
```

**Constants:**
```python
MAX_RETRIES = 3           # UPPER_SNAKE_CASE
DEFAULT_TIMEOUT = 30
IGNORED_DIRECTORIES = (...)
```

**Private Members:**
```python
def _internal_method():   # Leading underscore
self._private_variable = value
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_scanner.py

# Run with coverage
pytest --cov=src/media_manager

# Run with verbose output
pytest -v

# Run only fast tests
pytest -m "not slow"
```

### Writing Tests

```python
"""Tests for scanner module."""

import pytest
from pathlib import Path
from media_manager.scanner import Scanner, ScanConfig
from media_manager.models import MediaType


class TestScanner:
    """Test suite for Scanner class."""
    
    def test_parse_movie(self):
        """Test parsing movie filename."""
        scanner = Scanner()
        path = Path("Inception.2010.1080p.mkv")
        
        result = scanner.parse_video(path)
        
        assert result.title == "Inception"
        assert result.year == 2010
        assert result.media_type == MediaType.MOVIE
    
    def test_parse_episode(self):
        """Test parsing TV episode filename."""
        scanner = Scanner()
        path = Path("Breaking Bad - S05E16 - Felina.mkv")
        
        result = scanner.parse_video(path)
        
        assert result.title == "Felina"
        assert result.season == 5
        assert result.episode == 16
        assert result.media_type == MediaType.TV
    
    def test_parse_invalid_path(self):
        """Test parsing invalid path raises error."""
        scanner = Scanner()
        
        with pytest.raises(Exception):
            scanner.parse_video(Path(""))


class TestScanConfig:
    """Test suite for ScanConfig."""
    
    def test_default_config(self):
        """Test creating default config."""
        config = ScanConfig(root_paths=[Path("/media")])
        
        assert len(config.root_paths) == 1
        assert config.root_paths[0] == Path("/media")
        assert ".mkv" in config.video_extensions
    
    def test_custom_extensions(self):
        """Test config with custom extensions."""
        config = ScanConfig(
            root_paths=[Path("/media")],
            video_extensions=(".mkv", ".mp4")
        )
        
        assert len(config.video_extensions) == 2
        assert ".avi" not in config.video_extensions
```

### Test Structure

```
tests/
├── __init__.py
├── conftest.py                    # Shared fixtures
├── test_smoke.py                  # Basic functionality
├── test_scanner.py                # Scanner tests
├── test_scan_engine.py            # ScanEngine tests
├── test_settings.py               # Settings tests
├── test_match_integration.py      # Matching workflow
├── test_poster_downloader.py      # Poster system
├── test_poster_integration.py     # Poster workflow
├── test_poster_settings.py        # Poster UI
├── test_subtitle_provider.py      # Subtitle provider
├── test_subtitle_downloader.py    # Subtitle system
├── test_subtitle_integration.py   # Subtitle workflow
├── test_nfo_exporter.py           # NFO generation
├── test_nfo_integration.py        # NFO workflow
├── test_library_postprocessor.py  # Post-processing
└── test_matching_basic.py         # Basic matching
```

### Test Best Practices

1. **Descriptive names:**
   ```python
   def test_scan_finds_movie_files():  # Good
   def test_scan():                     # Bad
   ```

2. **Arrange-Act-Assert pattern:**
   ```python
   def test_process_video(self):
       # Arrange
       scanner = Scanner()
       path = Path("movie.mkv")
       
       # Act
       result = scanner.parse_video(path)
       
       # Assert
       assert result.title == "movie"
   ```

3. **Mock external dependencies:**
   ```python
   @pytest.fixture
   def mock_api():
       with patch('requests.get') as mock_get:
           mock_get.return_value.json.return_value = {...}
           yield mock_get
   ```

4. **Use fixtures for setup:**
   ```python
   @pytest.fixture
   def scanner():
       return Scanner()
   
   def test_parse(scanner):
       result = scanner.parse_video(Path("test.mkv"))
       assert result is not None
   ```

## Documentation

### Updating Documentation

When adding features, update relevant docs:

- **README.md**: Project overview
- **API.md**: API reference
- **ARCHITECTURE.md**: Design changes
- **USAGE.md**: User-facing features
- **Code docstrings**: Implementation details

### Writing Documentation

- Use clear, concise language
- Include code examples
- Document edge cases
- Explain design decisions

```markdown
## Feature Name

Brief description of the feature.

### Usage

```python
# Code example
```

### Configuration

List configuration options.

### Known Limitations

Document any limitations.
```

## Commit Messages

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Type

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation
- **style**: Formatting, no code change
- **refactor**: Code refactor
- **perf**: Performance improvement
- **test**: Test addition/update
- **ci**: CI/CD changes
- **chore**: Maintenance

### Scope

Component affected:
- scanner
- matching
- ui
- settings
- poster
- subtitle
- nfo

### Subject

- Use imperative mood ("add" not "added")
- Don't capitalize first letter
- No period at the end
- Limit to 50 characters

### Body

- Explain what and why, not how
- Wrap at 72 characters
- Use bullet points for multiple changes

### Footer

Reference issues:
```
Closes #123
Relates to #456
```

### Examples

```
feat(scanner): add episode number parsing

Implement regex patterns for common TV episode formats:
- S01E01 format
- 1x01 format
- Full date-based naming

Closes #42

---

fix(matching): handle missing metadata gracefully

Return empty match instead of raising exception when
title is missing from API response.

Relates to #78

---

docs(api): update API reference for new endpoints

Add documentation for the new poster_urls field in
SearchResult and update examples.
```

## Pull Requests

### Before Submitting

1. **Check your changes:**
   ```bash
   pytest                    # All tests pass
   black --check src/ tests/ # Formatting
   ruff check src/ tests/    # Linting
   mypy src/                 # Type checking
   ```

2. **Update documentation** if needed

3. **Rebase on main:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

4. **Push to your fork:**
   ```bash
   git push origin feature/my-feature-name
   ```

### PR Template

```markdown
## Description

Brief description of changes.

## Type of Change

- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Related Issues

Closes #123

## Testing

Describe testing performed:
- [ ] Unit tests added
- [ ] Integration tests added
- [ ] Manual testing completed

## Checklist

- [ ] Code follows style guidelines
- [ ] Docstrings updated
- [ ] Tests pass locally
- [ ] No new warnings generated
- [ ] Documentation updated
```

### PR Guidelines

- Keep PRs focused and single-purpose
- Include tests for all changes
- Update docs as needed
- Respond to review feedback
- Squash commits before merge if requested

## Reporting Issues

### Before Reporting

- Check existing issues
- Review documentation
- Try latest development version
- Verify reproduction steps

### Issue Template

```markdown
## Description

Clear description of the issue.

## Steps to Reproduce

1. First step
2. Second step
3. ...

## Expected Behavior

What should happen.

## Actual Behavior

What actually happens.

## Screenshots

If applicable, include screenshots.

## Environment

- OS: [e.g., Ubuntu 22.04]
- Python: [e.g., 3.10.5]
- Version: [e.g., 0.1.0]

## Logs

Include relevant log excerpts from `~/.media-manager/logs/app.log`

## Additional Context

Any other relevant information.
```

### Issue Types

- **Bug Report**: Describe unexpected behavior
- **Feature Request**: Suggest new functionality
- **Enhancement**: Improve existing feature
- **Documentation**: Documentation issues
- **Question**: How-to and usage questions

## Development Tools

### Setup IDE

**VS Code:**
```json
{
  "[python]": {
    "editor.defaultFormatter": "ms-python.python",
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
      "source.organizeImports": true
    }
  },
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": false,
  "python.linting.flake8Enabled": false
}
```

**PyCharm:**
- Enable Black formatter
- Enable Ruff as external tool
- Configure pytest as test runner

### Pre-commit Hook

Setup auto-formatting on commit:

```bash
pip install pre-commit
pre-commit install

# Create .pre-commit-config.yaml
```

## Recognition

Contributors will be recognized in:
- README.md contributors section
- Release notes
- GitHub contributors graph

## Questions?

- Open an issue with [question] label
- Check existing discussions
- Read documentation thoroughly

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

Thank you for contributing to 影藏·媒体管理器! 🎉
