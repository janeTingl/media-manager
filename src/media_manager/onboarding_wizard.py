"""First-run onboarding wizard for new users."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QCheckBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
    QWizard,
    QWizardPage,
)

from .logging import get_logger
from .persistence.repositories import LibraryRepository
from .settings import SettingsManager


class OnboardingWizard(QWizard):
    """First-run onboarding wizard to guide users through initial setup."""

    def __init__(self, settings: SettingsManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._settings = settings
        self._library_repo = LibraryRepository()

        self.setWindowTitle("Welcome to 影藏·媒体管理器")
        self.setWizardStyle(QWizard.WizardStyle.ModernStyle)
        self.setMinimumSize(700, 550)
        self.setOption(QWizard.WizardOption.NoBackButtonOnStartPage, True)

        # Add wizard pages
        self.addPage(WelcomePage(self))
        self.addPage(LibrarySetupPage(self._library_repo, self))
        self.addPage(ProviderSetupPage(self._settings, self))
        self.addPage(FeatureTourPage(self))
        self.addPage(CompletionPage(self))

        # Connect finish signal
        self.finished.connect(self._on_wizard_finished)

        self._logger.info("Onboarding wizard initialized")

    def _on_wizard_finished(self, result: int) -> None:
        """Handle wizard completion."""
        if result == QWizard.DialogCode.Accepted:
            # Mark onboarding as completed
            self._settings.set("onboarding_completed", True)
            self._settings.save_settings()
            self._logger.info("Onboarding completed successfully")


class WelcomePage(QWizardPage):
    """Welcome page with introduction to 影藏·媒体管理器."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setTitle("Welcome to 影藏·媒体管理器")
        self.setSubTitle("Let's get you set up in just a few steps")

        layout = QVBoxLayout()

        # Welcome message
        welcome_browser = QTextBrowser()
        welcome_browser.setMaximumHeight(400)
        welcome_browser.setOpenExternalLinks(True)
        welcome_browser.setHtml("""
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                h2 { color: #2c3e50; }
                ul { padding-left: 20px; }
                li { margin: 8px 0; }
                .highlight { color: #3498db; font-weight: bold; }
            </style>
        </head>
        <body>
            <h2>Welcome!</h2>
            <p>影藏·媒体管理器 helps you organize, manage, and track your media library with ease.</p>

            <h3>What You Can Do:</h3>
            <ul>
                <li>Automatically fetch metadata from online databases</li>
                <li>Organize media with libraries, tags, and collections</li>
                <li>Download posters and subtitles</li>
                <li>Batch edit multiple items at once</li>
                <li>Search and filter your media collection</li>
                <li>Export and backup your library data</li>
            </ul>

            <h3>This Setup Wizard Will Help You:</h3>
            <ul>
                <li><span class="highlight">Create your first library</span> - Point to your media files</li>
                <li><span class="highlight">Configure metadata providers</span> - Get API keys for automatic metadata</li>
                <li><span class="highlight">Learn about key features</span> - Quick tour of what's available</li>
            </ul>

            <p><strong>Ready to begin?</strong> Click <em>Next</em> to continue.</p>
        </body>
        </html>
        """)
        layout.addWidget(welcome_browser)

        layout.addStretch()
        self.setLayout(layout)


