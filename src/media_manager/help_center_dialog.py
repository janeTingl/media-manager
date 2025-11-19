"""Help Center Dialog with searchable documentation and navigation."""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import Qt, QUrl, Signal
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSplitter,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from .logging import get_logger
from .settings import get_settings


class HelpCenterDialog(QDialog):
    """Dialog for displaying help documentation with navigation and search."""

    DEFAULT_LOCALE = "en"

    topic_changed = Signal(str)  # topic_id

    def __init__(self, parent: Optional[QWidget] = None, initial_topic: str = "welcome") -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._docs_path = Path(__file__).parent.parent.parent / "docs"

        # Get locale from settings
        settings = get_settings()
        self._current_locale = settings.get_help_locale()
        self._strings = self._get_locale_strings(self._current_locale)

        self._topics = []
        self._history = []
        self._history_index = -1

        self.resize(900, 700)

        self._setup_ui()
        self._apply_locale_strings()

        if not self._load_help_index() and self._current_locale != self.DEFAULT_LOCALE:
            self._logger.warning(
                "Help locale '%s' not found. Falling back to default locale '%s'",
                self._current_locale,
                self.DEFAULT_LOCALE,
            )
            self._current_locale = self.DEFAULT_LOCALE
            self._strings = self._get_locale_strings(self._current_locale)
            self._apply_locale_strings()
            self._load_help_index()

        if self._topics:
            self._show_topic(initial_topic)
        else:
            self._display_error(self._strings["error_missing_index"])

        self._logger.info("Help Center dialog initialized")

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Top toolbar with navigation and search
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # Main content area with splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left panel: Topics list
        left_panel = self._create_topics_panel()
        splitter.addWidget(left_panel)

        # Right panel: Content browser
        right_panel = self._create_content_panel()
        splitter.addWidget(right_panel)

        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 3)
        splitter.setSizes([250, 650])

        layout.addWidget(splitter)

        # Setup keyboard shortcuts
        self._setup_shortcuts()

    def _create_toolbar(self) -> QWidget:
        """Create the toolbar with navigation and search."""
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(10, 5, 10, 5)

        # Navigation buttons
        self._back_button = QPushButton(self._strings["nav_back"])
        self._back_button.setEnabled(False)
        self._back_button.clicked.connect(self._navigate_back)
        toolbar_layout.addWidget(self._back_button)

        self._forward_button = QPushButton(self._strings["nav_forward"])
        self._forward_button.setEnabled(False)
        self._forward_button.clicked.connect(self._navigate_forward)
        toolbar_layout.addWidget(self._forward_button)

        toolbar_layout.addSpacing(20)

        # Search box
        self._search_box = QLineEdit()
        self._search_box.setPlaceholderText(self._strings["search_placeholder"])
        self._search_box.textChanged.connect(self._filter_topics)
        self._search_box.setMaximumWidth(300)
        toolbar_layout.addWidget(self._search_box)

        toolbar_layout.addStretch()

        # Close button
        self._close_button = QPushButton(self._strings["close_button"])
        self._close_button.clicked.connect(self.accept)
        toolbar_layout.addWidget(self._close_button)

        return toolbar

    def _create_topics_panel(self) -> QWidget:
        """Create the left panel with topics list."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        self._topics_list = QListWidget()
        self._topics_list.itemClicked.connect(self._on_topic_selected)
        layout.addWidget(self._topics_list)

        return panel

    def _create_content_panel(self) -> QWidget:
        """Create the right panel with content browser."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(5, 5, 5, 5)

        self._content_browser = QTextBrowser()
        self._content_browser.setOpenLinks(False)
        self._content_browser.anchorClicked.connect(self._on_link_clicked)
        layout.addWidget(self._content_browser)

        return panel

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts."""
        # Alt+Left for back
        back_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Back), self)
        back_shortcut.activated.connect(self._navigate_back)

        # Alt+Right for forward
        forward_shortcut = QShortcut(QKeySequence(Qt.Key.Key_Forward), self)
        forward_shortcut.activated.connect(self._navigate_forward)

        # Ctrl+F for search focus
        search_shortcut = QShortcut(QKeySequence.StandardKey.Find, self)
        search_shortcut.activated.connect(self._focus_search)

    def _load_help_index(self) -> bool:
        """Load the help index from JSON."""
        locale_path = self._docs_path / self._current_locale
        index_file = locale_path / "index.json"

        if not index_file.exists():
            self._logger.warning("Help index not found: %s", index_file)
            self._topics = []
            self._topics_list.clear()
            return False

        try:
            with open(index_file, encoding="utf-8") as f:
                data = json.load(f)
                self._topics = data.get("topics", [])

            # Populate topics list
            self._topics_list.clear()
            for topic in self._topics:
                item = QListWidgetItem(topic["title"])
                item.setData(Qt.ItemDataRole.UserRole, topic["id"])
                self._topics_list.addItem(item)

            self._logger.info("Loaded %s help topics for locale '%s'", len(self._topics), self._current_locale)
            return True

        except (json.JSONDecodeError, OSError) as e:
            self._logger.error("Failed to load help index: %s", e)
            self._topics = []
            self._topics_list.clear()
            return False

    def _filter_topics(self, search_text: str) -> None:
        """Filter topics list based on search text."""
        search_lower = search_text.lower()

        for i in range(self._topics_list.count()):
            item = self._topics_list.item(i)
            topic_id = item.data(Qt.ItemDataRole.UserRole)

            # Find matching topic
            topic = next((t for t in self._topics if t["id"] == topic_id), None)
            if not topic:
                continue

            # Match against title and keywords
            matches = (
                search_lower in topic["title"].lower()
                or any(search_lower in kw.lower() for kw in topic.get("keywords", []))
            )

            item.setHidden(not matches if search_text else False)

    def _show_topic(self, topic_id: str) -> None:
        """Show a specific help topic."""
        # Find topic in index
        topic = next((t for t in self._topics if t["id"] == topic_id), None)
        if not topic:
            self._logger.warning("Topic not found: %s", topic_id)
            self._display_error(self._strings["error_missing_topic"], topic_id)
            return

        # Load HTML content
        locale_path = self._docs_path / self._current_locale
        topic_file = locale_path / topic["file"]

        if not topic_file.exists():
            self._logger.error("Help file not found: %s", topic_file)
            self._display_error(self._strings["error_missing_file"], topic["file"])
            return

        try:
            with open(topic_file, encoding="utf-8") as f:
                html_content = f.read()

            # Set base URL for relative links
            base_url = QUrl.fromLocalFile(str(locale_path) + "/")
            self._content_browser.setHtml(html_content, base_url)

            # Add to history
            if self._history_index == -1 or self._history[self._history_index] != topic_id:
                # Remove forward history if we're not at the end
                if self._history_index < len(self._history) - 1:
                    self._history = self._history[: self._history_index + 1]

                self._history.append(topic_id)
                self._history_index = len(self._history) - 1

            self._update_navigation_buttons()
            self.topic_changed.emit(topic_id)

            self._logger.debug("Displayed help topic: %s", topic_id)

        except OSError as e:
            self._logger.error("Failed to load help file: %s", e)
            self._display_error(self._strings["error_loading_content"], str(e))

    def _on_topic_selected(self, item: QListWidgetItem) -> None:
        """Handle topic selection from list."""
        topic_id = item.data(Qt.ItemDataRole.UserRole)
        if topic_id:
            self._show_topic(topic_id)

    def _on_link_clicked(self, url: QUrl) -> None:
        """Handle link clicks in the content browser."""
        if url.isLocalFile():
            # Extract topic ID from filename
            file_path = Path(url.toLocalFile())
            topic_file = file_path.name

            # Find topic by filename
            topic = next((t for t in self._topics if t["file"] == topic_file), None)
            if topic:
                self._show_topic(topic["id"])
            else:
                self._logger.warning(f"Unknown help link: {url.toString()}")
        else:
            # External link - could open in browser if needed
            self._logger.info(f"External link clicked: {url.toString()}")

    def _navigate_back(self) -> None:
        """Navigate back in history."""
        if self._history_index > 0:
            self._history_index -= 1
            topic_id = self._history[self._history_index]

            # Show topic without adding to history
            topic = next((t for t in self._topics if t["id"] == topic_id), None)
            if topic:
                locale_path = self._docs_path / self._current_locale
                topic_file = locale_path / topic["file"]

                if topic_file.exists():
                    with open(topic_file, encoding="utf-8") as f:
                        html_content = f.read()

                    base_url = QUrl.fromLocalFile(str(locale_path) + "/")
                    self._content_browser.setHtml(html_content, base_url)

            self._update_navigation_buttons()

    def _navigate_forward(self) -> None:
        """Navigate forward in history."""
        if self._history_index < len(self._history) - 1:
            self._history_index += 1
            topic_id = self._history[self._history_index]

            # Show topic without adding to history
            topic = next((t for t in self._topics if t["id"] == topic_id), None)
            if topic:
                locale_path = self._docs_path / self._current_locale
                topic_file = locale_path / topic["file"]

                if topic_file.exists():
                    with open(topic_file, encoding="utf-8") as f:
                        html_content = f.read()

                    base_url = QUrl.fromLocalFile(str(locale_path) + "/")
                    self._content_browser.setHtml(html_content, base_url)

            self._update_navigation_buttons()

    def _update_navigation_buttons(self) -> None:
        """Update the enabled state of navigation buttons."""
        self._back_button.setEnabled(self._history_index > 0)
        self._forward_button.setEnabled(self._history_index < len(self._history) - 1)

    def _focus_search(self) -> None:
        """Focus the search box."""
        self._search_box.setFocus()
        self._search_box.selectAll()

    def _display_error(self, message: str, details: Optional[str] = None) -> None:
        """Render an error message in the help viewer."""
        if not hasattr(self, "_content_browser"):
            return

        detail_html = ""
        if details:
            detail_html = f"<p>{html.escape(details)}</p>"

        self._content_browser.setHtml(f"<h1>{html.escape(message)}</h1>{detail_html}")

    def show_topic(self, topic_id: str) -> None:
        """Public method to show a specific topic."""
        self._show_topic(topic_id)

    def set_locale(self, locale: str) -> None:
        """Set the help locale."""
        if locale == self._current_locale:
            return

        previous_locale = self._current_locale
        previous_strings = self._strings

        self._current_locale = locale
        self._strings = self._get_locale_strings(locale)
        self._apply_locale_strings()

        if self._load_help_index():
            if self._topics:
                self._show_topic("welcome")
            return

        self._logger.warning("Locale not found or invalid: %s. Reverting to %s", locale, previous_locale)
        self._current_locale = previous_locale
        self._strings = previous_strings
        self._apply_locale_strings()
        if not self._load_help_index():
            self._display_error(self._strings["error_missing_index"])

    def _get_locale_strings(self, locale: str) -> Dict[str, str]:
        """Return localized UI strings for the dialog."""
        base = {
            "window_title": "Help Center",
            "nav_back": "◀ Back",
            "nav_forward": "Forward ▶",
            "search_placeholder": "Search help topics...",
            "close_button": "Close",
            "error_missing_topic": "Help topic not found",
            "error_missing_file": "Help topic file not found",
            "error_loading_content": "Failed to load help content",
            "error_missing_index": "Help content is not available",
        }

        zh_translations = {
            "window_title": "帮助中心",
            "nav_back": "◀ 返回",
            "nav_forward": "前进 ▶",
            "search_placeholder": "搜索帮助主题…",
            "close_button": "关闭",
            "error_missing_topic": "找不到指定的帮助主题",
            "error_missing_file": "无法找到帮助文件",
            "error_loading_content": "无法加载帮助内容",
            "error_missing_index": "当前语言的帮助内容不可用",
        }

        if locale.lower().startswith("zh"):
            base.update(zh_translations)

        return base

    def _apply_locale_strings(self) -> None:
        """Update UI strings to match the current locale."""
        self.setWindowTitle(self._strings["window_title"])

        if hasattr(self, "_back_button"):
            self._back_button.setText(self._strings["nav_back"])
        if hasattr(self, "_forward_button"):
            self._forward_button.setText(self._strings["nav_forward"])
        if hasattr(self, "_search_box"):
            self._search_box.setPlaceholderText(self._strings["search_placeholder"])
        if hasattr(self, "_close_button"):
            self._close_button.setText(self._strings["close_button"])
