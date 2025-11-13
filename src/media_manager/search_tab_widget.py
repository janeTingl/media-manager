"""Main search tab widget combining filters and results."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QSplitter,
)

from .logging import get_logger
from .search_filter_widget import SearchFilterWidget
from .search_results_widget import SearchResultsWidget
from .search_criteria import SearchCriteria
from .persistence.models import MediaItem


class SearchTabWidget(QWidget):
    """Main search tab with filters and results."""

    # Signals
    item_selected = Signal(MediaItem)
    item_activated = Signal(MediaItem)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the UI layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Create splitter for resizable panes
        splitter = QSplitter(Qt.Horizontal)

        # Left side - filter widget
        self.filter_widget = SearchFilterWidget()
        splitter.addWidget(self.filter_widget)

        # Right side - results widget
        self.results_widget = SearchResultsWidget()
        splitter.addWidget(self.results_widget)

        # Set splitter sizes (30% filters, 70% results)
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

    def _connect_signals(self) -> None:
        """Connect signals between components."""
        # Filter to results
        self.filter_widget.search_requested.connect(self.results_widget.search)
        
        # Results to parent
        self.results_widget.item_selected.connect(self.item_selected)
        self.results_widget.item_activated.connect(self.item_activated)

    def set_library_filter(self, library_id: int) -> None:
        """Set library filter for searches."""
        # Could be used to automatically filter by current library
        pass

    def get_results_model(self):
        """Get the search results model."""
        return self.results_widget.get_model()
