"""Match resolution widget for reviewing and editing media matches."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .logging import get_logger
from .models import MatchStatus, MediaMatch, SearchRequest, SearchResult
from .workers import SearchWorker


class MatchResolutionWidget(QWidget):
    """Widget for resolving and editing media matches."""

    # Signals
    match_updated = Signal(object)  # MediaMatch
    search_requested = Signal(object)  # SearchRequest

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._current_match: Optional[MediaMatch] = None
        self._search_worker: Optional[SearchWorker] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the match resolution UI."""
        layout = QHBoxLayout(self)

        # Left side - current match info
        left_widget = self._create_match_info_panel()
        layout.addWidget(left_widget, 1)

        # Right side - search results
        right_widget = self._create_search_panel()
        layout.addWidget(right_widget, 1)

    def _create_match_info_panel(self) -> QWidget:
        """Create the match information panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Current match info
        info_group = QGroupBox("Current Match")
        info_layout = QVBoxLayout(info_group)

        # File info
        self.file_label = QLabel("No file selected")
        self.file_label.setWordWrap(True)
        info_layout.addWidget(self.file_label)

        # Parsed info
        self.parsed_label = QLabel("")
        self.parsed_label.setWordWrap(True)
        info_layout.addWidget(self.parsed_label)

        # Current match info
        self.match_label = QLabel("")
        self.match_label.setWordWrap(True)
        info_layout.addWidget(self.match_label)

        # Confidence indicator
        self.confidence_label = QLabel("")
        info_layout.addWidget(self.confidence_label)

        # Overview
        self.overview_text = QTextEdit()
        self.overview_text.setMaximumHeight(100)
        self.overview_text.setReadOnly(True)
        info_layout.addWidget(QLabel("Overview:"))
        info_layout.addWidget(self.overview_text)

        layout.addWidget(info_group)

        # Action buttons
        action_group = QGroupBox("Actions")
        action_layout = QHBoxLayout(action_group)

        self.accept_button = QPushButton("Accept Match")
        self.accept_button.clicked.connect(self._on_accept_clicked)
        action_layout.addWidget(self.accept_button)

        self.manual_search_button = QPushButton("Manual Search")
        self.manual_search_button.clicked.connect(self._on_manual_search_clicked)
        action_layout.addWidget(self.manual_search_button)

        self.skip_button = QPushButton("Skip")
        self.skip_button.clicked.connect(self._on_skip_clicked)
        action_layout.addWidget(self.skip_button)

        layout.addWidget(action_group)

        return widget

    def _create_search_panel(self) -> QWidget:
        """Create the search results panel."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Search controls
        search_group = QGroupBox("Manual Search")
        search_layout = QHBoxLayout(search_group)

        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Enter search terms...")
        self.search_edit.returnPressed.connect(self._on_search_clicked)
        search_layout.addWidget(self.search_edit)

        self.search_button = QPushButton("Search")
        self.search_button.clicked.connect(self._on_search_clicked)
        search_layout.addWidget(self.search_button)

        layout.addWidget(search_group)

        # Search results
        results_group = QGroupBox("Search Results")
        results_layout = QVBoxLayout(results_group)

        self.results_list = QListWidget()
        self.results_list.itemSelectionChanged.connect(self._on_result_selected)
        results_layout.addWidget(self.results_list)

        # Apply selected result button
        self.apply_button = QPushButton("Apply Selected Result")
        self.apply_button.clicked.connect(self._on_apply_result_clicked)
        self.apply_button.setEnabled(False)
        results_layout.addWidget(self.apply_button)

        layout.addWidget(results_group)

        return widget

    def set_match(self, match: MediaMatch) -> None:
        """Set the current match to display."""
        self._current_match = match
        self._update_match_display()
        self._update_action_buttons()

    def _update_match_display(self) -> None:
        """Update the match information display."""
        if not self._current_match:
            self.file_label.setText("No file selected")
            self.parsed_label.setText("")
            self.match_label.setText("")
            self.confidence_label.setText("")
            self.overview_text.clear()
            return

        match = self._current_match
        metadata = match.metadata

        # File info
        self.file_label.setText(f"File: {metadata.path.name}")

        # Parsed info
        parsed_info = f"Type: {metadata.media_type.value.title()}"
        if metadata.year:
            parsed_info += f" | Year: {metadata.year}"
        if metadata.season and metadata.episode:
            parsed_info += f" | S{metadata.season:02d}E{metadata.episode:02d}"
        self.parsed_label.setText(parsed_info)

        # Match info
        if match.is_matched():
            match_info = f"Match: {match.matched_title or 'Unknown'}"
            if match.matched_year:
                match_info += f" ({match.matched_year})"
            if match.source:
                match_info += f" | Source: {match.source}"
            self.match_label.setText(match_info)
        else:
            self.match_label.setText("No match found")

        # Confidence
        if match.confidence is not None:
            confidence_pct = int(match.confidence * 100)
            color = "green" if match.confidence > 0.8 else "orange" if match.confidence > 0.6 else "red"
            self.confidence_label.setText(
                f'Confidence: <span style="color: {color};">{confidence_pct}%</span>'
            )
        else:
            self.confidence_label.setText("")

        # Overview
        self.overview_text.setText(match.overview or "")

        # Update search field with original title
        self.search_edit.setText(metadata.title)

    def _update_action_buttons(self) -> None:
        """Update the state of action buttons."""
        if not self._current_match:
            self.accept_button.setEnabled(False)
            self.manual_search_button.setEnabled(False)
            self.skip_button.setEnabled(False)
            return

        match = self._current_match
        self.accept_button.setEnabled(match.is_matched())
        self.manual_search_button.setEnabled(True)
        self.skip_button.setEnabled(True)

    @Slot()
    def _on_accept_clicked(self) -> None:
        """Handle accept match button click."""
        if not self._current_match:
            return

        # Mark as user selected and update status
        self._current_match.user_selected = True
        if self._current_match.status == MatchStatus.PENDING:
            self._current_match.status = MatchStatus.MATCHED

        self.match_updated.emit(self._current_match)
        self._logger.info(f"Accepted match for {self._current_match.metadata.title}")

    @Slot()
    def _on_manual_search_clicked(self) -> None:
        """Handle manual search button click."""
        if not self._current_match:
            return

        query = self.search_edit.text().strip()
        if not query:
            return

        self._perform_search(query)

    @Slot()
    def _on_search_clicked(self) -> None:
        """Handle search button click."""
        query = self.search_edit.text().strip()
        if not query:
            return

        self._perform_search(query)

    @Slot()
    def _on_skip_clicked(self) -> None:
        """Handle skip button click."""
        if not self._current_match:
            return

        self._current_match.status = MatchStatus.SKIPPED
        self.match_updated.emit(self._current_match)
        self._logger.info(f"Skipped match for {self._current_match.metadata.title}")

    @Slot()
    def _on_result_selected(self) -> None:
        """Handle search result selection."""
        has_selection = bool(self.results_list.currentItem())
        self.apply_button.setEnabled(has_selection)

    @Slot()
    def _on_apply_result_clicked(self) -> None:
        """Handle apply selected result button click."""
        if not self._current_match:
            return

        current_item = self.results_list.currentItem()
        if not current_item:
            return

        result = current_item.data(Qt.UserRole)
        if not result:
            return

        # Update match with search result
        self._current_match.status = MatchStatus.MANUAL
        self._current_match.matched_title = result.title
        self._current_match.matched_year = result.year
        self._current_match.external_id = result.external_id
        self._current_match.source = result.source
        self._current_match.poster_url = result.poster_url
        self._current_match.overview = result.overview
        self._current_match.confidence = result.confidence
        self._current_match.user_selected = True

        # Update display
        self._update_match_display()
        self._update_action_buttons()

        self.match_updated.emit(self._current_match)
        self._logger.info(f"Applied manual match for {self._current_match.metadata.title}")

    def _perform_search(self, query: str) -> None:
        """Perform a search with the given query."""
        if not self._current_match:
            return

        # Create search request
        request = SearchRequest(
            query=query,
            media_type=self._current_match.metadata.media_type,
            year=self._current_match.metadata.year,
            season=self._current_match.metadata.season,
            episode=self._current_match.metadata.episode
        )

        # Emit search request signal
        self.search_requested.emit(request)

        # Update UI state
        self.search_button.setEnabled(False)
        self.search_button.setText("Searching...")
        self.results_list.clear()
        self.apply_button.setEnabled(False)

        self._logger.info(f"Searching for '{query}'")

    def set_search_results(self, results: List[SearchResult]) -> None:
        """Set search results from a search operation."""
        self.results_list.clear()

        for result in results:
            item_text = self._format_result_text(result)
            item = QListWidgetItem(item_text)
            item.setData(Qt.UserRole, result)
            self.results_list.addItem(item)

        # Reset search button
        self.search_button.setEnabled(True)
        self.search_button.setText("Search")

        self._logger.info(f"Displaying {len(results)} search results")

    def _format_result_text(self, result: SearchResult) -> str:
        """Format search result text for display."""
        text = result.title
        if result.year:
            text += f" ({result.year})"
        if result.confidence > 0:
            confidence_pct = int(result.confidence * 100)
            text += f" [{confidence_pct}%]"
        if result.source:
            text += f" - {result.source}"
        return text

    def search_failed(self, error: str) -> None:
        """Handle search failure."""
        self.results_list.clear()
        self.results_list.addItem(f"Search failed: {error}")

        # Reset search button
        self.search_button.setEnabled(True)
        self.search_button.setText("Search")

        self._logger.error(f"Search failed: {error}")

    def clear_match(self) -> None:
        """Clear the current match display."""
        self._current_match = None
        self._update_match_display()
        self._update_action_buttons()
        self.results_list.clear()
        self.apply_button.setEnabled(False)

    def get_current_match(self) -> Optional[MediaMatch]:
        """Get the currently displayed match."""
        return self._current_match