class LibrarySetupPage(QWizardPage):
    """Page for creating the first library."""

    def __init__(self, library_repo: LibraryRepository, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._library_repo = library_repo

        self.setTitle("Create Your First Library")
        self.setSubTitle("A library is a collection of media files you want to manage")

        layout = QVBoxLayout()

        # Info text
        info_label = QLabel(
            "Don't worry, you can create more libraries later and change these settings at any time."
        )
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addSpacing(20)

        # Library configuration
        config_group = QGroupBox("Library Configuration")
        config_layout = QFormLayout()

        # Library name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("e.g., My Movies, TV Shows")
        config_layout.addRow("Library Name:", self.name_edit)

        # Media type
        type_layout = QHBoxLayout()
        self.movie_radio = QRadioButton("Movies")
        self.movie_radio.setChecked(True)
        self.tv_radio = QRadioButton("TV Shows")
        type_layout.addWidget(self.movie_radio)
        type_layout.addWidget(self.tv_radio)
        type_layout.addStretch()
        config_layout.addRow("Media Type:", type_layout)

        # Root path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Select folder containing your media files...")
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self._browse_folder)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_button)
        config_layout.addRow("Media Folder:", path_layout)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Skip option
        layout.addSpacing(20)
        self.skip_checkbox = QCheckBox("Skip this step (I'll set up libraries later)")
        layout.addWidget(self.skip_checkbox)

        layout.addStretch()
        self.setLayout(layout)

        # Register fields for validation
        self.registerField("library_name", self.name_edit)
        self.registerField("library_path", self.path_edit)
        self.registerField("skip_library", self.skip_checkbox)

    def _browse_folder(self) -> None:
        """Open folder browser dialog."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Media Folder",
            str(Path.home()),
        )
        if folder:
            self.path_edit.setText(folder)

    def validatePage(self) -> bool:
        """Validate and create library if configured."""
        if self.skip_checkbox.isChecked():
            return True

        name = self.name_edit.text().strip()
        path = self.path_edit.text().strip()

        if not name or not path:
            return True  # Allow proceeding even without library

        # Create library
        try:
            media_type = "movie" if self.movie_radio.isChecked() else "tv"
            library = self._library_repo.create(name, media_type, path)
            if library:
                self._library_repo.set_default_library_id(library.id)
            return True
        except Exception as e:
            # Log error but don't block progression
            get_logger().get_logger(__name__).error(f"Failed to create library: {e}")
            return True


class ProviderSetupPage(QWizardPage):
    """Page for configuring metadata providers."""

    def __init__(self, settings: SettingsManager, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._settings = settings

        self.setTitle("Configure Metadata Providers")
        self.setSubTitle("API keys are needed to automatically fetch movie and TV show information")

        layout = QVBoxLayout()

        # Info text
        info_browser = QTextBrowser()
        info_browser.setMaximumHeight(150)
        info_browser.setOpenExternalLinks(True)
        info_browser.setHtml("""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.5;">
            <p>Metadata providers supply information like titles, descriptions, cast, ratings, and posters.</p>
            <p><strong>Getting API Keys (free for personal use):</strong></p>
            <ul style="margin-top: 5px;">
                <li><strong>TMDB:</strong> <a href="https://www.themoviedb.org/settings/api">themoviedb.org/settings/api</a></li>
                <li><strong>TVDB:</strong> <a href="https://thetvdb.com/dashboard/account/apikeys">thetvdb.com/dashboard/account/apikeys</a></li>
            </ul>
        </body>
        </html>
        """)
        layout.addWidget(info_browser)

        layout.addSpacing(10)

        # API key configuration
        keys_group = QGroupBox("API Keys")
        keys_layout = QFormLayout()

        self.tmdb_key_edit = QLineEdit()
        self.tmdb_key_edit.setPlaceholderText("Enter your TMDB API key (optional)")
        existing_tmdb = self._settings.get_tmdb_api_key()
        if existing_tmdb:
            self.tmdb_key_edit.setText(existing_tmdb)
        keys_layout.addRow("TMDB API Key:", self.tmdb_key_edit)

        self.tvdb_key_edit = QLineEdit()
        self.tvdb_key_edit.setPlaceholderText("Enter your TVDB API key (optional)")
        existing_tvdb = self._settings.get_tvdb_api_key()
        if existing_tvdb:
            self.tvdb_key_edit.setText(existing_tvdb)
        keys_layout.addRow("TVDB API Key:", self.tvdb_key_edit)

        keys_group.setLayout(keys_layout)
        layout.addWidget(keys_group)

        # Note about skipping
        layout.addSpacing(10)
        note_label = QLabel(
            "Note: You can skip this step and configure providers later in Preferences. "
            "Without API keys, you'll need to enter metadata manually."
        )
        note_label.setWordWrap(True)
        note_label.setStyleSheet("color: #7f8c8d; font-style: italic;")
        layout.addWidget(note_label)

        layout.addStretch()
        self.setLayout(layout)

        # Register fields
        self.registerField("tmdb_key", self.tmdb_key_edit)
        self.registerField("tvdb_key", self.tvdb_key_edit)

    def validatePage(self) -> bool:
        """Save API keys if provided."""
        tmdb_key = self.tmdb_key_edit.text().strip()
        tvdb_key = self.tvdb_key_edit.text().strip()

        if tmdb_key:
            self._settings.set_tmdb_api_key(tmdb_key)
        if tvdb_key:
            self._settings.set_tvdb_api_key(tvdb_key)

        if tmdb_key or tvdb_key:
            self._settings.save_settings()

        return True


class FeatureTourPage(QWizardPage):
    """Page with quick feature tour."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setTitle("Key Features Overview")
        self.setSubTitle("Here's what you can do with 影藏·媒体管理器")

        layout = QVBoxLayout()

        # Feature tour content
        tour_browser = QTextBrowser()
        tour_browser.setOpenExternalLinks(False)
        tour_browser.setHtml("""
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                h3 { color: #2c3e50; margin-top: 15px; }
                .feature { background: #ecf0f1; padding: 10px; margin: 10px 0; border-radius: 5px; }
                .feature-title { color: #3498db; font-weight: bold; }
            </style>
        </head>
        <body>
            <div class="feature">
                <div class="feature-title">📚 Libraries</div>
                <p>Organize different collections separately. Create libraries for movies, TV shows, or any category you want.</p>
            </div>

            <div class="feature">
                <div class="feature-title">🔍 Search & Filter</div>
                <p>Find media quickly with powerful search and filtering. Search by title, genre, year, cast, and more.</p>
            </div>

            <div class="feature">
                <div class="feature-title">✏️ Metadata Editor</div>
                <p>Edit and customize information about your media. Add your own descriptions, ratings, and details.</p>
            </div>

            <div class="feature">
                <div class="feature-title">⚡ Batch Operations</div>
                <p>Edit multiple items at once. Perfect for organizing large collections efficiently.</p>
            </div>

            <div class="feature">
                <div class="feature-title">🏷️ Tags & Favorites</div>
                <p>Create custom tags and mark favorites. Build collections that match your viewing preferences.</p>
            </div>

            <div class="feature">
                <div class="feature-title">💾 Import & Export</div>
                <p>Backup your library data or migrate to a new system. Your data is portable and safe.</p>
            </div>

            <p style="margin-top: 20px;"><strong>Tip:</strong> Press <strong>F1</strong> anytime to access context-sensitive help!</p>
        </body>
        </html>
        """)
        layout.addWidget(tour_browser)

        self.setLayout(layout)


