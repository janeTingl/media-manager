"""Library view model implementing QAbstractItemModel for media items."""

from __future__ import annotations

from typing import Any, Optional

from PySide6.QtCore import (
    QAbstractItemModel,
    QModelIndex,
    Qt,
    Signal,
)
from PySide6.QtGui import QIcon

from media_manager.logging import get_logger
from media_manager.persistence.models import MediaItem
from media_manager.persistence.repositories import MediaItemRepository


class LibraryViewModel(QAbstractItemModel):
    """
    View model for media library items implementing QAbstractItemModel.
    
    Provides data binding between the persistence layer and UI views.
    Supports sorting, grouping, and lazy loading of media items.
    """

    # Signals
    data_loaded = Signal(int)  # Emitted when data is loaded with item count
    loading_started = Signal()
    loading_finished = Signal()
    error_occurred = Signal(str)

    # Custom roles for additional data
    MediaItemRole = Qt.UserRole + 1
    PosterRole = Qt.UserRole + 2
    RatingRole = Qt.UserRole + 3
    YearRole = Qt.UserRole + 4
    MediaTypeRole = Qt.UserRole + 5

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        
        # Data storage
        self._items: list[MediaItem] = []
        self._filtered_items: list[MediaItem] = []
        
        # Repository for data access
        self._repository = MediaItemRepository()
        
        # Filtering and sorting
        self._filter_text = ""
        self._sort_column = 0  # Default to title
        self._sort_order = Qt.AscendingOrder
        self._media_type_filter = "all"  # "all", "movie", "tv"
        self._library_filter: Optional[int] = None  # Filter by library ID
        
        # Lazy loading
        self._page_size = 50
        self._current_page = 0
        self._total_count = 0
        self._loading = False

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows under the given parent."""
        if parent.isValid():
            return 0
        return len(self._filtered_items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns under the given parent."""
        if parent.isValid():
            return 0
        return 8  # Title, Year, Type, Rating, Duration, Added, Size, Status

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """Create a model index for the given row and column."""
        if parent.isValid() or row < 0 or row >= len(self._filtered_items):
            return QModelIndex()
        
        return self.createIndex(row, column, self._filtered_items[row])

    def parent(self, child: QModelIndex) -> QModelIndex:
        """Return the parent of the given child index."""
        return QModelIndex()  # Flat model, no parent-child relationships

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Return data for the given index and role."""
        if not index.isValid():
            return None

        item = index.internalPointer()
        if not isinstance(item, MediaItem):
            return None

        column = index.column()

        if role == Qt.DisplayRole:
            return self._get_display_data(item, column)
        elif role == Qt.DecorationRole and column == 0:
            return self._get_decoration_data(item)
        elif role == Qt.ToolTipRole:
            return self._get_tooltip_data(item)
        elif role == Qt.TextAlignmentRole:
            return self._get_alignment_data(column)
        elif role == self.MediaItemRole:
            return item
        elif role == self.PosterRole:
            return self._get_poster_data(item)
        elif role == self.RatingRole:
            return item.rating
        elif role == self.YearRole:
            return item.year
        elif role == self.MediaTypeRole:
            return item.media_type

        return None

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole) -> Any:
        """Return header data for the given section."""
        if orientation != Qt.Horizontal or role != Qt.DisplayRole:
            return None

        headers = [
            "Title",
            "Year", 
            "Type",
            "Rating",
            "Duration",
            "Added",
            "Size",
            "Status"
        ]
        
        if 0 <= section < len(headers):
            return headers[section]
        
        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.AscendingOrder) -> None:
        """Sort the model by column and order."""
        self.layoutAboutToBeChanged.emit()
        
        self._sort_column = column
        self._sort_order = order
        
        # Sort the filtered items
        reverse = order == Qt.DescendingOrder
        if column == 0:  # Title
            self._filtered_items.sort(key=lambda x: x.title or "", reverse=reverse)
        elif column == 1:  # Year
            self._filtered_items.sort(key=lambda x: x.year or 0, reverse=reverse)
        elif column == 2:  # Type
            self._filtered_items.sort(key=lambda x: x.media_type, reverse=reverse)
        elif column == 3:  # Rating
            self._filtered_items.sort(key=lambda x: x.rating or 0, reverse=reverse)
        elif column == 4:  # Duration
            self._filtered_items.sort(key=lambda x: x.runtime or 0, reverse=reverse)
        elif column == 5:  # Added
            self._filtered_items.sort(key=lambda x: x.created_at, reverse=reverse)
        
        self.layoutChanged.emit()

    def load_data(self, library_id: Optional[int] = None, force_reload: bool = False) -> None:
        """Load media items from the repository."""
        if self._loading and not force_reload:
            return
        
        self._loading = True
        self.loading_started.emit()
        
        try:
            # Use library_filter if set, otherwise use the parameter
            filter_library_id = library_id if library_id is not None else self._library_filter
            
            # Fetch items from repository
            if filter_library_id:
                self._items = self._repository.get_by_library(filter_library_id)
            else:
                self._items = self._repository.get_all()
            
            self._total_count = len(self._items)
            
            # Apply current filters
            self._apply_filters()
            
            self.data_loaded.emit(len(self._filtered_items))
            self._logger.info(f"Loaded {len(self._filtered_items)} media items")
            
        except Exception as e:
            error_msg = f"Failed to load data: {str(e)}"
            self._logger.error(error_msg)
            self.error_occurred.emit(error_msg)
        finally:
            self._loading = False
            self.loading_finished.emit()

    def set_filter(self, filter_text: str) -> None:
        """Set text filter and update the view."""
        self._filter_text = filter_text.lower()
        self._apply_filters()

    def set_media_type_filter(self, media_type: str) -> None:
        """Set media type filter ('all', 'movie', 'tv')."""
        self._media_type_filter = media_type
        self._apply_filters()

    def set_library_filter(self, library_id: Optional[int]) -> None:
        """Set library filter and reload data."""
        self._library_filter = library_id
        self.load_data()

    def clear_filters(self) -> None:
        """Clear all filters and reload data."""
        self._filter_text = ""
        self._media_type_filter = "all"
        self._library_filter = None
        self.load_data()

    def _apply_filters(self) -> None:
        """Apply current filters to the items."""
        self.layoutAboutToBeChanged.emit()
        
        self._filtered_items = []
        
        for item in self._items:
            # Media type filter
            if self._media_type_filter != "all":
                if item.media_type != self._media_type_filter:
                    continue
            
            # Text filter
            if self._filter_text:
                text = self._filter_text.lower()
                title_match = item.title and text in item.title.lower()
                desc_match = item.description and text in item.description.lower()
                year_match = str(item.year) and text in str(item.year)
                
                if not (title_match or desc_match or year_match):
                    continue
            
            self._filtered_items.append(item)
        
        # Apply current sort
        self.sort(self._sort_column, self._sort_order)
        
        self.layoutChanged.emit()

    def _get_display_data(self, item: MediaItem, column: int) -> str:
        """Get display data for the given column."""
        if column == 0:  # Title
            title = item.title or "Unknown"
            if item.media_type == "tv" and item.season and item.episode:
                title += f" S{item.season:02d}E{item.episode:02d}"
            return title
        elif column == 1:  # Year
            return str(item.year) if item.year else ""
        elif column == 2:  # Type
            return item.media_type.capitalize() if item.media_type else ""
        elif column == 3:  # Rating
            return f"{item.rating:.1f}" if item.rating else ""
        elif column == 4:  # Duration
            if item.runtime:
                hours = item.runtime // 60
                minutes = item.runtime % 60
                return f"{hours}h {minutes}m" if hours else f"{minutes}m"
            return ""
        elif column == 5:  # Added
            return item.created_at.strftime("%Y-%m-%d") if item.created_at else ""
        elif column == 6:  # Size
            # Calculate size from files
            total_size = sum(f.file_size for f in item.files if f.file_size)
            if total_size:
                for unit in ['B', 'KB', 'MB', 'GB']:
                    if total_size < 1024:
                        return f"{total_size:.1f} {unit}"
                    total_size /= 1024
                return f"{total_size:.1f} TB"
            return ""
        elif column == 7:  # Status
            # Could indicate match status, watch status, etc.
            return "Available"
        
        return ""

    def _get_decoration_data(self, item: MediaItem) -> Optional[QIcon]:
        """Get decoration (icon) for the item."""
        # Return different icons based on media type
        # This could be enhanced to return thumbnail icons
        return None

    def _get_tooltip_data(self, item: MediaItem) -> str:
        """Get tooltip text for the item."""
        tooltip = f"<b>{item.title}</b><br>"
        if item.year:
            tooltip += f"Year: {item.year}<br>"
        if item.media_type:
            tooltip += f"Type: {item.media_type.capitalize()}<br>"
        if item.description:
            # Truncate long descriptions
            desc = item.description[:100] + "..." if len(item.description) > 100 else item.description
            tooltip += f"<br>{desc}"
        return tooltip

    def _get_alignment_data(self, column: int) -> Qt.AlignmentFlag:
        """Get text alignment for the column."""
        if column in [1, 3, 4, 6]:  # Year, Rating, Duration, Size
            return Qt.AlignRight | Qt.AlignVCenter
        return Qt.AlignLeft | Qt.AlignVCenter

    def _get_poster_data(self, item: MediaItem) -> Optional[str]:
        """Get poster URL/path for the item."""
        # Look for poster artwork
        for artwork in item.artworks:
            if artwork.artwork_type == "poster":
                return artwork.local_path or artwork.url
        return None

    def get_item_at_row(self, row: int) -> Optional[MediaItem]:
        """Get the media item at the given row."""
        if 0 <= row < len(self._filtered_items):
            return self._filtered_items[row]
        return None

    def get_items_for_indices(self, indices: list[QModelIndex]) -> list[MediaItem]:
        """Get media items for the given model indices."""
        items = []
        for index in indices:
            if index.isValid():
                item = index.internalPointer()
                if isinstance(item, MediaItem):
                    items.append(item)
        return items

    def refresh(self) -> None:
        """Refresh the data from the repository."""
        self.load_data(force_reload=True)

    def is_loading(self) -> bool:
        """Check if data is currently loading."""
        return self._loading

    def total_count(self) -> int:
        """Get total number of items (before filtering)."""
        return self._total_count

    def filtered_count(self) -> int:
        """Get number of items after filtering."""
        return len(self._filtered_items)