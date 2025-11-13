"""Search results widget with grid and table views."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QToolBar,
    QLabel,
    QPushButton,
    QStackedWidget,
    QComboBox,
)

from .logging import get_logger
from .media_grid_view import MediaGridView
from .media_table_view import MediaTableView
from .search_results_model import SearchResultsModel
from .search_criteria import SearchCriteria
from .persistence.models import MediaItem


class SearchResultsWidget(QWidget):
    """Widget for displaying search results in grid or table view."""

    # Signals
    item_selected = Signal(MediaItem)
    item_activated = Signal(MediaItem)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        
        # Create model
        self._model = SearchResultsModel()
        
        # Current view mode
        self._current_view = "grid"
        
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the UI layout."""
        layout = QVBoxLayout(self)

        # Toolbar
        toolbar = QToolBar()
        toolbar.setMovable(False)

        # View mode buttons
        self.grid_btn = QPushButton("Grid View")
        self.grid_btn.setCheckable(True)
        self.grid_btn.setChecked(True)
        self.grid_btn.clicked.connect(lambda: self._switch_view("grid"))
        toolbar.addWidget(self.grid_btn)

        self.table_btn = QPushButton("Table View")
        self.table_btn.setCheckable(True)
        self.table_btn.clicked.connect(lambda: self._switch_view("table"))
        toolbar.addWidget(self.table_btn)

        toolbar.addSeparator()

        # Thumbnail size controls (for grid view)
        toolbar.addWidget(QLabel("Size:"))
        self.size_combo = QComboBox()
        self.size_combo.addItems(["Small", "Medium", "Large", "Extra Large"])
        self.size_combo.setCurrentIndex(1)  # Default to Medium
        self.size_combo.currentTextChanged.connect(self._on_size_changed)
        toolbar.addWidget(self.size_combo)

        toolbar.addSeparator()

        # Results count label
        self.results_label = QLabel("No results")
        toolbar.addWidget(self.results_label)

        toolbar.addSeparator()

        # Pagination controls
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self._on_previous_page)
        self.prev_btn.setEnabled(False)
        toolbar.addWidget(self.prev_btn)

        self.page_label = QLabel("Page 1")
        toolbar.addWidget(self.page_label)

        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self._on_next_page)
        self.next_btn.setEnabled(False)
        toolbar.addWidget(self.next_btn)

        layout.addWidget(toolbar)

        # Stacked widget for view switching
        self.view_stack = QStackedWidget()

        # Create grid view
        self.grid_view = MediaGridView()
        self.grid_view.set_model(self._model)
        self.view_stack.addWidget(self.grid_view)

        # Create table view
        self.table_view = MediaTableView()
        self.table_view.set_model(self._model)
        self.view_stack.addWidget(self.table_view)

        layout.addWidget(self.view_stack)

        # Current criteria for pagination
        self._current_criteria = SearchCriteria()
        self._current_page = 0
        self._total_pages = 0

    def _connect_signals(self) -> None:
        """Connect signals."""
        self._model.search_started.connect(self._on_search_started)
        self._model.search_finished.connect(self._on_search_finished)
        self._model.error_occurred.connect(self._on_error)

        # Grid view signals
        self.grid_view.item_selected.connect(self.item_selected)
        self.grid_view.item_activated.connect(self.item_activated)

        # Table view signals
        self.table_view.item_selected.connect(self.item_selected)
        self.table_view.item_activated.connect(self.item_activated)

    def search(self, criteria: SearchCriteria) -> None:
        """Execute search with given criteria."""
        self._current_criteria = criteria
        self._current_page = criteria.page
        self._model.search(criteria)

    def get_model(self) -> SearchResultsModel:
        """Get the results model."""
        return self._model

    def _switch_view(self, view_mode: str) -> None:
        """Switch between grid and table view."""
        self._current_view = view_mode

        if view_mode == "grid":
            self.view_stack.setCurrentIndex(0)
            self.grid_btn.setChecked(True)
            self.table_btn.setChecked(False)
            self.size_combo.setEnabled(True)
        else:
            self.view_stack.setCurrentIndex(1)
            self.grid_btn.setChecked(False)
            self.table_btn.setChecked(True)
            self.size_combo.setEnabled(False)

    def _on_size_changed(self, size_text: str) -> None:
        """Handle thumbnail size change."""
        size_map = {
            "Small": "small",
            "Medium": "medium",
            "Large": "large",
            "Extra Large": "extra_large",
        }
        size = size_map.get(size_text, "medium")
        self.grid_view.set_thumbnail_size(size)

    def _on_search_started(self) -> None:
        """Handle search started."""
        self.results_label.setText("Searching...")
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)

    def _on_search_finished(self, total_count: int) -> None:
        """Handle search finished."""
        result_count = self._model.rowCount()
        
        # Update results label
        if total_count == 0:
            self.results_label.setText("No results")
        elif result_count == total_count:
            self.results_label.setText(f"{total_count} result(s)")
        else:
            page_start = self._current_page * self._current_criteria.page_size + 1
            page_end = min(page_start + result_count - 1, total_count)
            self.results_label.setText(
                f"Showing {page_start}-{page_end} of {total_count} result(s)"
            )

        # Update pagination
        self._total_pages = (
            (total_count + self._current_criteria.page_size - 1)
            // self._current_criteria.page_size
        )
        self.page_label.setText(f"Page {self._current_page + 1} of {self._total_pages}")
        
        self.prev_btn.setEnabled(self._current_page > 0)
        self.next_btn.setEnabled(self._current_page < self._total_pages - 1)

    def _on_error(self, error_msg: str) -> None:
        """Handle search error."""
        self.results_label.setText(f"Error: {error_msg}")
        self._logger.error(f"Search error: {error_msg}")

    def _on_previous_page(self) -> None:
        """Go to previous page."""
        if self._current_page > 0:
            self._current_criteria.page = self._current_page - 1
            self.search(self._current_criteria)

    def _on_next_page(self) -> None:
        """Go to next page."""
        if self._current_page < self._total_pages - 1:
            self._current_criteria.page = self._current_page + 1
            self.search(self._current_criteria)

    def clear(self) -> None:
        """Clear results."""
        self._model.clear()
        self.results_label.setText("No results")
        self.page_label.setText("Page 1")
        self.prev_btn.setEnabled(False)
        self.next_btn.setEnabled(False)
        self._current_page = 0
        self._total_pages = 0
