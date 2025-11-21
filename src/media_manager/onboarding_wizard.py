"""First-run onboarding wizard for new users."""

from __future__ import annotations

from pathlib import Path

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

    def __init__(
        self, settings: SettingsManager, parent: QWidget | None = None
    ) -> None:
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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle("欢迎使用影藏·媒体管理器")
        self.setSubTitle("让我们通过几个步骤完成设置")

        layout = QVBoxLayout()

        # Welcome message
        welcome_browser = QTextBrowser()
        welcome_browser.setMaximumHeight(400)
        welcome_browser.setOpenExternalLinks(True)
        welcome_browser.setHtml(
            """
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
            <h2>欢迎！</h2>
            <p>影藏·媒体管理器帮助您轻松组织、管理和追踪您的媒体库。</p>

            <h3>您可以做什么：</h3>
            <ul>
                <li>从在线数据库自动获取元数据</li>
                <li>使用媒体库、标签和收藏来组织媒体</li>
                <li>下载海报和字幕</li>
                <li>一次批量编辑多个项目</li>
                <li>搜索和过滤您的媒体收藏</li>
                <li>导出和备份您的媒体库数据</li>
            </ul>

            <h3>本设置向导将帮助您：</h3>
            <ul>
                <li><span class="highlight">创建第一个媒体库</span> - 指向您的媒体文件</li>
                <li><span class="highlight">配置元数据提供商</span> - 获取 API 密钥以自动获取元数据</li>
                <li><span class="highlight">了解主要功能</span> - 快速浏览可用功能</li>
            </ul>

            <p><strong>准备好开始了吗？</strong>点击<em>下一步</em>继续。</p>
        </body>
        </html>
        """
        )
        layout.addWidget(welcome_browser)

        layout.addStretch()
        self.setLayout(layout)