class CompletionPage(QWizardPage):
    """Final completion page."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setTitle("Setup Complete!")
        self.setSubTitle("You're all set to start managing your media")

        layout = QVBoxLayout()

        # Completion message
        completion_browser = QTextBrowser()
        completion_browser.setOpenExternalLinks(False)
        completion_browser.setHtml("""
        <html>
        <head>
            <style>
                body { font-family: Arial, sans-serif; line-height: 1.6; }
                h2 { color: #27ae60; }
                .next-steps { background: #e8f5e9; padding: 15px; margin: 15px 0; border-radius: 5px; }
                ul { padding-left: 20px; }
                li { margin: 8px 0; }
            </style>
        </head>
        <body>
            <h2>🎉 You're Ready to Go!</h2>
            <p>影藏·媒体管理器 is now configured and ready to use.</p>

            <div class="next-steps">
                <h3>Next Steps:</h3>
                <ul>
                    <li>If you created a library, it will start scanning automatically</li>
                    <li>Review and confirm metadata matches in the Matching tab</li>
                    <li>Explore the different views: Grid, Table, and Dashboard</li>
                    <li>Try the search features to find specific media</li>
                    <li>Check out Preferences (Edit → Preferences) to customize settings</li>
                </ul>
            </div>

            <h3>Need Help?</h3>
            <ul>
                <li>Press <strong>F1</strong> for context-sensitive help</li>
                <li>Access <strong>Help → Help Center</strong> from the menu</li>
                <li>Check the troubleshooting guide if you encounter issues</li>
            </ul>

            <p><strong>Enjoy using 影藏·媒体管理器!</strong></p>
        </body>
        </html>
        """)
        layout.addWidget(completion_browser)

        self.setLayout(layout)
