"""Lazy-loading model for efficient UI list rendering."""

from __future__ import annotations

from typing import Any, Callable, List, Optional

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Signal, Slot

from .instrumentation import get_instrumentation
from .logging import get_logger
from .persistence.repositories import MediaItemRepository

logger_instance = get_logger()
logger = logger_instance.get_logger(__name__)


class LazyListModel(QAbstractListModel):
    """Abstract lazy-loading list model with pagination support."""

    loadMoreRequested = Signal()
    loadingStateChanged = Signal(bool)

    def __init__(
        self,
        parent: Any = None,
        page_size: int = 100,
        prefetch_threshold: int = 20,
    ) -> None:
        """Initialize lazy list model.

        Args:
            parent: Parent QObject
            page_size: Number of items to load per page
            prefetch_threshold: Number of items from end to trigger prefetch
        """
        super().__init__(parent)
        self.page_size = page_size
        self.prefetch_threshold = prefetch_threshold
        self._items: List[Any] = []
        self._total_count: Optional[int] = None
        self._is_loading = False
        self._current_offset = 0
        self._instrumentation = get_instrumentation()

    @property
    def is_loading(self) -> bool:
        """Whether the model is currently loading data."""
        return self._is_loading

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Return the number of rows in the model."""
        if parent.isValid():
            return 0
        return len(self._items)

    def canFetchMore(self, parent: QModelIndex = QModelIndex()) -> bool:
        """Check if more data can be fetched."""
        if parent.isValid() or self._is_loading:
            return False

        # Can fetch more if we don't know total count or have more items
        if self._total_count is None:
            return True

        return len(self._items) < self._total_count

    def fetchMore(self, parent: QModelIndex = QModelIndex()) -> None:
        """Fetch more data when needed."""
        if parent.isValid() or self._is_loading:
            return

        if not self.canFetchMore(parent):
            return

        with self._instrumentation.timer("lazy_model.fetch_more"):
            self._is_loading = True
            self.loadingStateChanged.emit(True)
            self.loadMoreRequested.emit()

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        """Get data for a specific index and role."""
        if not index.isValid() or index.row() >= len(self._items):
            return None

        # Check if we should prefetch more data
        if (
            not self._is_loading
            and self.canFetchMore()
            and index.row() >= len(self._items) - self.prefetch_threshold
        ):
            self.fetchMore()

        return self.get_item_data(self._items[index.row()], role)

    def get_item_data(self, item: Any, role: int) -> Any:
        """Get data for a specific item and role.

        Subclasses should override this method.

        Args:
            item: The item
            role: Qt display role

        Returns:
            Data for the role
        """
        raise NotImplementedError

    def clear(self) -> None:
        """Clear all items from the model."""
        if self._items:
            self.beginResetModel()
            self._items.clear()
            self._total_count = None
            self._current_offset = 0
            self._is_loading = False
            self.endResetModel()

    def set_total_count(self, count: int) -> None:
        """Set the total number of items available.

        Args:
            count: Total item count
        """
        self._total_count = count

    def append_items(self, items: List[Any]) -> None:
        """Append items to the model.

        Args:
            items: Items to append
        """
        if not items:
            self._is_loading = False
            self.loadingStateChanged.emit(False)
            return

        with self._instrumentation.timer("lazy_model.append_items"):
            start_row = len(self._items)
            end_row = start_row + len(items) - 1

            self.beginInsertRows(QModelIndex(), start_row, end_row)
            self._items.extend(items)
            self._current_offset += len(items)
            self.endInsertRows()

            self._is_loading = False
            self.loadingStateChanged.emit(False)

            self._instrumentation.increment_counter(
                "lazy_model.items_loaded", value=len(items)
            )

    def get_item(self, row: int) -> Optional[Any]:
        """Get item at a specific row.

        Args:
            row: Row index

        Returns:
            Item or None
        """
        if 0 <= row < len(self._items):
            return self._items[row]
        return None


class LazyMediaItemModel(LazyListModel):
    """Lazy-loading model for media items."""

    def __init__(
        self,
        parent: Any = None,
        page_size: int = 100,
        prefetch_threshold: int = 20,
        library_id: Optional[int] = None,
    ) -> None:
        """Initialize lazy media item model.

        Args:
            parent: Parent QObject
            page_size: Number of items to load per page
            prefetch_threshold: Number of items from end to trigger prefetch
            library_id: Optional library ID to filter by
        """
        super().__init__(parent, page_size, prefetch_threshold)
        self.library_id = library_id
        self._repository = MediaItemRepository()

        # Connect load signal to loading function
        self.loadMoreRequested.connect(self._load_next_page)

    def set_library(self, library_id: Optional[int]) -> None:
        """Set the library to load items from.

        Args:
            library_id: Library ID or None for all libraries
        """
        if self.library_id != library_id:
            self.clear()
            self.library_id = library_id
            self._load_total_count()
            self.fetchMore()

    @Slot()
    def _load_next_page(self) -> None:
        """Load the next page of items."""
        try:
            with self._instrumentation.timer("lazy_media_model.load_page"):
                if self.library_id is not None:
                    items = self._repository.get_by_library(
                        self.library_id,
                        limit=self.page_size,
                        offset=self._current_offset,
                        lazy_load=True,  # Use lazy loading for better performance
                    )
                else:
                    items = self._repository.get_all(
                        limit=self.page_size,
                        offset=self._current_offset,
                        lazy_load=True,
                    )

                self.append_items(items)
                logger.debug(
                    f"Loaded page: offset={self._current_offset}, "
                    f"count={len(items)}, total={len(self._items)}"
                )

        except Exception as e:
            logger.error(f"Failed to load media items: {e}")
            self._is_loading = False
            self.loadingStateChanged.emit(False)

    def _load_total_count(self) -> None:
        """Load the total count of items."""
        try:
            if self.library_id is not None:
                count = self._repository.count_by_library(self.library_id)
            else:
                count = self._repository.count_all()

            self.set_total_count(count)
            logger.debug(f"Total item count: {count}")

        except Exception as e:
            logger.error(f"Failed to load total count: {e}")

    def get_item_data(self, item: Any, role: int) -> Any:
        """Get data for a specific media item and role.

        Args:
            item: MediaItem
            role: Qt display role

        Returns:
            Data for the role
        """
        if role == Qt.DisplayRole:
            return item.title
        elif role == Qt.UserRole:
            return item
        elif role == Qt.UserRole + 1:  # Year
            return item.year
        elif role == Qt.UserRole + 2:  # Media type
            return item.media_type
        elif role == Qt.UserRole + 3:  # Rating
            return item.rating
        elif role == Qt.UserRole + 4:  # Description
            return item.description

        return None

    def refresh(self) -> None:
        """Refresh the model by reloading from the beginning."""
        self.clear()
        self._load_total_count()
        self.fetchMore()


class VirtualScrollDelegate:
    """Helper class for virtual scrolling calculations."""

    def __init__(self, item_height: int = 50, viewport_height: int = 600) -> None:
        """Initialize virtual scroll delegate.

        Args:
            item_height: Height of each item in pixels
            viewport_height: Height of the viewport in pixels
        """
        self.item_height = item_height
        self.viewport_height = viewport_height

    def visible_range(self, scroll_position: int, total_items: int) -> tuple[int, int]:
        """Calculate the range of visible items.

        Args:
            scroll_position: Current scroll position in pixels
            total_items: Total number of items

        Returns:
            Tuple of (start_index, end_index)
        """
        start_index = max(0, scroll_position // self.item_height)
        visible_count = (self.viewport_height // self.item_height) + 2  # +2 for buffer
        end_index = min(total_items, start_index + visible_count)

        return start_index, end_index

    def should_load_more(
        self, scroll_position: int, total_items: int, loaded_items: int
    ) -> bool:
        """Check if more items should be loaded.

        Args:
            scroll_position: Current scroll position
            total_items: Total number of items
            loaded_items: Number of items currently loaded

        Returns:
            True if more items should be loaded
        """
        start_index, end_index = self.visible_range(scroll_position, total_items)

        # Load more if we're close to the end of loaded items
        threshold = loaded_items - 20
        return end_index >= threshold and loaded_items < total_items
