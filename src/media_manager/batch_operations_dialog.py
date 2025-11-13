from __future__ import annotations

from typing import Iterable

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .batch_operations_service import (
    BatchOperationConfig,
    BatchOperationSummary,
    BatchOperationsService,
)
from .persistence.models import MediaItem
from .persistence.repositories import LibraryRepository
from .settings import SettingsManager, get_settings


class BatchOperationsDialog(QDialog):
    """Dialog for configuring and executing batch media operations."""

    operations_completed = Signal(object)  # BatchOperationSummary

    def __init__(
        self,
        items: Iterable[MediaItem],
        settings: SettingsManager | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)

        self._items = list(items)
        if not self._items:
            raise ValueError("BatchOperationsDialog requires at least one media item")

        self._settings = settings or get_settings()
        self._service = BatchOperationsService(self._settings)
        self._library_repository = LibraryRepository()

        self._setup_ui()
        self._load_libraries()
        self._apply_defaults()

    def _setup_ui(self) -> None:
        self.setWindowTitle("Batch Operations")
        self.resize(520, 420)

        layout = QVBoxLayout(self)

        self.selection_label = QLabel(f"{len(self._items)} items selected")
        self.selection_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
        layout.addWidget(self.selection_label)

        # Rename option
        self.rename_checkbox = QCheckBox("Rename using templates")
        layout.addWidget(self.rename_checkbox)

        # Move option
        move_container = QWidget()
        move_layout = QHBoxLayout(move_container)
        move_layout.setContentsMargins(0, 0, 0, 0)
        move_layout.setSpacing(8)

        self.move_checkbox = QCheckBox("Move to library")
        self.library_combo = QComboBox()
        self.library_combo.setEnabled(False)
        self.move_checkbox.toggled.connect(self.library_combo.setEnabled)

        move_layout.addWidget(self.move_checkbox)
        move_layout.addWidget(self.library_combo, stretch=1)
        layout.addWidget(move_container)

        # Delete option
        self.delete_checkbox = QCheckBox("Delete files (permanent)")
        layout.addWidget(self.delete_checkbox)

        # Tags assignment
        tags_container = QWidget()
        tags_layout = QHBoxLayout(tags_container)
        tags_layout.setContentsMargins(0, 0, 0, 0)
        tags_layout.setSpacing(8)

        self.tags_checkbox = QCheckBox("Assign tags")
        self.tags_edit = QLineEdit()
        self.tags_edit.setPlaceholderText("Comma-separated tags")
        self.tags_edit.setEnabled(False)
        self.tags_checkbox.toggled.connect(self.tags_edit.setEnabled)

        tags_layout.addWidget(self.tags_checkbox)
        tags_layout.addWidget(self.tags_edit, stretch=1)
        layout.addWidget(tags_container)

        # Metadata overrides
        self.metadata_checkbox = QCheckBox("Override metadata (genres, rating)")
        layout.addWidget(self.metadata_checkbox)

        self.metadata_fields_widget = QWidget()
        metadata_layout = QFormLayout(self.metadata_fields_widget)
        metadata_layout.setContentsMargins(26, 0, 0, 0)

        self.genres_edit = QLineEdit()
        self.genres_edit.setPlaceholderText("Comma-separated genres")

        self.rating_spin = QSpinBox()
        self.rating_spin.setRange(0, 100)
        self.rating_spin.setSuffix(" / 100")
        self.rating_spin.setValue(0)

        metadata_layout.addRow("Genres", self.genres_edit)
        metadata_layout.addRow("Rating", self.rating_spin)

        self.metadata_fields_widget.setEnabled(False)
        self.metadata_checkbox.toggled.connect(self.metadata_fields_widget.setEnabled)

        layout.addWidget(self.metadata_fields_widget)

        # Provider re-sync
        self.resync_checkbox = QCheckBox("Re-sync metadata from providers")
        layout.addWidget(self.resync_checkbox)

        # Progress section
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(len(self._items))
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel()
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        # Dialog buttons
        self.button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        self.button_box.accepted.connect(self._on_apply_clicked)
        self.button_box.rejected.connect(self.reject)
        layout.addWidget(self.button_box)

    def _load_libraries(self) -> None:
        libraries = self._library_repository.get_active()
        self.library_combo.clear()

        for library in libraries:
            self.library_combo.addItem(library.name, library.id)

        if not libraries:
            self.move_checkbox.setEnabled(False)
            self.library_combo.setEnabled(False)
            self.move_checkbox.setToolTip("No active libraries available")

    def _apply_defaults(self) -> None:
        defaults = self._settings.get_batch_defaults()
        if not defaults:
            return

        self.rename_checkbox.setChecked(bool(defaults.get("rename", self.rename_checkbox.isChecked())))
        move_default = bool(defaults.get("move", self.move_checkbox.isChecked()))
        self.move_checkbox.setChecked(move_default)
        delete_default = bool(defaults.get("delete", self.delete_checkbox.isChecked()))
        self.delete_checkbox.setChecked(delete_default)
        tags_default = bool(defaults.get("tags", self.tags_checkbox.isChecked()))
        self.tags_checkbox.setChecked(tags_default)
        metadata_default = bool(defaults.get("metadata", self.metadata_checkbox.isChecked()))
        self.metadata_checkbox.setChecked(metadata_default)
        resync_default = bool(defaults.get("resync", self.resync_checkbox.isChecked()))
        self.resync_checkbox.setChecked(resync_default)

        move_library_id = defaults.get("move_library_id")
        if move_library_id is not None:
            index = self.library_combo.findData(move_library_id)
            if index >= 0:
                self.library_combo.setCurrentIndex(index)

        default_tags = defaults.get("default_tags")
        if isinstance(default_tags, str):
            self.tags_edit.setText(default_tags)
        elif isinstance(default_tags, list):
            self.tags_edit.setText(", ".join(str(tag) for tag in default_tags))

        default_genres = defaults.get("default_genres")
        if isinstance(default_genres, list):
            self.genres_edit.setText(", ".join(str(genre) for genre in default_genres))
        elif isinstance(default_genres, str):
            self.genres_edit.setText(default_genres)

        default_rating = defaults.get("default_rating")
        if default_rating is not None:
            try:
                self.rating_spin.setValue(int(default_rating))
            except (TypeError, ValueError):
                pass

    def _on_apply_clicked(self) -> None:
        config = self._build_config()

        if not self._has_selected_operations(config):
            QMessageBox.information(self, "No Operations", "Select at least one batch operation to apply.")
            return

        if config.move_library_id is not None and self.library_combo.currentData() is None:
            QMessageBox.warning(self, "Select Library", "Choose a target library for the move operation.")
            return

        if config.delete_files:
            confirm = QMessageBox.question(
                self,
                "Confirm Deletion",
                "This will permanently delete the selected files. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if confirm != QMessageBox.Yes:
                return

        self._execute_operations(config)

    def _build_config(self) -> BatchOperationConfig:
        target_library_id = self.library_combo.currentData() if self.move_checkbox.isChecked() else None
        genres_value = self.genres_edit.text() if self.metadata_checkbox.isChecked() else None
        rating_value = (
            float(self.rating_spin.value()) if self.metadata_checkbox.isChecked() else None
        )

        tags = []
        if self.tags_checkbox.isChecked():
            tags = [tag.strip() for tag in self.tags_edit.text().split(",") if tag.strip()]

        config = BatchOperationConfig(
            rename=self.rename_checkbox.isChecked(),
            move_library_id=target_library_id,
            delete_files=self.delete_checkbox.isChecked(),
            tags_to_add=tags,
            override_genres=genres_value,
            override_rating=rating_value,
            resync_providers=self.resync_checkbox.isChecked(),
        )
        return config

    def _has_selected_operations(self, config: BatchOperationConfig) -> bool:
        return any(
            [
                config.rename,
                config.move_library_id is not None,
                config.delete_files,
                bool(config.tags_to_add),
                config.override_genres is not None,
                config.override_rating is not None,
                config.resync_providers,
            ]
        )

    def _execute_operations(self, config: BatchOperationConfig) -> None:
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Starting batch operations...")

        def progress_callback(current: int, total: int, message: str) -> None:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            self.status_label.setText(message)
            QApplication.processEvents()

        try:
            summary = self._service.perform(self._items, config, progress_callback)
        except Exception as exc:  # pragma: no cover - UI feedback path
            QMessageBox.critical(self, "Batch Operation Failed", str(exc))
            self.status_label.setText("Batch operation failed")
            return

        self.status_label.setText("Batch operations completed")
        QMessageBox.information(self, "Batch Operations", summary.to_message() or "Completed")
        self.operations_completed.emit(summary)
        self.accept()
