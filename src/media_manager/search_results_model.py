"""Search results model for displaying search results."""

from typing import Any, List, Optional

from PySide6.QtCore import QAbstractItemModel, QModelIndex, Qt, Signal

from .logging import get_logger
from .persistence.models import MediaItem
from .search_criteria import SearchCriteria
from .search_service import SearchService


class SearchResultsModel(QAbstractItemModel):
    """Model for displaying search results."""

    # Signals
    search_started = Signal()
    search_finished = Signal(int)  # total count
    error_occurred = Signal(str)

    # Custom roles
    MediaItemRole = Qt.UserRole + 1
    PosterRole = Qt.UserRole + 2
    RatingRole = Qt.UserRole + 3
    YearRole = Qt.UserRole + 4
    MediaTypeRole = Qt.UserRole + 5

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)

        # Data storage
        self._items: List[MediaItem] = []
        self._total_count = 0

        # Search service
        self._search_service = SearchService()

        # Current criteria
        self._criteria = SearchCriteria()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows."""
        if parent.isValid():
            return 0
        return len(self._items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of columns."""
        if parent.isValid():
            return 0
        return 8  # Same as LibraryViewModel

    def index(self, row: int, column: int, parent: QModelIndex = QModelIndex()) -> QModelIndex:
        """Create a model index."""
        if parent.isValid() or row < 0 or row >= len(self._items):
            return QModelIndex()
        return self.createIndex(row, column, self._items[row])

    def parent(self, child: QModelIndex) -> QModelIndex:
        """Return parent index (always invalid for flat model)."""
        return QModelIndex()

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
            return None  # Could return icons
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
        """Return header data."""
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
            "Status",
        ]

        if 0 <= section < len(headers):
            return headers[section]

        return None

    def search(self, criteria: SearchCriteria) -> None:
        """Execute search with given criteria."""
        self.search_started.emit()
        self._criteria = criteria

        try:
            # Execute search
            results, total_count = self._search_service.search(criteria)

            # Update model data
            self.beginResetModel()
            self._items = results
            self._total_count = total_count
            self.endResetModel()

            self.search_finished.emit(total_count)
            self._logger.info(f"Search completed: {len(results)} results (total: {total_count})")

        except Exception as e:
            error_msg = f"Search failed: {str(e)}"
            self._logger.error(error_msg)
            self.error_occurred.emit(error_msg)
            self.beginResetModel()
            self._items = []
            self._total_count = 0
            self.endResetModel()

    def get_item_at_row(self, row: int) -> Optional[MediaItem]:
        """Get the media item at the given row."""
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    def get_total_count(self) -> int:
        """Get total number of results (before pagination)."""
        return self._total_count

    def get_current_criteria(self) -> SearchCriteria:
        """Get current search criteria."""
        return self._criteria

    def clear(self) -> None:
        """Clear all results."""
        self.beginResetModel()
        self._items = []
        self._total_count = 0
        self._criteria = SearchCriteria()
        self.endResetModel()

    def _get_display_data(self, item: MediaItem, column: int) -> str:
        """Get display data for column."""
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
            total_size = sum(f.file_size for f in item.files if f.file_size)
            if total_size:
                for unit in ["B", "KB", "MB", "GB"]:
                    if total_size < 1024:
                        return f"{total_size:.1f} {unit}"
                    total_size /= 1024
                return f"{total_size:.1f} TB"
            return ""
        elif column == 7:  # Status
            return "Available"

        return ""

    def _get_tooltip_data(self, item: MediaItem) -> str:
        """Get tooltip text."""
        tooltip = f"<b>{item.title}</b><br>"
        if item.year:
            tooltip += f"Year: {item.year}<br>"
        if item.media_type:
            tooltip += f"Type: {item.media_type.capitalize()}<br>"
        if item.rating:
            tooltip += f"Rating: {item.rating:.1f}/10<br>"
        if item.description:
            desc = item.description[:100] + "..." if len(item.description) > 100 else item.description
            tooltip += f"<br>{desc}"
        return tooltip

    def _get_alignment_data(self, column: int) -> Qt.AlignmentFlag:
        """Get text alignment."""
        if column in [1, 3, 4, 6]:  # Year, Rating, Duration, Size
            return Qt.AlignRight | Qt.AlignVCenter
        return Qt.AlignLeft | Qt.AlignVCenter

    def _get_poster_data(self, item: MediaItem) -> Optional[str]:
        """Get poster URL/path."""
        for artwork in item.artworks:
            if artwork.artwork_type == "poster":
                return artwork.local_path or artwork.url
        return None
