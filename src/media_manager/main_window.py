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

from .batch_operations_dialog import BatchOperationsDialog
from .dashboard_widget import DashboardWidget
from .detail_panel import DetailPanel
from .library_manager_dialog import LibraryManagerDialog
from .library_postprocessor import PostProcessingOptions
from .library_tree_widget import LibraryTreeWidget
from .library_view_model import LibraryViewModel
from .logging import get_logger
from .match_manager import MatchManager
from .match_resolution_widget import MatchResolutionWidget
from .media_grid_view import MediaGridView
from .media_table_view import MediaTableView
from .metadata_editor_widget import MetadataEditorWidget
from .persistence.repositories import LibraryRepository
from .preferences_window import PreferencesWindow
from .scan_queue_widget import ScanQueueWidget
from .search_tab_widget import SearchTabWidget
from .settings import SettingsManager


class MainWindow(QMainWindow):
    """Main application window with navigation panes and status bar."""

    # Signals
    file_opened = Signal(str)
    settings_changed = Signal()

    def __init__(self, settings: SettingsManager) -> None:
        super().__init__()
        self._settings = settings
        self._settings.setting_changed.connect(self._on_settings_manager_changed)
        self._logger = get_logger().get_logger(__name__)
        self._current_library = None
        self._library_repository = LibraryRepository()

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
        
        # Restore last active library
        self._restore_last_active_library()

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
        self.search_tab_widget = SearchTabWidget(self)
        self.dashboard_widget = DashboardWidget(self)

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
        """Create the left navigation pane with library tree."""
        # Create library tree widget
        self.library_tree_widget = LibraryTreeWidget()
        self.library_tree_widget.library_selected.connect(self._on_library_selected)
        self.library_tree_widget.manage_libraries_requested.connect(self._on_manage_libraries)
        return self.library_tree_widget

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
        
        # Add dashboard tab
        self.tab_widget.addTab(self.dashboard_widget, "Dashboard")
        
        # Add search tab
        self.tab_widget.addTab(self.search_tab_widget, "Search")
        
        # Add other tabs (keeping existing structure)
        self.tab_widget.addTab(QListWidget(), "Recent")
        self.tab_widget.addTab(QListWidget(), "Favorites")

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
        
        # Search tab signals
        self.search_tab_widget.item_selected.connect(self._on_item_selected)
        self.search_tab_widget.item_activated.connect(self._on_item_activated)
        
        # Dashboard signals
        self.match_manager.matches_updated.connect(self.dashboard_widget.on_data_mutation)
        self.library_view_model.data_loaded.connect(self.dashboard_widget.on_data_mutation)

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

        manage_libraries_action = QAction("Manage &Libraries...", self)
        manage_libraries_action.setShortcut("Ctrl+L")
        manage_libraries_action.triggered.connect(self._on_manage_libraries)
        file_menu.addAction(manage_libraries_action)

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

        batch_ops_action = QAction("Batch &Operations...", self)
        batch_ops_action.setShortcut("Ctrl+B")
        batch_ops_action.triggered.connect(self._on_batch_operations)
        edit_menu.addAction(batch_ops_action)

        edit_menu.addSeparator()

        export_action = QAction("&Export Media...", self)
        export_action.setShortcut("Ctrl+E")
        export_action.triggered.connect(self._on_export_media)
        edit_menu.addAction(export_action)

        import_action = QAction("&Import Media...", self)
        import_action.setShortcut("Ctrl+I")
        import_action.triggered.connect(self._on_import_media)
        edit_menu.addAction(import_action)

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
        geometry = self._settings.get_ui_layout("main_window.geometry")
        if geometry:
            try:
                self.restoreGeometry(bytes.fromhex(geometry))
            except (ValueError, TypeError):
                pass

        state = self._settings.get_ui_layout("main_window.state")
        if state:
            try:
                self.restoreState(bytes.fromhex(state))
            except (ValueError, TypeError):
                pass

    def _save_window_state(self) -> None:
        """Save window geometry and state."""
        geometry_bytes = self.saveGeometry()
        state_bytes = self.saveState()
        self._settings.set_ui_layout("main_window.geometry", bytes(geometry_bytes).hex())
        self._settings.set_ui_layout("main_window.state", bytes(state_bytes).hex())
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
        dialog = PreferencesWindow(self._settings, self)
        dialog.preferences_applied.connect(self.settings_changed.emit)
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

    def _on_settings_manager_changed(self, key: str, value: object) -> None:
        """Forward settings updates to interested components."""
        del key, value  # Unused but kept for signal compatibility
        self.settings_changed.emit()

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

            # Quick tags submenu
            tags_menu = menu.addMenu("Quick Tags")
            from .persistence.models import Tag, Favorite
            from .search_service import SearchService
            from .persistence.repositories import transactional_context

            search_service = SearchService()
            available_tags = search_service.get_available_tags()

            for tag in available_tags:
                tag_action = tags_menu.addAction(tag.name)
                tag_action.setCheckable(True)
                tag_action.setChecked(tag in item.tags)
                tag_action.triggered.connect(
                    lambda checked, t=tag, i=item: self._toggle_tag_on_item(i, t)
                )

            tags_menu.addSeparator()
            new_tag_action = tags_menu.addAction("+ Add New Tag...")
            new_tag_action.triggered.connect(lambda: self._create_new_tag_for_item(item))

            # Toggle favorite
            favorite_action = menu.addAction("Toggle Favorite")
            favorite_action.setCheckable(True)
            favorite_action.setChecked(len(item.favorites) > 0)
            favorite_action.triggered.connect(lambda: self._toggle_favorite(item))

            menu.addSeparator()

        batch_action = menu.addAction("Batch Operations...")
        batch_action.triggered.connect(self._on_batch_operations)

        menu.addSeparator()

        refresh_action = menu.addAction("Refresh")
        refresh_action.triggered.connect(lambda: self.library_view_model.refresh())

        menu.exec(global_pos)

    def _on_batch_operations(self) -> None:
        """Open the batch operations dialog for the current selection."""
        selected_items = self._get_selected_media_items()
        if not selected_items:
            self.update_status("Select one or more items to run batch operations")
            return
        dialog = BatchOperationsDialog(selected_items, self._settings, self)
        dialog.operations_completed.connect(self._on_batch_operations_completed)
        dialog.exec()

    def _on_batch_operations_completed(self, summary) -> None:
        """Handle completion of batch operations."""
        if summary:
            self.update_status(summary.to_message())
        self.library_view_model.refresh()

    def _on_export_media(self) -> None:
        """Handle export media action."""
        from .import_export_wizard import ExportWizard

        wizard = ExportWizard(self)
        if wizard.exec():
            self.update_status("Export completed successfully")
        else:
            self.update_status("Export cancelled")

    def _on_import_media(self) -> None:
        """Handle import media action."""
        from .import_export_wizard import ImportWizard

        wizard = ImportWizard(self)
        if wizard.exec():
            self.update_status("Import completed successfully")
            # Refresh the library view to show imported items
            self.library_view_model.refresh()
        else:
            self.update_status("Import cancelled")

    def _get_selected_media_items(self) -> list:
        """Return the currently selected media items from the active view."""
        items = self.media_table_view.get_selected_items()
        if not items:
            items = self.media_grid_view.get_selected_items()
        return items

    def _on_edit_requested(self, item) -> None:

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

    def _on_library_selected(self, library, media_type_filter: str) -> None:
        """Handle library selection from tree widget."""
        self._current_library = library
        
        # Save the last active library
        self._settings.set_last_active_library_id(library.id)
        self._settings.save_settings()
        
        # Update the view model to filter by library and media type
        if media_type_filter == "all":
            self.library_view_model.set_library_filter(library.id)
            self.library_view_model.set_media_type_filter("all")
        elif media_type_filter == "library":
            # Just selected the library node itself
            self.library_view_model.set_library_filter(library.id)
            self.library_view_model.set_media_type_filter("all")
        else:
            # Selected a specific media type under the library
            self.library_view_model.set_library_filter(library.id)
            self.library_view_model.set_media_type_filter(media_type_filter)
        
        # Update scan queue widget with the current library
        self.scan_queue_widget.set_target_library(library.id)
        
        # Update status
        media_type_text = media_type_filter.title() if media_type_filter != "all" else "All"
        self.update_status(f"Viewing {library.name} - {media_type_text}")

    def _on_manage_libraries(self) -> None:
        """Handle manage libraries request."""
        dialog = LibraryManagerDialog(self)
        dialog.library_created.connect(self._on_library_created)
        dialog.library_updated.connect(self._on_library_updated)
        dialog.library_deleted.connect(self._on_library_deleted)
        dialog.exec()

    def _on_library_created(self, library) -> None:
        """Handle library created event."""
        self.library_tree_widget.load_libraries()
        self.update_status(f"Library '{library.name}' created")

    def _on_library_updated(self, library) -> None:
        """Handle library updated event."""
        self.library_tree_widget.load_libraries()
        
        # Reload data if this is the current library
        if self._current_library and self._current_library.id == library.id:
            self._current_library = library
            self.library_view_model.load_data()
        
        self.update_status(f"Library '{library.name}' updated")

    def _on_library_deleted(self, library_id: int) -> None:
        """Handle library deleted event."""
        self.library_tree_widget.load_libraries()
        
        # Clear view if the deleted library was active
        if self._current_library and self._current_library.id == library_id:
            self._current_library = None
            self.library_view_model.clear_filters()
        
        self.update_status("Library deleted")

    def _restore_last_active_library(self) -> None:
        """Restore the last active library from settings."""
        library_id = self._settings.get_last_active_library_id()
        if library_id:
            library = self._library_repository.get_by_id(library_id)
            if library and library.is_active:
                self.library_tree_widget.select_library(library_id)
                return
        
        # If no saved library or it's invalid, select the first active library
        libraries = self._library_repository.get_active()
        if libraries:
            self.library_tree_widget.select_library(libraries[0].id)
        else:
            # No libraries exist, prompt to create one
            self.update_status("No libraries found. Please create a library to get started.")

    def get_current_library(self):
        """Get the currently selected library."""
        return self._current_library

    def _toggle_tag_on_item(self, item, tag) -> None:
        """Toggle a tag on a media item."""
        from .persistence.repositories import transactional_context
        
        try:
            with transactional_context() as uow:
                from .persistence.models import Tag, MediaItem
                repo = uow.get_repository(MediaItem)
                current_item = repo.read(item.id)
                
                if tag in current_item.tags:
                    current_item.tags.remove(tag)
                    self.update_status(f"Removed tag '{tag.name}' from {item.title}")
                else:
                    current_item.tags.append(tag)
                    self.update_status(f"Added tag '{tag.name}' to {item.title}")
                
                uow.commit()
                self.library_view_model.refresh()
        except Exception as e:
            self._logger.error(f"Error toggling tag: {e}")
            self.update_status(f"Error toggling tag: {str(e)}")

    def _create_new_tag_for_item(self, item) -> None:
        """Create a new tag and add it to the item."""
        from PySide6.QtWidgets import QInputDialog
        from .persistence.models import Tag
        from .persistence.repositories import transactional_context
        
        tag_name, ok = QInputDialog.getText(
            self, "New Tag", "Enter tag name:"
        )
        
        if ok and tag_name.strip():
            try:
                with transactional_context() as uow:
                    tag_repo = uow.get_repository(Tag)
                    from .persistence.models import MediaItem
                    media_repo = uow.get_repository(MediaItem)
                    
                    existing = tag_repo.filter_by(name=tag_name.strip())
                    if existing:
                        tag = existing[0]
                    else:
                        tag = Tag(name=tag_name.strip())
                        tag_repo.create(tag)
                    
                    current_item = media_repo.read(item.id)
                    if tag not in current_item.tags:
                        current_item.tags.append(tag)
                    
                    uow.commit()
                    self.update_status(f"Created and added tag '{tag.name}' to {item.title}")
                    self.library_view_model.refresh()
            except Exception as e:
                self._logger.error(f"Error creating tag: {e}")
                self.update_status(f"Error creating tag: {str(e)}")

    def _toggle_favorite(self, item) -> None:
        """Toggle favorite status for a media item."""
        from .persistence.models import Favorite, MediaItem
        from .persistence.repositories import transactional_context
        
        try:
            with transactional_context() as uow:
                media_repo = uow.get_repository(MediaItem)
                favorite_repo = uow.get_repository(Favorite)
                
                current_item = media_repo.read(item.id)
                existing_favorite = favorite_repo.filter_by(media_item_id=item.id)
                
                if existing_favorite:
                    favorite_repo.delete(existing_favorite[0].id)
                    self.update_status(f"Removed {item.title} from favorites")
                else:
                    favorite = Favorite(media_item_id=item.id)
                    favorite_repo.create(favorite)
                    self.update_status(f"Added {item.title} to favorites")
                
                uow.commit()
                self.library_view_model.refresh()
        except Exception as e:
            self._logger.error(f"Error toggling favorite: {e}")
            self.update_status(f"Error toggling favorite: {str(e)}")
