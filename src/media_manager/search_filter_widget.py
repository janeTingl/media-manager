"""Search filter widget with advanced filtering controls."""

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QComboBox,
    QPushButton,
    QSlider,
    QGroupBox,
    QCheckBox,
    QScrollArea,
    QListWidget,
    QListWidgetItem,
    QSpinBox,
    QDoubleSpinBox,
    QFormLayout,
    QInputDialog,
    QMessageBox,
)

from .logging import get_logger
from .search_criteria import SearchCriteria
from .search_service import SearchService
from .persistence.models import Tag, Person, Collection, SavedSearch


class SearchFilterWidget(QWidget):
    """Widget for advanced search filtering."""

    # Signals
    search_requested = Signal(SearchCriteria)
    criteria_changed = Signal(SearchCriteria)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._search_service = SearchService()
        
        self._setup_ui()
        self._load_filter_options()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the UI layout."""
        layout = QVBoxLayout(self)

        # Scroll area for filters
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # Text search
        text_group = QGroupBox("Text Search")
        text_layout = QVBoxLayout(text_group)
        self.text_input = QLineEdit()
        self.text_input.setPlaceholderText("Search title or description...")
        text_layout.addWidget(self.text_input)
        scroll_layout.addWidget(text_group)

        # Quick filters
        quick_group = QGroupBox("Quick Filters")
        quick_layout = QVBoxLayout(quick_group)
        
        quick_buttons_layout = QHBoxLayout()
        self.quick_filter_buttons = {}
        for filter_name, display_name in [
            ("unmatched", "Unmatched"),
            ("recent", "Recently Added"),
            ("favorites", "Favorites"),
            ("no_poster", "No Poster"),
            ("high_rated", "High Rated (8+)"),
        ]:
            btn = QPushButton(display_name)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, f=filter_name: self._on_quick_filter_clicked(f, checked))
            self.quick_filter_buttons[filter_name] = btn
            quick_buttons_layout.addWidget(btn)
        
        quick_layout.addLayout(quick_buttons_layout)
        scroll_layout.addWidget(quick_group)

        # Media type filter
        type_group = QGroupBox("Media Type")
        type_layout = QHBoxLayout(type_group)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["All", "Movies", "TV Shows"])
        type_layout.addWidget(self.type_combo)
        scroll_layout.addWidget(type_group)

        # Year range
        year_group = QGroupBox("Year Range")
        year_layout = QFormLayout(year_group)
        
        self.year_min_spin = QSpinBox()
        self.year_min_spin.setRange(1900, 2100)
        self.year_min_spin.setValue(1900)
        self.year_min_spin.setSpecialValueText("Any")
        
        self.year_max_spin = QSpinBox()
        self.year_max_spin.setRange(1900, 2100)
        self.year_max_spin.setValue(2100)
        self.year_max_spin.setSpecialValueText("Any")
        
        year_layout.addRow("From:", self.year_min_spin)
        year_layout.addRow("To:", self.year_max_spin)
        scroll_layout.addWidget(year_group)

        # Rating range
        rating_group = QGroupBox("Rating Range")
        rating_layout = QFormLayout(rating_group)
        
        self.rating_min_spin = QDoubleSpinBox()
        self.rating_min_spin.setRange(0.0, 10.0)
        self.rating_min_spin.setValue(0.0)
        self.rating_min_spin.setSingleStep(0.1)
        self.rating_min_spin.setSpecialValueText("Any")
        
        self.rating_max_spin = QDoubleSpinBox()
        self.rating_max_spin.setRange(0.0, 10.0)
        self.rating_max_spin.setValue(10.0)
        self.rating_max_spin.setSingleStep(0.1)
        self.rating_max_spin.setSpecialValueText("Any")
        
        rating_layout.addRow("Min:", self.rating_min_spin)
        rating_layout.addRow("Max:", self.rating_max_spin)
        scroll_layout.addWidget(rating_group)

        # Runtime range
        runtime_group = QGroupBox("Runtime (minutes)")
        runtime_layout = QFormLayout(runtime_group)
        
        self.runtime_min_spin = QSpinBox()
        self.runtime_min_spin.setRange(0, 500)
        self.runtime_min_spin.setValue(0)
        self.runtime_min_spin.setSpecialValueText("Any")
        
        self.runtime_max_spin = QSpinBox()
        self.runtime_max_spin.setRange(0, 500)
        self.runtime_max_spin.setValue(500)
        self.runtime_max_spin.setSpecialValueText("Any")
        
        runtime_layout.addRow("Min:", self.runtime_min_spin)
        runtime_layout.addRow("Max:", self.runtime_max_spin)
        scroll_layout.addWidget(runtime_group)

        # Tags
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(tags_group)
        self.tags_list = QListWidget()
        self.tags_list.setMaximumHeight(100)
        self.tags_list.setSelectionMode(QListWidget.MultiSelection)
        tags_layout.addWidget(self.tags_list)
        scroll_layout.addWidget(tags_group)

        # People (cast/crew)
        people_group = QGroupBox("People (Cast/Crew)")
        people_layout = QVBoxLayout(people_group)
        self.people_search = QLineEdit()
        self.people_search.setPlaceholderText("Search people...")
        people_layout.addWidget(self.people_search)
        self.people_list = QListWidget()
        self.people_list.setMaximumHeight(100)
        self.people_list.setSelectionMode(QListWidget.MultiSelection)
        people_layout.addWidget(self.people_list)
        scroll_layout.addWidget(people_group)

        # Collections
        collections_group = QGroupBox("Collections")
        collections_layout = QVBoxLayout(collections_group)
        self.collections_list = QListWidget()
        self.collections_list.setMaximumHeight(100)
        self.collections_list.setSelectionMode(QListWidget.MultiSelection)
        collections_layout.addWidget(self.collections_list)
        scroll_layout.addWidget(collections_group)

        # Sorting
        sort_group = QGroupBox("Sort By")
        sort_layout = QFormLayout(sort_group)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Title", "Year", "Rating", "Added", "Runtime"])
        
        self.sort_order_combo = QComboBox()
        self.sort_order_combo.addItems(["Ascending", "Descending"])
        
        sort_layout.addRow("Field:", self.sort_combo)
        sort_layout.addRow("Order:", self.sort_order_combo)
        scroll_layout.addWidget(sort_group)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Action buttons
        buttons_layout = QHBoxLayout()
        
        self.search_btn = QPushButton("Search")
        self.search_btn.setDefault(True)
        buttons_layout.addWidget(self.search_btn)
        
        self.clear_btn = QPushButton("Clear")
        buttons_layout.addWidget(self.clear_btn)
        
        self.save_btn = QPushButton("Save Search")
        buttons_layout.addWidget(self.save_btn)
        
        self.load_btn = QPushButton("Load Search")
        buttons_layout.addWidget(self.load_btn)
        
        layout.addLayout(buttons_layout)

    def _connect_signals(self) -> None:
        """Connect widget signals."""
        self.search_btn.clicked.connect(self._on_search_clicked)
        self.clear_btn.clicked.connect(self._on_clear_clicked)
        self.save_btn.clicked.connect(self._on_save_clicked)
        self.load_btn.clicked.connect(self._on_load_clicked)
        self.text_input.returnPressed.connect(self._on_search_clicked)
        self.people_search.textChanged.connect(self._filter_people_list)

    def _load_filter_options(self) -> None:
        """Load available filter options from database."""
        try:
            # Load tags
            tags = self._search_service.get_available_tags()
            for tag in tags:
                item = QListWidgetItem(tag.name)
                item.setData(Qt.UserRole, tag.id)
                self.tags_list.addItem(item)

            # Load people
            people = self._search_service.get_available_people()
            self._all_people = people
            self._update_people_list(people)

            # Load collections
            collections = self._search_service.get_available_collections()
            for collection in collections:
                item = QListWidgetItem(collection.name)
                item.setData(Qt.UserRole, collection.id)
                self.collections_list.addItem(item)

        except Exception as e:
            self._logger.error(f"Failed to load filter options: {e}")

    def _update_people_list(self, people: List[Person]) -> None:
        """Update people list widget."""
        self.people_list.clear()
        for person in people:
            item = QListWidgetItem(person.name)
            item.setData(Qt.UserRole, person.id)
            self.people_list.addItem(item)

    def _filter_people_list(self, text: str) -> None:
        """Filter people list based on search text."""
        if not text:
            self._update_people_list(self._all_people)
            return
        
        filtered = [p for p in self._all_people if text.lower() in p.name.lower()]
        self._update_people_list(filtered)

    def _on_quick_filter_clicked(self, filter_name: str, checked: bool) -> None:
        """Handle quick filter button click."""
        # Uncheck other quick filter buttons
        if checked:
            for name, btn in self.quick_filter_buttons.items():
                if name != filter_name:
                    btn.setChecked(False)

    def _on_search_clicked(self) -> None:
        """Handle search button click."""
        criteria = self.get_criteria()
        self.search_requested.emit(criteria)

    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        self.clear_filters()

    def _on_save_clicked(self) -> None:
        """Handle save search button click."""
        name, ok = QInputDialog.getText(
            self, "Save Search", "Enter search name:"
        )
        if ok and name:
            description, _ = QInputDialog.getText(
                self, "Save Search", "Enter description (optional):"
            )
            try:
                criteria = self.get_criteria()
                self._search_service.save_search(name, criteria, description or None)
                QMessageBox.information(
                    self, "Success", f"Search '{name}' saved successfully!"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error", f"Failed to save search: {str(e)}"
                )

    def _on_load_clicked(self) -> None:
        """Handle load search button click."""
        try:
            saved_searches = self._search_service.get_saved_searches()
            if not saved_searches:
                QMessageBox.information(
                    self, "No Saved Searches", "No saved searches found."
                )
                return

            items = [s.name for s in saved_searches]
            name, ok = QInputDialog.getItem(
                self, "Load Search", "Select search to load:", items, 0, False
            )
            if ok and name:
                # Find the saved search
                saved_search = next(s for s in saved_searches if s.name == name)
                result = self._search_service.load_search(saved_search.id)
                if result:
                    _, criteria = result
                    self.set_criteria(criteria)
                    self._on_search_clicked()

        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Failed to load search: {str(e)}"
            )

    def get_criteria(self) -> SearchCriteria:
        """Build search criteria from current UI state."""
        criteria = SearchCriteria()

        # Text search
        criteria.text_query = self.text_input.text().strip()

        # Media type
        type_text = self.type_combo.currentText()
        if type_text == "Movies":
            criteria.media_type = "movie"
        elif type_text == "TV Shows":
            criteria.media_type = "tv"

        # Year range
        year_min = self.year_min_spin.value()
        year_max = self.year_max_spin.value()
        if year_min > 1900:
            criteria.year_min = year_min
        if year_max < 2100:
            criteria.year_max = year_max

        # Rating range
        rating_min = self.rating_min_spin.value()
        rating_max = self.rating_max_spin.value()
        if rating_min > 0.0:
            criteria.rating_min = rating_min
        if rating_max < 10.0:
            criteria.rating_max = rating_max

        # Runtime range
        runtime_min = self.runtime_min_spin.value()
        runtime_max = self.runtime_max_spin.value()
        if runtime_min > 0:
            criteria.runtime_min = runtime_min
        if runtime_max < 500:
            criteria.runtime_max = runtime_max

        # Tags
        criteria.tags = [
            item.data(Qt.UserRole)
            for item in self.tags_list.selectedItems()
        ]

        # People
        criteria.people = [
            item.data(Qt.UserRole)
            for item in self.people_list.selectedItems()
        ]

        # Collections
        criteria.collections = [
            item.data(Qt.UserRole)
            for item in self.collections_list.selectedItems()
        ]

        # Quick filter
        for filter_name, btn in self.quick_filter_buttons.items():
            if btn.isChecked():
                criteria.quick_filter = filter_name
                break

        # Sorting
        sort_fields = {
            "Title": "title",
            "Year": "year",
            "Rating": "rating",
            "Added": "added",
            "Runtime": "runtime",
        }
        criteria.sort_by = sort_fields.get(
            self.sort_combo.currentText(), "title"
        )
        criteria.sort_order = (
            "desc" if self.sort_order_combo.currentText() == "Descending" else "asc"
        )

        return criteria

    def set_criteria(self, criteria: SearchCriteria) -> None:
        """Set UI state from criteria."""
        # Text search
        self.text_input.setText(criteria.text_query)

        # Media type
        if criteria.media_type == "movie":
            self.type_combo.setCurrentText("Movies")
        elif criteria.media_type == "tv":
            self.type_combo.setCurrentText("TV Shows")
        else:
            self.type_combo.setCurrentText("All")

        # Year range
        self.year_min_spin.setValue(criteria.year_min or 1900)
        self.year_max_spin.setValue(criteria.year_max or 2100)

        # Rating range
        self.rating_min_spin.setValue(criteria.rating_min or 0.0)
        self.rating_max_spin.setValue(criteria.rating_max or 10.0)

        # Runtime range
        self.runtime_min_spin.setValue(criteria.runtime_min or 0)
        self.runtime_max_spin.setValue(criteria.runtime_max or 500)

        # Quick filter
        for filter_name, btn in self.quick_filter_buttons.items():
            btn.setChecked(filter_name == criteria.quick_filter)

        # Sorting
        sort_display = {
            "title": "Title",
            "year": "Year",
            "rating": "Rating",
            "added": "Added",
            "runtime": "Runtime",
        }
        self.sort_combo.setCurrentText(
            sort_display.get(criteria.sort_by, "Title")
        )
        self.sort_order_combo.setCurrentText(
            "Descending" if criteria.sort_order == "desc" else "Ascending"
        )

    def clear_filters(self) -> None:
        """Clear all filter inputs."""
        self.text_input.clear()
        self.type_combo.setCurrentIndex(0)
        self.year_min_spin.setValue(1900)
        self.year_max_spin.setValue(2100)
        self.rating_min_spin.setValue(0.0)
        self.rating_max_spin.setValue(10.0)
        self.runtime_min_spin.setValue(0)
        self.runtime_max_spin.setValue(500)
        self.tags_list.clearSelection()
        self.people_list.clearSelection()
        self.collections_list.clearSelection()
        
        for btn in self.quick_filter_buttons.values():
            btn.setChecked(False)
        
        self.sort_combo.setCurrentIndex(0)
        self.sort_order_combo.setCurrentIndex(0)
