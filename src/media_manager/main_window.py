"""Main application window for the media manager."""

from typing import Any

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from .library_postprocessor import PostProcessingOptions
from .logging import get_logger
from .match_manager import MatchManager
from .match_resolution_widget import MatchResolutionWidget
from .scan_queue_widget import ScanQueueWidget
from .settings import SettingsManager


class MainWindow(QMainWindow):
    """Main application window with navigation panes and status bar."""

    # Signals
    file_opened = Signal(str)
    settings_changed = Signal()

    def __init__(self, settings: SettingsManager) -> None:
        super().__init__()
        self._settings = settings
        self._logger = get_logger().get_logger(__name__)

        self.setWindowTitle("Media Manager")
        self.setMinimumSize(1200, 800)

        # Initialize components
        self._setup_components()

        # Setup UI
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()

        # Load saved geometry if available
        self._load_window_state()

        self._logger.info("Main window initialized")

    def _setup_components(self) -> None:
        """Initialize application components."""
        # Create match manager
        self.match_manager = MatchManager(self)

        # Create UI widgets
        self.scan_queue_widget = ScanQueueWidget(self)
        self.match_resolution_widget = MatchResolutionWidget(self)

        # Connect signals
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the main UI layout."""
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Main layout
        main_layout = QHBoxLayout(central_widget)

        # Create splitter for resizable panes
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # Left navigation pane
        left_widget = self._create_navigation_pane()
        splitter.addWidget(left_widget)

        # Center content area with tabs
        center_widget = self._create_content_area()
        splitter.addWidget(center_widget)

        # Right properties/info pane
        right_widget = self._create_properties_pane()
        splitter.addWidget(right_widget)

        # Set splitter sizes (25% left, 50% center, 25% right)
        splitter.setSizes([300, 600, 300])

    def _create_navigation_pane(self) -> QWidget:
        """Create the left navigation pane with file tree."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # File tree
        self.file_tree = QTreeWidget()
        self.file_tree.setHeaderLabel("File System")
        self.file_tree.setColumnCount(1)
        layout.addWidget(self.file_tree)

        return widget

    def _create_content_area(self) -> QWidget:
        """Create the center content area with tabs."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Tab widget for different views
        self.tab_widget = QTabWidget()

        # Add tabs
        self.tab_widget.addTab(QListWidget(), "Library")
        self.tab_widget.addTab(QListWidget(), "Recent")
        self.tab_widget.addTab(QListWidget(), "Favorites")
        self.tab_widget.addTab(QListWidget(), "Search")

        # Add matching tab
        self.tab_widget.addTab(self._create_matching_tab(), "Matching")

        layout.addWidget(self.tab_widget)

        return widget

    def _create_matching_tab(self) -> QWidget:
        """Create the matching workflow tab."""
        widget = QWidget()
        layout = QHBoxLayout(widget)

        # Left side - scan queue
        layout.addWidget(self.scan_queue_widget, 1)

        # Right side - match resolution
        layout.addWidget(self.match_resolution_widget, 1)

        return widget

    def _create_properties_pane(self) -> QWidget:
        """Create the right properties/info pane."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Properties placeholder
        properties_label = QLabel("Properties")
        properties_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(properties_label)

        self.properties_list = QListWidget()
        layout.addWidget(self.properties_list)

        return widget

    def _connect_signals(self) -> None:
        """Connect signals between components."""
        # Scan queue signals
        self.scan_queue_widget.match_selected.connect(
            self.match_resolution_widget.set_match
        )
        self.scan_queue_widget.start_matching.connect(self._on_start_matching)
        self.scan_queue_widget.clear_queue.connect(self._on_clear_queue)
        self.scan_queue_widget.finalize_requested.connect(self._on_finalize_requested)

        # Match resolution signals
        self.match_resolution_widget.match_updated.connect(
            self.match_manager.update_match
        )
        self.match_resolution_widget.search_requested.connect(
            self.match_manager.search_matches
        )
        self.match_resolution_widget.poster_download_requested.connect(
            self._on_poster_download_requested
        )

        # Match manager signals
        self.match_manager.match_selected.connect(
            self.match_resolution_widget.set_match
        )
        self.match_manager.status_changed.connect(self.update_status)

    def _on_start_matching(self) -> None:
        """Handle start matching request."""
        # Get pending matches from scan queue
        pending_matches = self.scan_queue_widget.get_matches()
        if pending_matches:
            # Extract metadata for matching
            metadata_list = [match.metadata for match in pending_matches]

            # Add to match manager and start matching
            self.match_manager.add_metadata(metadata_list)
            self.match_manager.start_matching()

    def _on_clear_queue(self) -> None:
        """Handle clear queue request."""
        self.match_manager.clear_all()
        self.scan_queue_widget.do_clear_queue()
        self.match_resolution_widget.clear_match()
        self.update_status("Queue cleared")

    def _on_poster_download_requested(self, match, poster_types) -> None:
        """Handle poster download request."""
        self.match_manager.download_posters(match, poster_types)

    def _on_finalize_requested(self, options: PostProcessingOptions) -> None:
        """Handle library finalization requests."""
        worker = self.match_manager.finalize_library(options)
        if worker is not None:
            self.scan_queue_widget.set_post_processing_worker(worker)
        else:
            # Reset UI state when finalization cannot start
            self.scan_queue_widget.finalize_button.setEnabled(True)
            self.scan_queue_widget.finalize_progress_bar.setVisible(False)

    def add_scan_results(self, metadata_list) -> None:
        """Add scan results to the queue."""
        # Add to scan queue widget
        self.scan_queue_widget.add_metadata(metadata_list)

        # Switch to matching tab
        self.tab_widget.setCurrentIndex(4)  # Matching tab index

        self.update_status(f"Added {len(metadata_list)} items to scan queue")

    def _setup_menu_bar(self) -> None:
        """Setup the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        open_action = QAction("&Open", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_file)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("E&xit", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Edit menu
        edit_menu = menubar.addMenu("&Edit")

        preferences_action = QAction("&Preferences", self)
        preferences_action.triggered.connect(self._on_preferences)
        edit_menu.addAction(preferences_action)

        # View menu
        view_menu = menubar.addMenu("&View")

        toggle_panes_action = QAction("Toggle &Panes", self)
        toggle_panes_action.setShortcut("F9")
        toggle_panes_action.setCheckable(True)
        toggle_panes_action.setChecked(True)
        toggle_panes_action.triggered.connect(self._toggle_panes)
        view_menu.addAction(toggle_panes_action)

        # Help menu
        help_menu = menubar.addMenu("&Help")

        about_action = QAction("&About", self)
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)

    def _setup_status_bar(self) -> None:
        """Setup the application status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

        # Permanent widgets
        self.item_count_label = QLabel("0 items")
        self.status_bar.addPermanentWidget(self.item_count_label)

    def _load_window_state(self) -> None:
        """Load saved window geometry and state."""
        geometry = self._settings.get("window_geometry")
        if geometry:
            try:
                self.restoreGeometry(bytes.fromhex(geometry))
            except (ValueError, TypeError):
                pass

        state = self._settings.get("window_state")
        if state:
            try:
                self.restoreState(bytes.fromhex(state))
            except (ValueError, TypeError):
                pass

    def _save_window_state(self) -> None:
        """Save window geometry and state."""
        geometry_bytes = self.saveGeometry()
        state_bytes = self.saveState()
        self._settings.set("window_geometry", bytes(geometry_bytes).hex())
        self._settings.set("window_state", bytes(state_bytes).hex())
        self._settings.save_settings()

    def _on_open_file(self) -> None:
        """Handle file open action."""
        from PySide6.QtWidgets import QFileDialog

        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open File", "", "All Files (*)"
        )
        if file_path:
            self.file_opened.emit(file_path)
            self.status_label.setText(f"Opened: {file_path}")

    def _on_preferences(self) -> None:
        """Handle preferences action."""
        from PySide6.QtWidgets import (
            QDialog,
            QDialogButtonBox,
            QTabWidget,
            QVBoxLayout,
        )

        from .poster_settings_widget import PosterSettingsWidget

        dialog = QDialog(self)
        dialog.setWindowTitle("Preferences")
        dialog.setMinimumSize(600, 500)

        layout = QVBoxLayout(dialog)

        # Create tab widget for different preference categories
        tab_widget = QTabWidget()

        # Poster settings tab
        poster_settings = PosterSettingsWidget()
        poster_settings.settings_changed.connect(self.settings_changed.emit)
        tab_widget.addTab(poster_settings, "Posters")

        layout.addWidget(tab_widget)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok)
        button_box.accepted.connect(dialog.accept)
        layout.addWidget(button_box)

        # Show dialog
        dialog.exec()
        self.status_label.setText("Preferences updated")

    def _on_about(self) -> None:
        """Handle about action."""
        from PySide6.QtWidgets import QMessageBox

        QMessageBox.about(
            self,
            "About Media Manager",
            "Media Manager v0.1.0\n\n"
            "A PySide6-based media management application.\n\n"
            "Built with Python and PySide6.",
        )

    def _toggle_panes(self, checked: bool) -> None:
        """Toggle navigation and properties panes."""
        # This is a placeholder - actual implementation would hide/show panes
        self.status_label.setText(f"Panes {'shown' if checked else 'hidden'}")

    def update_status(self, message: str) -> None:
        """Update the status bar message."""
        self.status_label.setText(message)

    def update_item_count(self, count: int) -> None:
        """Update the item count in the status bar."""
        self.item_count_label.setText(f"{count} items")

    def closeEvent(self, event: Any) -> None:
        """Handle window close event."""
        self._save_window_state()
        self._logger.info("Main window closing")
        super().closeEvent(event)
