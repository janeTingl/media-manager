# 影藏·媒体管理器 - Documentation Index

Welcome to the comprehensive documentation for the 影藏·媒体管理器 project! This guide will help you find the information you need.

## 📖 Documentation Overview

### For Different Audiences

#### 👤 End Users
- **[QUICK_START.md](QUICK_START.md)** - Get started in 5 minutes
- **[USAGE.md](USAGE.md)** - Comprehensive user guide
- **[FAQ.md](#faq-section)** - Common questions (see FAQ section below)

#### 👨‍💻 Developers
- **[API.md](API.md)** - Complete API reference
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Development guidelines
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System design and patterns

#### 🏗️ System Administrators
- **[INSTALLATION.md](INSTALLATION.md)** - Setup and deployment
- **[PROJECT_SUMMARY.md](PROJECT_SUMMARY.md)** - Technical overview
- **[.env.example](.env.example)** - Configuration template

#### 📚 Everyone
- **[README.md](README.md)** - Project overview
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and features

## 📋 Document Structure

### Core Documentation

```
Core Documentation
├── README.md (309 lines)
│   └── Project overview, features, basic setup
│
├── QUICK_START.md (215 lines)
│   └── 5-minute quick start guide
│
├── INSTALLATION.md (320 lines)
│   ├── System requirements
│   ├── Installation methods (pip, source, poetry)
│   ├── Configuration
│   └── Troubleshooting
│
├── USAGE.md (450 lines)
│   ├── Getting started
│   ├── Main interface
│   ├── Scanning media
│   ├── Matching workflow
│   ├── Processing options
│   ├── Preferences
│   ├── Advanced usage
│   ├── Troubleshooting
│   ├── Keyboard shortcuts
│   └── Tips & best practices
│
├── API.md (650+ lines)
│   ├── Data models
│   ├── Scanning API
│   ├── Matching API
│   ├── Media processing
│   ├── Settings management
│   ├── Background workers
│   ├── Logging
│   ├── Service registry
│   └── Code examples
│
├── ARCHITECTURE.md (700+ lines)
│   ├── Architecture overview
│   ├── Core modules
│   ├── Data flow
│   ├── Design patterns
│   ├── Component relationships
│   ├── Threading model
│   ├── Settings management
│   └── Extensibility
│
├── CONTRIBUTING.md (400+ lines)
│   ├── Code of conduct
│   ├── Getting started
│   ├── Development workflow
│   ├── Code style
│   ├── Testing guidelines
│   ├── Documentation
│   ├── Commit messages
│   ├── Pull requests
│   └── Issue reporting
│
├── PROJECT_SUMMARY.md (400+ lines)
│   ├── Executive summary
│   ├── Feature matrix
│   ├── Technology stack
│   ├── Project structure
│   ├── Data models
│   ├── Architectural patterns
│   ├── Configuration
│   ├── Performance characteristics
│   ├── API integration status
│   ├── Testing strategy
│   ├── Security considerations
│   ├── Known limitations
│   └── Roadmap
│
├── CHANGELOG.md (280 lines)
│   ├── Current version features
│   ├── Version history
│   ├── Breaking changes
│   ├── Known issues
│   └── Future roadmap
│
└── DOCUMENTATION.md (this file)
    └── Complete documentation index
```

### Feature Documentation

```
Feature-Specific Documentation
├── MATCHING_UI.md
│   └── Matching and search workflow
│
├── POSTER_DOWNLOADING_IMPLEMENTATION.md
│   └── Poster management system
│
├── SUBTITLE_MANAGEMENT_IMPLEMENTATION.md
│   └── Subtitle handling system
│
└── NFO_EXPORTER_IMPLEMENTATION.md
    └── Metadata export system
```

### Configuration

```
Configuration Files
├── pyproject.toml
│   └── Project metadata and dependencies
│
├── .env.example
│   └── Environment variables template
│
├── .gitignore
│   └── Git ignore rules
│
└── Makefile
    └── Common development tasks
```

## 🗺️ Navigation by Task

### Getting Started

1. **First time user?**
   - Start: [QUICK_START.md](QUICK_START.md)
   - Then: [USAGE.md](USAGE.md)

2. **Installing application?**
   - Read: [INSTALLATION.md](INSTALLATION.md)
   - Reference: [.env.example](.env.example)

3. **Want to use the app?**
   - Guide: [USAGE.md](USAGE.md)
   - Shortcuts: [USAGE.md#keyboard-shortcuts](USAGE.md)
   - Tips: [USAGE.md#tips-and-best-practices](USAGE.md)

### Development

1. **Want to contribute?**
   - Start: [CONTRIBUTING.md](CONTRIBUTING.md)
   - Code style: [CONTRIBUTING.md#code-style](CONTRIBUTING.md)
   - Tests: [CONTRIBUTING.md#testing](CONTRIBUTING.md)

2. **Need API reference?**
   - Go to: [API.md](API.md)
   - Examples: [API.md#complete-example](API.md)

3. **Want to understand design?**
   - Read: [ARCHITECTURE.md](ARCHITECTURE.md)
   - Patterns: [ARCHITECTURE.md#design-patterns](ARCHITECTURE.md)
   - Threading: [ARCHITECTURE.md#threading-model](ARCHITECTURE.md)

4. **Extending the system?**
   - Section: [ARCHITECTURE.md#extensibility](ARCHITECTURE.md)

### Features

1. **Poster downloading?**
   - See: [POSTER_DOWNLOADING_IMPLEMENTATION.md](POSTER_DOWNLOADING_IMPLEMENTATION.md)

2. **Subtitle management?**
   - See: [SUBTITLE_MANAGEMENT_IMPLEMENTATION.md](SUBTITLE_MANAGEMENT_IMPLEMENTATION.md)

3. **Metadata export?**
   - See: [NFO_EXPORTER_IMPLEMENTATION.md](NFO_EXPORTER_IMPLEMENTATION.md)

4. **Matching workflow?**
   - See: [MATCHING_UI.md](MATCHING_UI.md)

### Problems & Solutions

1. **Application issues?**
   - Section: [USAGE.md#troubleshooting](USAGE.md)
   - Or: [INSTALLATION.md#troubleshooting](INSTALLATION.md)

2. **Installation problems?**
   - Section: [INSTALLATION.md#troubleshooting](INSTALLATION.md)

3. **Development questions?**
   - Section: [CONTRIBUTING.md](#contributing)

## 📊 Content Statistics

| Document | Lines | Focus |
|----------|-------|-------|
| README.md | 309 | Overview |
| QUICK_START.md | 215 | Quick guide |
| INSTALLATION.md | 320 | Setup |
| USAGE.md | 450 | User guide |
| API.md | 650+ | Developer reference |
| ARCHITECTURE.md | 700+ | System design |
| CONTRIBUTING.md | 400+ | Development |
| PROJECT_SUMMARY.md | 400+ | Technical summary |
| CHANGELOG.md | 280 | Version history |
| **TOTAL** | **~3,800** | **Complete** |

## 🔑 Key Concepts

### Core Concepts to Understand

1. **Scanning** - Finding and parsing video files
2. **Matching** - Connecting videos to external databases
3. **Processing** - Renaming, organizing, adding metadata
4. **Posters** - Downloading and caching artwork
5. **Subtitles** - Managing subtitle files
6. **NFO** - Generating XML metadata

### Architecture Concepts

1. **Signals/Slots** - Qt's event system
2. **Threading** - Background worker threads
3. **Dependency Injection** - Service registry pattern
4. **Dataclasses** - Type-safe data models
5. **Post-processing** - Coordinated enhancement pipeline

## 🛠️ Development Resources

### Code Quality
- Python style: PEP 8 + Black
- Linting: Ruff
- Type checking: MyPy (strict)
- Testing: Pytest + Pytest-Qt

### Important Files
- `src/media_manager/models.py` - Core data models
- `src/media_manager/scanner.py` - File scanning logic
- `src/media_manager/workers.py` - Background workers
- `src/media_manager/main_window.py` - GUI layout
- `tests/` - Test suite (44+ tests)

### Development Commands
```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Test
pytest

# Build
pip install -e ".[dev]"
```

## 📞 Getting Help

### Documentation
1. Check relevant section in this index
2. Read the specific documentation file
3. Check code examples in API.md

### Logs
```bash
# View logs
cat ~/.media-manager/logs/app.log

# Watch logs
tail -f ~/.media-manager/logs/app.log
```

### Community
- GitHub Issues - Report bugs
- GitHub Discussions - Ask questions
- Code Examples - See tests/ directory

## 📈 Documentation Roadmap

### Current Version (Complete)
- ✓ Quick start guide
- ✓ Installation guide
- ✓ User guide
- ✓ API reference
- ✓ Architecture guide
- ✓ Contributing guide
- ✓ Project summary
- ✓ Changelog
- ✓ Documentation index
- ✓ Configuration template

### Planned Additions
- [ ] Video tutorials
- [ ] API integration guide
- [ ] Plugin development guide
- [ ] Deployment guide
- [ ] Performance tuning guide
- [ ] Troubleshooting guide (expanded)
- [ ] FAQ section (expanded)

## 🎯 Quick Links

### Essential Documents
| Document | Purpose |
|----------|---------|
| [README.md](README.md) | Start here |
| [QUICK_START.md](QUICK_START.md) | Get running in 5 minutes |
| [USAGE.md](USAGE.md) | Learn to use the app |
| [INSTALLATION.md](INSTALLATION.md) | Install the application |
| [API.md](API.md) | Developer reference |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribute to the project |

### Deep Dives
| Document | Topic |
|----------|-------|
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Complete overview |
| [CHANGELOG.md](CHANGELOG.md) | Version history |

### Feature Guides
| Document | Feature |
|----------|---------|
| [MATCHING_UI.md](MATCHING_UI.md) | Matching & search |
| [POSTER_DOWNLOADING_IMPLEMENTATION.md](POSTER_DOWNLOADING_IMPLEMENTATION.md) | Posters |
| [SUBTITLE_MANAGEMENT_IMPLEMENTATION.md](SUBTITLE_MANAGEMENT_IMPLEMENTATION.md) | Subtitles |
| [NFO_EXPORTER_IMPLEMENTATION.md](NFO_EXPORTER_IMPLEMENTATION.md) | Metadata |

## 📝 Document Maintenance

### Last Updated
- **README.md**: 2024-11-09
- **INSTALLATION.md**: 2024-11-09
- **USAGE.md**: 2024-11-09
- **API.md**: 2024-11-09
- **ARCHITECTURE.md**: 2024-11-09
- **CONTRIBUTING.md**: 2024-11-09
- **PROJECT_SUMMARY.md**: 2024-11-09
- **CHANGELOG.md**: 2024-11-09
- **QUICK_START.md**: 2024-11-09
- **DOCUMENTATION.md**: 2024-11-09

### Documentation Standards

All documentation follows:
- Clear, concise writing
- Practical examples
- Proper formatting (Markdown)
- Up-to-date information
- Cross-references

## 🚀 Getting Started Path

```
Start Here ↓
  │
  ├─→ Read README.md (5 min)
  │
  ├─→ Follow QUICK_START.md (5 min)
  │
  ├─→ Explore USAGE.md (30 min)
  │
  └─→ Choose your path:
      │
      ├─→ Want to develop? → CONTRIBUTING.md → API.md
      │
      ├─→ Want to understand? → ARCHITECTURE.md
      │
      └─→ Want more info? → PROJECT_SUMMARY.md
```

---

**Happy using 影藏·媒体管理器!** 

For specific questions, find the relevant document in this index and dive in. If you can't find what you need, check the code examples in the `tests/` directory or open an issue on GitHub.
