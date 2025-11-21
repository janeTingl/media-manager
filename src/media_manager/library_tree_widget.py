"""Library tree widget for displaying libraries and their media types."""

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QMenu,
    QPushButton,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .logging import get_logger
from .persistence.models import Library
from .persistence.repositories import LibraryRepository, MediaItemRepository


class LibraryTreeWidget(QWidget):
    """Widget for displaying libraries in a tree structure."""

    # Signals
    library_selected = Signal(object, str)
    manage_libraries_requested = Signal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._library_repository = LibraryRepository()
        self._media_repository = MediaItemRepository()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the tree widget UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Button toolbar
        button_layout = QHBoxLayout()

        self.manage_button = QPushButton("管理媒体库")
        self.manage_button.clicked.connect(self._on_manage_clicked)
        button_layout.addWidget(self.manage_button)

        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self.load_libraries)
        button_layout.addWidget(self.refresh_button)

        layout.addLayout(button_layout)

        # Tree widget
        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("媒体库")
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._on_context_menu)
        self.tree.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.tree)

        # Load initial data
        self.load_libraries()

    def load_libraries(self) -> None:
        """Load libraries and populate the tree."""
        self.tree.clear()
        libraries = self._library_repository.get_active()

        for library in libraries:
            # Create library item
            library_item = QTreeWidgetItem(self.tree)
            library_item.setText(0, library.name)
            library_item.setData(0, Qt.ItemDataRole.UserRole, library)
            library_item.setData(0, Qt.ItemDataRole.UserRole + 1, "library")

            # Apply color if set
            if library.color:
                from PySide6.QtGui import QBrush, QColor

                color = QColor(library.color)
                library_item.setForeground(0, QBrush(color))

            # Count items by media type
            all_items = self._media_repository.get_by_library(library.id)
            movie_count = sum(1 for item in all_items if item.media_type == "movie")
            tv_count = sum(1 for item in all_items if item.media_type == "tv")

            # Add "All" child node
            all_node = QTreeWidgetItem(library_item)
            all_node.setText(0, f"All ({len(all_items)})")
            all_node.setData(0, Qt.ItemDataRole.UserRole, library)
            all_node.setData(0, Qt.ItemDataRole.UserRole + 1, "all")

            # Add media type child nodes based on library type
            if library.media_type == "mixed":
                # Show both Movies and TV Shows
                movies_node = QTreeWidgetItem(library_item)
                movies_node.setText(0, f"Movies ({movie_count})")
                movies_node.setData(0, Qt.ItemDataRole.UserRole, library)
                movies_node.setData(0, Qt.ItemDataRole.UserRole + 1, "movie")

                tv_node = QTreeWidgetItem(library_item)
                tv_node.setText(0, f"TV Shows ({tv_count})")
                tv_node.setData(0, Qt.ItemDataRole.UserRole, library)
                tv_node.setData(0, Qt.ItemDataRole.UserRole + 1, "tv")
            elif library.media_type == "movie":
                # Show only Movies
                movies_node = QTreeWidgetItem(library_item)
                movies_node.setText(0, f"Movies ({movie_count})")
                movies_node.setData(0, Qt.ItemDataRole.UserRole, library)
                movies_node.setData(0, Qt.ItemDataRole.UserRole + 1, "movie")
            elif library.media_type == "tv":
                # Show only TV Shows
                tv_node = QTreeWidgetItem(library_item)
                tv_node.setText(0, f"TV Shows ({tv_count})")
                tv_node.setData(0, Qt.ItemDataRole.UserRole, library)
                tv_node.setData(0, Qt.ItemDataRole.UserRole + 1, "tv")

            # Expand library item by default
            library_item.setExpanded(True)

    def _on_selection_changed(self) -> None:
        """Handle tree selection change."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return

        item = selected_items[0]
        library = item.data(0, Qt.ItemDataRole.UserRole)
        media_type_filter = item.data(0, Qt.ItemDataRole.UserRole + 1)

        if library and media_type_filter:
            self.library_selected.emit(library, media_type_filter)

    def _on_context_menu(self, position) -> None:
        """Show context menu for tree items."""
        item = self.tree.itemAt(position)
        if not item:
            return

        menu = QMenu(self)

        # Get item type
        item_type = item.data(0, Qt.ItemDataRole.UserRole + 1)

        if item_type == "library":
            # Context menu for library node
            expand_action = menu.addAction("Expand")
            expand_action.triggered.connect(lambda: item.setExpanded(True))

            collapse_action = menu.addAction("Collapse")
            collapse_action.triggered.connect(lambda: item.setExpanded(False))

            menu.addSeparator()

            manage_action = menu.addAction("Manage Libraries...")
            manage_action.triggered.connect(self._on_manage_clicked)
        else:
            # Context menu for filter nodes
            refresh_action = menu.addAction("Refresh Counts")
            refresh_action.triggered.connect(self.load_libraries)

        menu.exec(self.tree.viewport().mapToGlobal(position))

    def _on_manage_clicked(self) -> None:
        """Handle manage libraries button click."""
        self.manage_libraries_requested.emit()

    def get_selected_library(self) -> Optional[Library]:
        """Get the currently selected library."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return None
        return selected_items[0].data(0, Qt.ItemDataRole.UserRole)

    def get_selected_media_type(self) -> Optional[str]:
        """Get the currently selected media type filter."""
        selected_items = self.tree.selectedItems()
        if not selected_items:
            return None
        return selected_items[0].data(0, Qt.ItemDataRole.UserRole + 1)

    def select_library(self, library_id: int, media_type: str = "all") -> None:
        """Select a library and media type in the tree."""
        for i in range(self.tree.topLevelItemCount()):
            library_item = self.tree.topLevelItem(i)
            library = library_item.data(0, Qt.ItemDataRole.UserRole)

            if library and library.id == library_id:
                # Find the child node matching the media type
                for j in range(library_item.childCount()):
                    child_item = library_item.child(j)
                    child_media_type = child_item.data(0, Qt.ItemDataRole.UserRole + 1)

                    if child_media_type == media_type:
                        self.tree.setCurrentItem(child_item)
                        return

                # If not found, select the first child
                if library_item.childCount() > 0:
                    self.tree.setCurrentItem(library_item.child(0))
                return
