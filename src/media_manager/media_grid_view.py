"""Media grid view with icon mode and adaptive thumbnails."""

from __future__ import annotations

from typing import Optional

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPainter, QPixmap
from PySide6.QtWidgets import (
    QListView,
    QStyle,
    QStyleOptionViewItem,
    QWidget,
    QToolTip,
)

from .library_view_model import LibraryViewModel


class MediaGridView(QListView):
    """
    Grid view for media items with icon mode and adaptive thumbnails.
    
    Provides a visual grid layout with poster thumbnails and item information.
    Supports selection, hover effects, and context menus.
    """

    # Signals
    item_activated = Signal(object)  # MediaItem
    item_selected = Signal(object)  # MediaItem
    context_menu_requested = Signal(object, object)  # MediaItem, global_pos

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        # Setup view properties
        self.setViewMode(QListView.ViewMode.IconMode)
        self.setResizeMode(QListView.ResizeMode.Adjust)
        self.setFlow(QListView.Flow.LeftToRight)
        self.setWrapping(True)
        self.setGridSize(QSize(200, 280))  # Default grid size
        self.setIconSize(QSize(150, 225))   # Default icon size (2:3 aspect ratio)
        
        # Selection and interaction
        self.setSelectionMode(QListView.SelectionMode.ExtendedSelection)
        self.setSelectionBehavior(QListView.SelectionBehavior.SelectRows)
        self.setEditTriggers(QListView.EditTrigger.NoEditTriggers)
        self.setDragEnabled(True)
        self.setAcceptDrops(False)
        self.setDropIndicatorShown(True)
        
        # Appearance
        self.setSpacing(10)
        self.setUniformItemSizes(True)
        self.setTextElideMode(Qt.TextElideMode.ElideRight)
        self.setWordWrap(True)
        
        # Custom item delegate for better rendering
        self.setItemDelegate(MediaGridDelegate(self))
        
        # Model
        self._model: Optional[LibraryViewModel] = None
        
        # Connect signals
        self.clicked.connect(self._on_item_clicked)
        self.doubleClicked.connect(self._on_item_double_clicked)
        self.entered.connect(self._on_item_entered)

    def set_model(self, model: LibraryViewModel) -> None:
        """Set the view model."""
        self._model = model
        self.setModel(model)

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

    def adjust_grid_size(self, thumbnail_size: QSize) -> None:
        """Adjust grid size based on thumbnail size."""
        padding = 20  # Padding around thumbnail
        text_height = 40  # Space for title text
        
        grid_width = thumbnail_size.width() + padding
        grid_height = thumbnail_size.height() + text_height + padding
        
        self.setGridSize(QSize(grid_width, grid_height))
        self.setIconSize(thumbnail_size)

    def set_thumbnail_size(self, size: str) -> None:
        """Set thumbnail size preset."""
        sizes = {
            "small": QSize(100, 150),
            "medium": QSize(150, 225),
            "large": QSize(200, 300),
            "extra_large": QSize(250, 375)
        }
        
        thumbnail_size = sizes.get(size, sizes["medium"])
        self.adjust_grid_size(thumbnail_size)

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
            # Show enhanced tooltip with more details
            self._show_item_tooltip(item, index)

    def _show_item_tooltip(self, item, index) -> None:
        """Show enhanced tooltip for media item."""
        if not item:
            return
        
        # Build tooltip content
        tooltip = f"<b>{item.title}</b><br>"
        if item.year:
            tooltip += f"Year: {item.year}<br>"
        if item.media_type:
            tooltip += f"Type: {item.media_type.capitalize()}<br>"
        if item.rating:
            tooltip += f"Rating: {item.rating:.1f}/10<br>"
        if item.runtime:
            hours = item.runtime // 60
            minutes = item.runtime % 60
            runtime_str = f"{hours}h {minutes}m" if hours else f"{minutes}m"
            tooltip += f"Duration: {runtime_str}<br>"
        if item.description:
            desc = item.description[:150] + "..." if len(item.description) > 150 else item.description
            tooltip += f"<br><i>{desc}</i>"
        
        # Show tooltip at cursor position
        pos = self.viewport().mapToGlobal(self.visualRect(index).bottomLeft())
        QToolTip.showText(pos, tooltip, self)

    def contextMenuEvent(self, event) -> None:
        """Handle context menu request."""
        index = self.indexAt(event.pos())
        if index.isValid() and self._model:
            item = index.internalPointer()
            global_pos = event.globalPos()
            self.context_menu_requested.emit(item, global_pos)