class LibrarySetupPage(QWizardPage):
    """Page for creating the first library."""

    def __init__(
        self, library_repo: LibraryRepository, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._library_repo = library_repo

        self.setTitle("创建第一个媒体库")
        self.setSubTitle("媒体库是您要管理的媒体文件的集合")

        layout = QVBoxLayout()

        # Info text
        info_label = QLabel("不用担心，您可以稍后创建更多媒体库并随时更改这些设置。")
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        layout.addSpacing(20)

        # Library configuration
        config_group = QGroupBox("媒体库配置")
        config_layout = QFormLayout()

        # Library name
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("例如：我的电影、电视节目")
        config_layout.addRow("媒体库名称：", self.name_edit)

        # Media type
        type_layout = QHBoxLayout()
        self.movie_radio = QRadioButton("电影")
        self.movie_radio.setChecked(True)
        self.tv_radio = QRadioButton("电视节目")
        type_layout.addWidget(self.movie_radio)
        type_layout.addWidget(self.tv_radio)
        type_layout.addStretch()
        config_layout.addRow("媒体类型：", type_layout)

        # Root path
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("选择包含媒体文件的文件夹...")
        browse_button = QPushButton("浏览...")
        browse_button.clicked.connect(self._browse_folder)
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(browse_button)
        config_layout.addRow("媒体文件夹：", path_layout)

        config_group.setLayout(config_layout)
        layout.addWidget(config_group)

        # Skip option
        layout.addSpacing(20)
        self.skip_checkbox = QCheckBox("跳过此步骤（稍后设置媒体库）")
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
            "选择媒体文件夹",
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

    def __init__(
        self, settings: SettingsManager, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._settings = settings

        self.setTitle("配置元数据提供商")
        self.setSubTitle("需要 API 密钥来自动获取电影和电视节目信息")

        layout = QVBoxLayout()

        # Info text
        info_browser = QTextBrowser()
        info_browser.setMaximumHeight(150)
        info_browser.setOpenExternalLinks(True)
        info_browser.setHtml(
            """
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.5;">
            <p>元数据提供商提供标题、描述、演员、评分和海报等信息。</p>
            <p><strong>获取 API 密钥（个人使用免费）：</strong></p>
            <ul style="margin-top: 5px;">
                <li><strong>TMDB:</strong> <a href="https://www.themoviedb.org/settings/api">themoviedb.org/settings/api</a></li>
                <li><strong>TVDB:</strong> <a href="https://thetvdb.com/dashboard/account/apikeys">thetvdb.com/dashboard/account/apikeys</a></li>
            </ul>
        </body>
        </html>
        """
        )
        layout.addWidget(info_browser)

        layout.addSpacing(10)

        # API key configuration
        keys_group = QGroupBox("API 密钥")
        keys_layout = QFormLayout()

        self.tmdb_key_edit = QLineEdit()
        self.tmdb_key_edit.setPlaceholderText("输入您的 TMDB API 密钥（可选）")
        existing_tmdb = self._settings.get_tmdb_api_key()
        if existing_tmdb:
            self.tmdb_key_edit.setText(existing_tmdb)
        keys_layout.addRow("TMDB API 密钥：", self.tmdb_key_edit)

        self.tvdb_key_edit = QLineEdit()
        self.tvdb_key_edit.setPlaceholderText("输入您的 TVDB API 密钥（可选）")
        existing_tvdb = self._settings.get_tvdb_api_key()
        if existing_tvdb:
            self.tvdb_key_edit.setText(existing_tvdb)
        keys_layout.addRow("TVDB API 密钥：", self.tvdb_key_edit)

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

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle("主要功能概述")
        self.setSubTitle("以下是您可以使用影藏·媒体管理器做的事情")

        layout = QVBoxLayout()

        # Feature tour content
        tour_browser = QTextBrowser()
        tour_browser.setOpenExternalLinks(False)
        tour_browser.setHtml(
            """
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
                <div class="feature-title">📚 媒体库</div>
                <p>分别组织不同的收藏。为电影、电视节目或任何您想要的类别创建媒体库。</p>
            </div>

            <div class="feature">
                <div class="feature-title">🔍 搜索和过滤</div>
                <p>通过强大的搜索和过滤功能快速查找媒体。按标题、类型、年份、演员等搜索。</p>
            </div>

            <div class="feature">
                <div class="feature-title">✏️ 元数据编辑器</div>
                <p>编辑和自定义媒体信息。添加您自己的描述、评分和详细信息。</p>
            </div>

            <div class="feature">
                <div class="feature-title">⚡ 批量操作</div>
                <p>一次编辑多个项目。非常适合高效组织大型收藏。</p>
            </div>

            <div class="feature">
                <div class="feature-title">🏷️ 标签和收藏</div>
                <p>创建自定义标签并标记收藏。构建符合您观看偏好的收藏。</p>
            </div>

            <div class="feature">
                <div class="feature-title">💾 导入和导出</div>
                <p>备份您的媒体库数据或迁移到新系统。您的数据是可移植和安全的。</p>
            </div>

            <p style="margin-top: 20px;"><strong>提示：</strong>随时按<strong>F1</strong>访问上下文敏感帮助！</p>
        </body>
        </html>
        """
        )
        layout.addWidget(tour_browser)

        self.setLayout(layout)


class CompletionPage(QWizardPage):
    """Final completion page."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle("设置完成！")
        self.setSubTitle("您已准备好开始管理您的媒体")

        layout = QVBoxLayout()

        # Completion message
        completion_browser = QTextBrowser()
        completion_browser.setOpenExternalLinks(False)
        completion_browser.setHtml(
            """
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
            <h2>🎉 您已准备就绪！</h2>
            <p>影藏·媒体管理器现已配置并准备使用。</p>

            <div class="next-steps">
                <h3>下一步：</h3>
                <ul>
                    <li>如果您创建了媒体库，它将自动开始扫描</li>
                    <li>在匹配选项卡中查看并确认元数据匹配</li>
                    <li>探索不同的视图：网格、表格和仪表板</li>
                    <li>尝试搜索功能查找特定媒体</li>
                    <li>查看偏好设置（编辑 → 偏好设置）以自定义设置</li>
                </ul>
            </div>

            <h3>需要帮助？</h3>
            <ul>
                <li>按<strong>F1</strong>获取上下文敏感帮助</li>
                <li>从菜单访问<strong>帮助 → 帮助中心</strong></li>
                <li>如果遇到问题，请查看故障排除指南</li>
            </ul>

            <p><strong>享受使用影藏·媒体管理器！</strong></p>
        </body>
        </html>
        """
        )
        layout.addWidget(completion_browser)

        self.setLayout(layout)
