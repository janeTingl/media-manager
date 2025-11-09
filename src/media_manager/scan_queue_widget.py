"""Scan queue widget for displaying and managing pending media matches."""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QCheckBox,
    QComboBox,
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

from .library_postprocessor import ConflictResolution, PostProcessingOptions
from .logging import get_logger
from .models import MatchStatus, MediaMatch, VideoMetadata
from .workers import MatchWorker


class ScanQueueWidget(QWidget):
    """Widget for displaying and managing the scan queue."""

    # Signals
    match_selected = Signal(object)  # MediaMatch
    start_matching = Signal()  # Request to start matching process
    clear_queue = Signal()  # Request to clear the queue
    finalize_requested = Signal(object)  # PostProcessingOptions

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._matches: List[MediaMatch] = []
        self._current_worker: Optional[MatchWorker] = None
        self._finalize_worker = None

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

        # Finalization controls
        self.finalize_group = self._create_finalize_group()
        layout.addWidget(self.finalize_group)

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

    def _create_finalize_group(self) -> QGroupBox:
        """Create the library finalization controls."""
        group = QGroupBox("Library Finalization")
        layout = QVBoxLayout(group)

        options_layout = QHBoxLayout()
        self.dry_run_checkbox = QCheckBox("Dry run")
        self.dry_run_checkbox.setToolTip("Simulate the operation without moving files")
        options_layout.addWidget(self.dry_run_checkbox)

        self.copy_checkbox = QCheckBox("Copy instead of move")
        self.copy_checkbox.setToolTip("Copy files and keep originals in place")
        options_layout.addWidget(self.copy_checkbox)

        self.cleanup_checkbox = QCheckBox("Cleanup empty folders")
        self.cleanup_checkbox.setChecked(True)
        self.cleanup_checkbox.setToolTip("Remove empty directories after moving files")
        options_layout.addWidget(self.cleanup_checkbox)

        layout.addLayout(options_layout)

        conflict_layout = QHBoxLayout()
        conflict_layout.addWidget(QLabel("On conflict:"))
        self.conflict_combo = QComboBox()
        self.conflict_combo.addItem("Skip", ConflictResolution.SKIP)
        self.conflict_combo.addItem("Overwrite", ConflictResolution.OVERWRITE)
        self.conflict_combo.addItem("Rename", ConflictResolution.RENAME)
        self.conflict_combo.setCurrentIndex(2)
        conflict_layout.addWidget(self.conflict_combo)
        layout.addLayout(conflict_layout)

        self.finalize_button = QPushButton("Finalize Library")
        self.finalize_button.clicked.connect(self._on_finalize_clicked)
        layout.addWidget(self.finalize_button)

        self.finalize_progress_bar = QProgressBar()
        self.finalize_progress_bar.setVisible(False)
        layout.addWidget(self.finalize_progress_bar)

        self.finalize_status_label = QLabel("Ready to finalize")
        self.finalize_status_label.setStyleSheet("color: gray; font-style: italic;")
        layout.addWidget(self.finalize_status_label)

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
            MatchStatus.SKIPPED: "⊘",
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
    def _on_finalize_clicked(self) -> None:
        """Handle finalize library button click."""
        matched = [m for m in self._matches if m.is_matched()]
        if not matched:
            self.finalize_status_label.setText("No matched items to finalize")
            return

        options = PostProcessingOptions(
            dry_run=self.dry_run_checkbox.isChecked(),
            copy_mode=self.copy_checkbox.isChecked(),
            conflict_resolution=self._get_selected_conflict_resolution(),
            cleanup_empty_dirs=self.cleanup_checkbox.isChecked(),
        )

        self.finalize_button.setEnabled(False)
        self.finalize_progress_bar.setRange(0, len(matched))
        self.finalize_progress_bar.setValue(0)
        self.finalize_progress_bar.setVisible(True)
        self.finalize_status_label.setText("Preparing library finalization...")
        self.finalize_requested.emit(options)

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

    def _get_selected_conflict_resolution(self) -> ConflictResolution:
        data = self.conflict_combo.currentData()
        if isinstance(data, ConflictResolution):
            return data
        return ConflictResolution.RENAME

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

    def set_post_processing_worker(self, worker) -> None:
        """Set the active library post-processing worker."""
        self._finalize_worker = worker

        worker.signals.progress.connect(self._on_finalize_progress)
        worker.signals.item_processed.connect(self._on_finalize_item_processed)
        worker.signals.item_skipped.connect(self._on_finalize_item_skipped)
        worker.signals.item_failed.connect(self._on_finalize_item_failed)
        worker.signals.finished.connect(self._on_finalize_finished)
        worker.signals.error.connect(self._on_finalize_error)

        matched_total = len([m for m in self._matches if m.is_matched()])
        self.finalize_progress_bar.setRange(0, max(1, matched_total))
        self.finalize_progress_bar.setValue(0)
        self.finalize_progress_bar.setVisible(True)
        self.finalize_status_label.setText("Finalizing library...")

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

    @Slot(int, int)
    def _on_finalize_progress(self, current: int, total: int) -> None:
        """Handle progress updates from the finalization worker."""
        total = max(1, total)
        self.finalize_progress_bar.setRange(0, total)
        self.finalize_progress_bar.setValue(min(current, total))
        self.finalize_status_label.setText(f"Finalizing {current}/{total} items")

    @Slot(object, object, object)
    def _on_finalize_item_processed(self, match: MediaMatch, source, target) -> None:
        """Update UI when an item has been processed."""
        target_name = ""
        if target:
            try:
                target_name = Path(target).name
            except TypeError:
                target_name = str(target)
        message = f"Finalized {match.metadata.title}"
        if target_name:
            message += f" → {target_name}"
        self.finalize_status_label.setText(message)

    @Slot(object, object, str)
    def _on_finalize_item_skipped(self, match: MediaMatch, target, reason: str) -> None:
        """Update UI when an item is skipped."""
        self.finalize_status_label.setText(f"Skipped {match.metadata.title}: {reason}")

    @Slot(object, str)
    def _on_finalize_item_failed(self, match: MediaMatch, message: str) -> None:
        """Update UI when an item fails to finalize."""
        self.finalize_status_label.setText(
            f"Failed to finalize {match.metadata.title}: {message}"
        )

    @Slot(object)
    def _on_finalize_finished(self, summary) -> None:
        """Handle completion of the finalization worker."""
        self._reset_finalize_ui()
        processed = len(getattr(summary, "processed", []))
        skipped = len(getattr(summary, "skipped", []))
        failed = len(getattr(summary, "failed", []))
        message = f"Finalization complete: {processed} processed"
        if skipped:
            message += f", {skipped} skipped"
        if failed:
            message += f", {failed} failed"
        self.finalize_status_label.setText(message)

    @Slot(str)
    def _on_finalize_error(self, message: str) -> None:
        """Handle finalization errors."""
        self._reset_finalize_ui()
        self.finalize_status_label.setText(f"Finalization error: {message}")

    def _reset_finalize_ui(self) -> None:
        """Reset finalization widgets to idle state."""
        self._finalize_worker = None
        self.finalize_button.setEnabled(True)
        self.finalize_progress_bar.setVisible(False)
        self.finalize_progress_bar.setValue(0)

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
            self.status_label.setText(
                f"All {total} items processed ({matched} matched)"
            )
        else:
            self.status_label.setText(
                f"{total} items ({matched} matched, {pending} pending)"
            )

    def do_clear_queue(self) -> None:
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
