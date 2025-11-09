"""Scan queue widget for displaying and managing pending media matches."""

from __future__ import annotations

from typing import List, Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .logging import get_logger
from .models import MatchStatus, MediaMatch, VideoMetadata
from .workers import MatchWorker


class ScanQueueWidget(QWidget):
    """Widget for displaying and managing the scan queue."""

    # Signals
    match_selected = Signal(object)  # MediaMatch
    start_matching = Signal()  # Request to start matching process
    clear_queue = Signal()  # Request to clear the queue

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._matches: List[MediaMatch] = []
        self._current_worker: Optional[MatchWorker] = None

        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the scan queue UI."""
        layout = QVBoxLayout(self)

        # Header with controls
        header_group = self._create_header_group()
        layout.addWidget(header_group)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Queue list
        self.queue_list = QListWidget()
        self.queue_list.setSelectionMode(QAbstractItemView.SingleSelection)
        self.queue_list.itemSelectionChanged.connect(self._on_selection_changed)
        layout.addWidget(self.queue_list)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.status_label)

    def _create_header_group(self) -> QGroupBox:
        """Create the header control group."""
        group = QGroupBox("Scan Queue")
        layout = QHBoxLayout(group)

        # Search/filter
        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter by title...")
        self.filter_edit.textChanged.connect(self._on_filter_changed)
        layout.addWidget(QLabel("Filter:"))
        layout.addWidget(self.filter_edit)

        # Control buttons
        self.start_button = QPushButton("Start Matching")
        self.start_button.clicked.connect(self._on_start_clicked)
        layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Stop")
        self.stop_button.clicked.connect(self._on_stop_clicked)
        self.stop_button.setEnabled(False)
        layout.addWidget(self.stop_button)

        self.clear_button = QPushButton("Clear")
        self.clear_button.clicked.connect(self._on_clear_clicked)
        layout.addWidget(self.clear_button)

        return group

    def add_metadata(self, metadata_list: List[VideoMetadata]) -> None:
        """Add metadata items to the queue."""
        for metadata in metadata_list:
            match = MediaMatch(metadata=metadata)
            self._matches.append(match)
            self._add_match_to_list(match)

        self._update_status()
        self._logger.info(f"Added {len(metadata_list)} items to scan queue")

    def _add_match_to_list(self, match: MediaMatch) -> None:
        """Add a match to the list widget."""
        item_text = self._format_match_text(match)
        item = QListWidgetItem(item_text)
        item.setData(Qt.UserRole, match)

        # Set color based on status
        if match.status == MatchStatus.MATCHED:
            item.setForeground(Qt.green)
        elif match.status == MatchStatus.MANUAL:
            item.setForeground(Qt.blue)
        elif match.status == MatchStatus.SKIPPED:
            item.setForeground(Qt.gray)
        else:  # PENDING
            item.setForeground(Qt.black)

        self.queue_list.addItem(item)

    def _format_match_text(self, match: MediaMatch) -> str:
        """Format match text for display."""
        metadata = match.metadata
        base_text = f"{metadata.title}"

        if metadata.year:
            base_text += f" ({metadata.year})"

        if metadata.media_type.value == "tv" and metadata.season and metadata.episode:
            base_text += f" S{metadata.season:02d}E{metadata.episode:02d}"

        # Add confidence if available
        if match.confidence is not None:
            confidence_pct = int(match.confidence * 100)
            base_text += f" [{confidence_pct}%]"

        # Add status indicator
        status_icons = {
            MatchStatus.PENDING: "⏳",
            MatchStatus.MATCHED: "✓",
            MatchStatus.MANUAL: "🔧",
            MatchStatus.SKIPPED: "⊘"
        }
        base_text = f"{status_icons.get(match.status, '?')} {base_text}"

        return base_text

    @Slot()
    def _on_selection_changed(self) -> None:
        """Handle selection change in the queue list."""
        current_item = self.queue_list.currentItem()
        if current_item:
            match = current_item.data(Qt.UserRole)
            if match:
                self.match_selected.emit(match)

    @Slot()
    def _on_start_clicked(self) -> None:
        """Handle start matching button click."""
        if not self._matches:
            return

        # Filter only pending matches
        pending_matches = [m for m in self._matches if m.status == MatchStatus.PENDING]
        if not pending_matches:
            self.status_label.setText("No pending items to match")
            return

        self.start_matching.emit()

    @Slot()
    def _on_stop_clicked(self) -> None:
        """Handle stop button click."""
        if self._current_worker:
            self._current_worker.stop()

    @Slot()
    def _on_clear_clicked(self) -> None:
        """Handle clear button click."""
        self.clear_queue.emit()

    @Slot(str)
    def _on_filter_changed(self, text: str) -> None:
        """Handle filter text change."""
        filter_text = text.lower().strip()

        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            match = item.data(Qt.UserRole)

            if match:
                title = match.metadata.title.lower()
                should_show = not filter_text or filter_text in title
                item.setHidden(not should_show)

    def set_worker(self, worker: MatchWorker) -> None:
        """Set the active match worker."""
        self._current_worker = worker

        # Connect worker signals
        worker.signals.match_found.connect(self._on_match_found)
        worker.signals.match_failed.connect(self._on_match_failed)
        worker.signals.progress.connect(self._on_progress)
        worker.signals.finished.connect(self._on_worker_finished)

        # Update UI state
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, len(self._matches))
        self.progress_bar.setValue(0)
        self.status_label.setText("Matching...")

    @Slot(object)
    def _on_match_found(self, match: MediaMatch) -> None:
        """Handle match found from worker."""
        # Update existing match in our list
        for i, existing_match in enumerate(self._matches):
            if existing_match.metadata.path == match.metadata.path:
                self._matches[i] = match
                break

        # Update list item
        self._update_list_item(match)

    @Slot(str, str)
    def _on_match_failed(self, path: str, error: str) -> None:
        """Handle match failure from worker."""
        self._logger.error(f"Match failed for {path}: {error}")
        self.status_label.setText(f"Error matching {path}")

    @Slot(int, int)
    def _on_progress(self, current: int, total: int) -> None:
        """Handle progress update from worker."""
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Matched {current}/{total} items")

    @Slot()
    def _on_worker_finished(self) -> None:
        """Handle worker completion."""
        self._current_worker = None
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.progress_bar.setVisible(False)
        self._update_status()

    def _update_list_item(self, match: MediaMatch) -> None:
        """Update the list item for a match."""
        for i in range(self.queue_list.count()):
            item = self.queue_list.item(i)
            existing_match = item.data(Qt.UserRole)

            if existing_match and existing_match.metadata.path == match.metadata.path:
                item.setText(self._format_match_text(match))
                item.setData(Qt.UserRole, match)

                # Update color
                if match.status == MatchStatus.MATCHED:
                    item.setForeground(Qt.green)
                elif match.status == MatchStatus.MANUAL:
                    item.setForeground(Qt.blue)
                elif match.status == MatchStatus.SKIPPED:
                    item.setForeground(Qt.gray)
                else:  # PENDING
                    item.setForeground(Qt.black)
                break

    def _update_status(self) -> None:
        """Update the status label."""
        total = len(self._matches)
        matched = len([m for m in self._matches if m.is_matched()])
        pending = len([m for m in self._matches if m.needs_review()])

        if total == 0:
            self.status_label.setText("Queue empty")
        elif pending == 0:
            self.status_label.setText(f"All {total} items processed ({matched} matched)")
        else:
            self.status_label.setText(f"{total} items ({matched} matched, {pending} pending)")

    def clear_queue(self) -> None:
        """Clear all items from the queue."""
        self._matches.clear()
        self.queue_list.clear()
        self._update_status()
        self._logger.info("Scan queue cleared")

    def get_matches(self) -> List[MediaMatch]:
        """Get all matches in the queue."""
        return list(self._matches)

    def get_selected_match(self) -> Optional[MediaMatch]:
        """Get the currently selected match."""
        current_item = self.queue_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None
