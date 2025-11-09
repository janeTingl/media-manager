"""Main application window for the media manager."""

from pathlib import Path
from typing import Any, List

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QMainWindow,
    QMessageBox,
    QProgressDialog,
    QSplitter,
    QStatusBar,
    QTabWidget,
    QTreeWidget,
    QVBoxLayout,
    QWidget,
)

from .file_operations import FileOperationManager
from .logging import get_logger
from .preview_panel import PreviewPanel
from .scanner import MediaScanner
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
        self.setMinimumSize(1000, 700)

        # Setup UI
        self._setup_ui()
        self._setup_menu_bar()
        self._setup_status_bar()

        # Load saved geometry if available
        self._load_window_state()

        self._logger.info("Main window initialized")

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

        # Set splitter sizes (30% left, 50% center, 20% right)
        splitter.setSizes([300, 500, 200])

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

        # Library tab with file list
        self.library_list = QListWidget()
        self.tab_widget.addTab(self.library_list, "Library")

        # Recent tab
        self.tab_widget.addTab(QListWidget(), "Recent")

        # Favorites tab
        self.tab_widget.addTab(QListWidget(), "Favorites")

        # Search tab
        self.tab_widget.addTab(QListWidget(), "Search")

        # Rename preview tab
        self.preview_panel = PreviewPanel()
        self.preview_panel.execute_requested.connect(self._on_execute_renames)
        self.tab_widget.addTab(self.preview_panel, "Rename Preview")

        layout.addWidget(self.tab_widget)

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

    def _setup_menu_bar(self) -> None:
        """Setup the application menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("&File")

        scan_action = QAction("&Scan Directory", self)
        scan_action.setShortcut("Ctrl+S")
        scan_action.triggered.connect(self._on_scan_directory)
        file_menu.addAction(scan_action)

        file_menu.addSeparator()

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
        self.status_label.setText("Preferences dialog not yet implemented")

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

    def _on_scan_directory(self) -> None:
        """Handle directory scanning."""
        from PySide6.QtWidgets import QFileDialog

        directory = QFileDialog.getExistingDirectory(
            self, "Select Directory to Scan", ""
        )
        if directory:
            self._scan_directory(Path(directory))

    def _scan_directory(self, directory: Path) -> None:
        """Scan a directory for media files."""
        self.update_status(f"Scanning {directory}...")

        scanner = MediaScanner()
        media_files = scanner.scan_directory(directory)

        # Update library list
        self.library_list.clear()
        for media in media_files:
            item_text = f"{media.title}"
            if media.year:
                item_text += f" ({media.year})"
            if media.media_type.value == "tv_episode":
                item_text += f" - S{media.season:02d}E{media.episode:02d}"
            item_text += f" [{media.media_type.value}]"

            self.library_list.addItem(item_text)

        # Update preview panel
        self.preview_panel.set_media_items(media_files)

        # Update status
        self.update_item_count(len(media_files))
        self.update_status(f"Found {len(media_files)} media files")

        # Switch to preview tab
        self.tab_widget.setCurrentWidget(self.preview_panel)

    def _on_execute_renames(self, operations: List, dry_run: bool) -> None:
        """Handle rename execution request."""
        if not operations:
            QMessageBox.information(
                self, "No Operations", "No operations selected for execution."
            )
            return

        # Show progress dialog
        progress = QProgressDialog(
            (
                "Executing rename operations..."
                if not dry_run
                else "Validating operations..."
            ),
            "Cancel",
            0,
            len(operations),
            self,
        )
        progress.setWindowModality(Qt.WindowModality.WindowModal)
        progress.show()

        try:
            # Execute operations
            file_manager = FileOperationManager()
            success, messages = file_manager.execute_atomic_renames(operations, dry_run)

            # Show results
            if success:
                title = "Success" if not dry_run else "Validation Successful"
                icon = QMessageBox.Icon.Information
            else:
                title = "Error" if not dry_run else "Validation Failed"
                icon = QMessageBox.Icon.Warning

            msg_box = QMessageBox(
                icon, title, "\n".join(messages), QMessageBox.StandardButton.Ok, self
            )
            msg_box.exec()

            # Update operation statuses in preview
            for i, op in enumerate(operations):
                if i < len(operations):  # Safety check
                    if op.executed:
                        self.preview_panel.update_operation_status(
                            op, "Completed", True
                        )
                    else:
                        self.preview_panel.update_operation_status(op, "Failed", False)

        except Exception as e:
            self._logger.exception("Error during rename execution")
            QMessageBox.critical(self, "Error", f"An unexpected error occurred: {e}")

        finally:
            progress.close()

    def closeEvent(self, event: Any) -> None:
        """Handle window close event."""
        self._save_window_state()
        self._logger.info("Main window closing")
        super().closeEvent(event)