class MediaGridDelegate:
    """
    Custom delegate for rendering media items in grid view.
    
    Provides enhanced visual appearance with posters, titles, and metadata.
    """
    
    def __init__(self, parent: MediaGridView) -> None:
        self._parent = parent
        self._default_poster = None

    def paint(self, painter: QPainter, option: QStyleOptionViewItem, index) -> None:
        """Paint the media item in the grid."""
        # Get the media item
        item = index.internalPointer()
        if not item:
            return
        
        # Draw background
        self._draw_background(painter, option)
        
        # Draw poster thumbnail
        self._draw_poster(painter, option, index, item)
        
        # Draw title and metadata
        self._draw_text(painter, option, item)
        
        # Draw selection/hover effects
        self._draw_effects(painter, option)

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:
        """Return the size hint for the item."""
        return self._parent.gridSize()

    def _draw_background(self, painter: QPainter, option: QStyleOptionViewItem) -> None:
        """Draw item background."""
        # Use the default style to draw selection and hover states
        style = self._parent.style()
        style.drawControl(QStyle.ControlElement.CE_ItemViewItem, option, painter, self._parent)

    def _draw_poster(self, painter: QPainter, option: QStyleOptionViewItem, index, item) -> None:
        """Draw poster thumbnail."""
        rect = option.rect
        icon_size = self._parent.iconSize()
        
        # Calculate poster position (centered at top)
        poster_x = rect.left() + (rect.width() - icon_size.width()) // 2
        poster_y = rect.top() + 5
        poster_rect = poster_x, poster_y, icon_size.width(), icon_size.height()
        
        # Get poster pixmap
        pixmap = self._get_poster_pixmap(index, item, icon_size)
        if pixmap:
            painter.drawPixmap(*poster_rect, pixmap)
        else:
            # Draw placeholder
            self._draw_poster_placeholder(painter, *poster_rect, item)

    def _draw_text(self, painter: QPainter, option: QStyleOptionViewItem, item) -> None:
        """Draw title and metadata text."""
        rect = option.rect
        icon_size = self._parent.iconSize()
        
        # Text area starts below the poster
        text_y = rect.top() + icon_size.height() + 10
        text_rect = rect.left() + 5, text_y, rect.width() - 10, rect.height() - text_y - 5
        
        # Set text color based on selection state
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(self._parent.palette().highlightedText().color())
        else:
            painter.setPen(self._parent.palette().text().color())
        
        # Draw title
        title = item.title or "Unknown"
        if item.media_type == "tv" and item.season and item.episode:
            title += f"\nS{item.season:02d}E{item.episode:02d}"
        
        painter.drawText(*text_rect, Qt.TextFlag.TextWordWrap | Qt.AlignmentFlag.AlignCenter, title)

    def _draw_effects(self, painter: QPainter, option: QStyleOptionViewItem) -> None:
        """Draw selection and hover effects."""
        # Additional visual effects can be added here
        pass

    def _get_poster_pixmap(self, index, item, size: QSize) -> Optional[QPixmap]:
        """Get poster pixmap for the item."""
        # Try to get poster from model
        model = index.model()
        if model:
            poster_path = model.data(index, model.PosterRole)
            if poster_path:
                pixmap = QPixmap(poster_path)
                if not pixmap.isNull():
                    return pixmap.scaled(size, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        return None

    def _draw_poster_placeholder(self, painter: QPainter, x: int, y: int, width: int, height: int, item) -> None:
        """Draw placeholder when no poster is available."""
        # Draw a simple placeholder rectangle with gradient
        from PySide6.QtCore import QRect, Qt
        from PySide6.QtGui import QColor, QLinearGradient, QPen
        
        rect = QRect(x, y, width, height)
        
        # Create gradient based on media type
        gradient = QLinearGradient(rect.topLeft(), rect.bottomRight())
        if item.media_type == "movie":
            gradient.setColorAt(0, QColor(52, 152, 219))  # Blue
            gradient.setColorAt(1, QColor(41, 128, 185))  # Darker blue
        else:  # TV
            gradient.setColorAt(0, QColor(155, 89, 182))  # Purple
            gradient.setColorAt(1, QColor(142, 68, 173))  # Darker purple
        
        painter.fillRect(rect, gradient)
        
        # Draw border
        painter.setPen(QPen(QColor(255, 255, 255, 100), 2))
        painter.drawRect(rect)
        
        # Draw media type icon/text
        painter.setPen(QColor(255, 255, 255))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, item.media_type.upper())