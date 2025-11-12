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
    QToolBar,
    QToolButton,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from .detail_panel import DetailPanel
from .library_postprocessor import PostProcessingOptions
from .library_view_model import LibraryViewModel
from .logging import get_logger
from .match_manager import MatchManager
from .match_resolution_widget import MatchResolutionWidget
from .media_grid_view import MediaGridView
from .media_table_view import MediaTableView
from .metadata_editor_widget import MetadataEditorWidget
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
        
        # Load initial data
        self.library_view_model.load_data()

        self._logger.info("Main window initialized")

    def _setup_components(self) -> None:
        """Initialize application components."""
        # Create match manager
        self.match_manager = MatchManager(self)

        # Create library view model
        self.library_view_model = LibraryViewModel(self)
        
        # Create new media views
        self.media_grid_view = MediaGridView(self)
        self.media_table_view = MediaTableView(self)
        self.detail_panel = DetailPanel(self)
        
        # Set up the view model with the views
        self.media_grid_view.set_model(self.library_view_model)
        self.media_table_view.set_model(self.library_view_model)
        
        # Create UI widgets
        self.scan_queue_widget = ScanQueueWidget(self)
        self.match_resolution_widget = MatchResolutionWidget(self)
        self.metadata_editor_widget = MetadataEditorWidget(self)

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
        
        # Create toolbar for view switching
        toolbar = QToolBar()
        toolbar.setMovable(False)
        
        # View mode buttons
        self.grid_action = QAction("Grid View", self)
        self.grid_action.setCheckable(True)
        self.grid_action.setChecked(True)
        self.grid_action.triggered.connect(lambda: self._switch_view("grid"))
        toolbar.addAction(self.grid_action)
        
        self.table_action = QAction("Table View", self)
        self.table_action.setCheckable(True)
        self.table_action.triggered.connect(lambda: self._switch_view("table"))
        toolbar.addAction(self.table_action)
        
        toolbar.addSeparator()
        
        # Thumbnail size controls
        toolbar.addWidget(QLabel("Thumbnail Size:"))
        for size in ["small", "medium", "large", "extra_large"]:
            action = QAction(size.capitalize(), self)
            action.triggered.connect(lambda checked, s=size: self.media_grid_view.set_thumbnail_size(s))
            toolbar.addAction(action)
        
        toolbar.addSeparator()
        
        # Filter controls
        self.filter_all_action = QAction("All", self)
        self.filter_all_action.setCheckable(True)
        self.filter_all_action.setChecked(True)
        self.filter_all_action.triggered.connect(lambda: self._set_media_filter("all"))
        toolbar.addAction(self.filter_all_action)
        
        self.filter_movies_action = QAction("Movies", self)
        self.filter_movies_action.setCheckable(True)
        self.filter_movies_action.triggered.connect(lambda: self._set_media_filter("movie"))
        toolbar.addAction(self.filter_movies_action)
        
        self.filter_tv_action = QAction("TV Shows", self)
        self.filter_tv_action.setCheckable(True)
        self.filter_tv_action.triggered.connect(lambda: self._set_media_filter("tv"))
        toolbar.addAction(self.filter_tv_action)
        
        layout.addWidget(toolbar)

        # Tab widget for different views
        self.tab_widget = QTabWidget()

        # Library tab with media views
        library_widget = QWidget()
        library_layout = QVBoxLayout(library_widget)
        
        # Create stacked widget for view switching
        from PySide6.QtWidgets import QStackedWidget
        self.view_stack = QStackedWidget()
        self.view_stack.addWidget(self.media_grid_view)
        self.view_stack.addWidget(self.media_table_view)
        library_layout.addWidget(self.view_stack)
        
        self.tab_widget.addTab(library_widget, "Library")
        
        # Add other tabs (keeping existing structure)
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
        
        # Add the new detail panel
        layout.addWidget(self.detail_panel)
        
        # Add metadata editor widget (keep existing functionality)
        layout.addWidget(self.metadata_editor_widget)

        return widget

    def _connect_signals(self) -> None:
        """Connect signals between components."""
        # Library view model signals
        self.library_view_model.data_loaded.connect(self._on_data_loaded)
        self.library_view_model.error_occurred.connect(self.update_status)
        
        # Media grid view signals
        self.media_grid_view.item_selected.connect(self._on_item_selected)
        self.media_grid_view.item_activated.connect(self._on_item_activated)
        self.media_grid_view.context_menu_requested.connect(self._on_context_menu_requested)
        
        # Media table view signals
        self.media_table_view.item_selected.connect(self._on_item_selected)
        self.media_table_view.item_activated.connect(self._on_item_activated)
        self.media_table_view.context_menu_requested.connect(self._on_context_menu_requested)
        self.media_table_view.selection_changed.connect(self._on_selection_changed)
        
        # Detail panel signals
        self.detail_panel.edit_requested.connect(self._on_edit_requested)
        self.detail_panel.play_requested.connect(self._on_play_requested)
        self.detail_panel.poster_download_requested.connect(self._on_poster_download_requested)
        
        # Scan queue signals
        self.scan_queue_widget.match_selected.connect(self.match_resolution_widget.set_match)
        self.scan_queue_widget.start_matching.connect(self._on_start_matching)
        self.scan_queue_widget.clear_queue.connect(self._on_clear_queue)
        self.scan_queue_widget.finalize_requested.connect(self._on_finalize_requested)

        # Match resolution signals
        self.match_resolution_widget.match_updated.connect(self.match_manager.update_match)
        self.match_resolution_widget.search_requested.connect(self.match_manager.search_matches)
        self.match_resolution_widget.poster_download_requested.connect(self._on_poster_download_requested)

        # Match manager signals
        self.match_manager.match_selected.connect(self.match_resolution_widget.set_match)
        self.match_manager.status_changed.connect(self.update_status)

        # Metadata editor signals
        self.metadata_editor_widget.match_updated.connect(self.match_manager.update_match)
        self.metadata_editor_widget.validation_error.connect(self.update_status)

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
        self.scan_queue_widget.clear_queue()
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

    def _switch_view(self, view_type: str) -> None:
        """Switch between grid and table views."""
        if view_type == "grid":
            self.view_stack.setCurrentWidget(self.media_grid_view)
            self.grid_action.setChecked(True)
            self.table_action.setChecked(False)
        elif view_type == "table":
            self.view_stack.setCurrentWidget(self.media_table_view)
            self.table_action.setChecked(True)
            self.grid_action.setChecked(False)

    def _set_media_filter(self, media_type: str) -> None:
        """Set media type filter."""
        # Update action states
        self.filter_all_action.setChecked(media_type == "all")
        self.filter_movies_action.setChecked(media_type == "movie")
        self.filter_tv_action.setChecked(media_type == "tv")
        
        # Apply filter to model
        self.library_view_model.set_media_type_filter(media_type)

    def _on_data_loaded(self, count: int) -> None:
        """Handle data loaded from model."""
        self.update_item_count(count)
        self.update_status(f"Loaded {count} media items")

    def _on_item_selected(self, item) -> None:
        """Handle item selection in any view."""
        self.detail_panel.set_media_item(item)
        
        # Synchronize selection between views
        self._synchronize_selection(item)

    def _on_item_activated(self, item) -> None:
        """Handle item activation (double click)."""
        if item:
            # Could play media, open details, or trigger matching
            self.update_status(f"Activated: {item.title}")

    def _on_selection_changed(self, items: list) -> None:
        """Handle selection change in table view."""
        if items:
            self.detail_panel.set_media_item(items[0])  # Show first selected item

    def _on_context_menu_requested(self, item, global_pos) -> None:
        """Handle context menu request."""
        # Create context menu
        from PySide6.QtWidgets import QMenu
        
        menu = QMenu(self)
        
        if item:
            view_action = menu.addAction("View Details")
            view_action.triggered.connect(lambda: self.detail_panel.set_media_item(item))
            
            edit_action = menu.addAction("Edit Metadata")
            edit_action.triggered.connect(lambda: self._on_edit_requested(item))
            
            menu.addSeparator()
            
            play_action = menu.addAction("Play")
            play_action.triggered.connect(lambda: self._on_play_requested(item))
            
            menu.addSeparator()
        
        refresh_action = menu.addAction("Refresh")
        refresh_action.triggered.connect(lambda: self.library_view_model.refresh())
        
        menu.exec(global_pos)

    def _on_edit_requested(self, item) -> None:
        """Handle edit request from detail panel or context menu."""
        if item:
            # Load item into metadata editor
            self.update_status(f"Editing: {item.title}")
            # Could switch to metadata editor tab or open dialog

    def _on_play_requested(self, item) -> None:
        """Handle play request from detail panel."""
        if item and item.files:
            # Play the first file
            file_path = item.files[0].path
            self.update_status(f"Playing: {file_path}")
            # Could use system default media player

    def _synchronize_selection(self, item) -> None:
        """Synchronize selection between grid and table views."""
        if not item:
            return
        
        # Clear selections in both views
        self.media_grid_view.clearSelection()
        self.media_table_view.clearSelection()
        
        # Find and select the item in both views
        # This is a simplified implementation - in practice you'd need to map items to indices
        pass
