"""Media table view with detailed list display."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHeaderView,
    QMenu,
    QTableView,
    QToolTip,
    QWidget,
)

from .library_view_model import LibraryViewModel


class MediaTableView(QTableView):
    """
    Table view for media items with detailed information display.
    
    Provides a tabular layout with sortable columns and comprehensive metadata.
    Supports filtering, grouping, and advanced selection features.
    """

    # Signals
    item_activated = Signal(object)  # MediaItem
    item_selected = Signal(object)  # MediaItem
    selection_changed = Signal(list)  # List[MediaItem]
    context_menu_requested = Signal(object, object)  # MediaItem, global_pos

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        # Setup table properties
        self.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        self.setSelectionMode(QTableView.SelectionMode.ExtendedSelection)
        self.setEditTriggers(QTableView.EditTrigger.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setWordWrap(False)
        
        # Header setup
        header = self.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        header.setSortIndicatorShown(True)
        
        # Vertical header
        vertical_header = self.verticalHeader()
        vertical_header.setVisible(False)
        vertical_header.setDefaultSectionSize(25)
        
        # Appearance
        self.setShowGrid(True)
        self.setGridStyle(Qt.PenStyle.SolidLine)
        self.setCornerButtonEnabled(True)
        
        # Column widths (will be adjusted after model is set)
        self._default_column_widths = {
            0: 300,  # Title
            1: 80,   # Year
            2: 80,   # Type
            3: 80,   # Rating
            4: 100,  # Duration
            5: 100,  # Added
            6: 100,  # Size
            7: 100,  # Status
        }
        
        # Model
        self._model: Optional[LibraryViewModel] = None
        
        # Context menu
        self._context_menu: Optional[QMenu] = None
        
        # Connect signals
        self.clicked.connect(self._on_item_clicked)
        self.doubleClicked.connect(self._on_item_double_clicked)
        self.entered.connect(self._on_item_entered)
        self.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def set_model(self, model: LibraryViewModel) -> None:
        """Set the view model."""
        self._model = model
        self.setModel(model)
        
        # Apply default column widths
        self._apply_column_widths()
        
        # Set default sort
        self.sortByColumn(0, Qt.SortOrder.AscendingOrder)

    def get_selected_items(self) -> list:
        """Get currently selected media items."""
        if not self._model:
            return []
        
        selected_indices = self.selectedIndexes()
        return self._model.get_items_for_indices(selected_indices)

    def get_current_item(self) -> Optional[object]:
        """Get the current media item."""
        if not self._model:
            return None
        
        current_index = self.currentIndex()
        if current_index.isValid():
            return current_index.internalPointer()
        return None

    def select_all(self) -> None:
        """Select all items in the table."""
        if self._model and self._model.rowCount() > 0:
            self.selectAll()

    def clear_selection(self) -> None:
        """Clear all selections."""
        self.clearSelection()

    def resize_columns_to_contents(self) -> None:
        """Resize all columns to fit their contents."""
        self.resizeColumnsToContents()
        
        # Apply minimum widths for better readability
        header = self.horizontalHeader()
        for column, min_width in self._default_column_widths.items():
            current_width = header.sectionSize(column)
            if current_width < min_width:
                header.resizeSection(column, min_width)

    def set_column_visibility(self, column: int, visible: bool) -> None:
        """Show or hide a specific column."""
        self.setColumnHidden(column, not visible)

    def toggle_column_visibility(self, column: int) -> None:
        """Toggle visibility of a specific column."""
        self.setColumnHidden(column, not self.isColumnHidden(column))

    def auto_fit_columns(self) -> None:
        """Automatically fit columns within the available width."""
        header = self.horizontalHeader()
        total_width = self.viewport().width()
        
        # Calculate proportional widths
        total_proportion = sum(self._default_column_widths.values())
        
        for column, width in self._default_column_widths.items():
            proportion = width / total_proportion
            new_width = int(total_width * proportion)
            header.resizeSection(column, new_width)

    def create_context_menu(self) -> QMenu:
        """Create and return the context menu."""
        menu = QMenu(self)
        
        # Add actions
        view_action = menu.addAction("View Details")
        view_action.triggered.connect(lambda: self._view_selected_items())
        
        menu.addSeparator()
        
        edit_action = menu.addAction("Edit Metadata")
        edit_action.triggered.connect(lambda: self._edit_selected_items())
        
        menu.addSeparator()
        
        select_action = menu.addAction("Select All")
        select_action.setShortcut("Ctrl+A")
        select_action.triggered.connect(self.select_all)
        
        menu.addSeparator()
        
        # Column visibility submenu
        columns_menu = menu.addMenu("Show Columns")
        headers = ["Title", "Year", "Type", "Rating", "Duration", "Added", "Size", "Status"]
        
        for i, header_text in enumerate(headers):
            action = columns_menu.addAction(header_text)
            action.setCheckable(True)
            action.setChecked(not self.isColumnHidden(i))
            action.triggered.connect(lambda checked, col=i: self.set_column_visibility(col, checked))
        
        return menu

    def _apply_column_widths(self) -> None:
        """Apply default column widths."""
        header = self.horizontalHeader()
        for column, width in self._default_column_widths.items():
            header.resizeSection(column, width)

    def _on_item_clicked(self, index) -> None:
        """Handle item click."""
        if index.isValid() and self._model:
            item = index.internalPointer()
            self.item_selected.emit(item)

    def _on_item_double_clicked(self, index) -> None:
        """Handle item double click."""
        if index.isValid() and self._model:
            item = index.internalPointer()
            self.item_activated.emit(item)

    def _on_item_entered(self, index) -> None:
        """Handle item hover for tooltip."""
        if index.isValid() and self._model:
            item = index.internalPointer()
            self._show_item_tooltip(item, index)

    def _on_selection_changed(self, selected, deselected) -> None:
        """Handle selection change."""
        selected_items = self.get_selected_items()
        self.selection_changed.emit(selected_items)

    def _show_item_tooltip(self, item, index) -> None:
        """Show enhanced tooltip for media item."""
        if not item:
            return
        
        # Build detailed tooltip content
        tooltip = f"<b>{item.title}</b><br>"
        tooltip += f"<table border='0' cellpadding='2' cellspacing='0'>"
        
        if item.year:
            tooltip += f"<tr><td><b>Year:</b></td><td>{item.year}</td></tr>"
        
        if item.media_type:
            tooltip += f"<tr><td><b>Type:</b></td><td>{item.media_type.capitalize()}</td></tr>"
        
        if item.rating:
            stars = "★" * int(item.rating) + "☆" * (10 - int(item.rating))
            tooltip += f"<tr><td><b>Rating:</b></td><td>{item.rating:.1f}/10 {stars}</td></tr>"
        
        if item.runtime:
            hours = item.runtime // 60
            minutes = item.runtime % 60
            runtime_str = f"{hours}h {minutes}m" if hours else f"{minutes}m"
            tooltip += f"<tr><td><b>Duration:</b></td><td>{runtime_str}</td></tr>"
        
        if item.created_at:
            tooltip += f"<tr><td><b>Added:</b></td><td>{item.created_at.strftime('%Y-%m-%d %H:%M')}</td></tr>"
        
        # File information
        if item.files:
            total_size = sum(f.file_size for f in item.files if f.file_size)
            if total_size:
                tooltip += f"<tr><td><b>Size:</b></td><td>{self._format_file_size(total_size)}</td></tr>"
        
        tooltip += "</table>"
        
        if item.description:
            desc = item.description[:200] + "..." if len(item.description) > 200 else item.description
            tooltip += f"<br><br><i>{desc}</i>"
        
        # Show tooltip at cursor position
        pos = self.viewport().mapToGlobal(self.visualRect(index).bottomLeft())
        QToolTip.showText(pos, tooltip, self)

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def _view_selected_items(self) -> None:
        """Handle view details action."""
        selected_items = self.get_selected_items()
        if selected_items:
            for item in selected_items:
                self.item_activated.emit(item)

    def _edit_selected_items(self) -> None:
        """Handle edit metadata action."""
        selected_items = self.get_selected_items()
        if selected_items:
            # This could emit a signal to open the metadata editor
            pass

    def contextMenuEvent(self, event) -> None:
        """Handle context menu request."""
        index = self.indexAt(event.pos())
        if index.isValid() and self._model:
            item = index.internalPointer()
            global_pos = event.globalPos()
            self.context_menu_requested.emit(item, global_pos)
            
            # Show context menu
            if not self._context_menu:
                self._context_menu = self.create_context_menu()
            self._context_menu.popup(global_pos)

    def keyPressEvent(self, event) -> None:
        """Handle key press events."""
        if event.key() == Qt.Key.Key_Delete:
            # Handle delete key (could trigger deletion or removal from library)
            pass
        elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Handle enter key (activate current item)
            current_item = self.get_current_item()
            if current_item:
                self.item_activated.emit(current_item)
        else:
            super().keyPressEvent(event)