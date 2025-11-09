"""Preview panel for reviewing rename operations."""

from typing import List, Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .models import RenameOperation, VideoMetadata
from .renaming_engine import RenamingEngine


class PreviewPanel(QWidget):
    """Panel for previewing rename operations before execution."""

    # Signals
    operations_changed = Signal(list)
    execute_requested = Signal(list, bool)  # operations, dry_run

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._operations: List[RenameOperation] = []
        self._renaming_engine = RenamingEngine()
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the preview panel UI."""
        layout = QVBoxLayout(self)

        # Template configuration
        template_group = QGroupBox("Rename Templates")
        template_layout = QVBoxLayout(template_group)

        # Movie template
        movie_layout = QHBoxLayout()
        movie_layout.addWidget(QLabel("Movie Template:"))
        self.movie_template_edit = QLineEdit()
        self.movie_template_edit.setText(
            self._renaming_engine.get_default_templates()["movie"]
        )
        movie_layout.addWidget(self.movie_template_edit)
        template_layout.addLayout(movie_layout)

        # TV template
        tv_layout = QHBoxLayout()
        tv_layout.addWidget(QLabel("TV Template:"))
        self.tv_template_edit = QLineEdit()
        self.tv_template_edit.setText(
            self._renaming_engine.get_default_templates()["tv_episode"]
        )
        tv_layout.addWidget(self.tv_template_edit)
        template_layout.addLayout(tv_layout)

        layout.addWidget(template_group)

        # Preview table
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(5)
        self.preview_table.setHorizontalHeaderLabels(
            ["Selected", "Original", "Target", "Type", "Status"]
        )
        self.preview_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.preview_table)

        # Action buttons
        button_layout = QHBoxLayout()

        self.select_all_btn = QPushButton("Select All")
        self.select_all_btn.clicked.connect(self._select_all)
        button_layout.addWidget(self.select_all_btn)

        self.select_none_btn = QPushButton("Select None")
        self.select_none_btn.clicked.connect(self._select_none)
        button_layout.addWidget(self.select_none_btn)

        self.preview_btn = QPushButton("Preview")
        self.preview_btn.clicked.connect(self._update_preview)
        button_layout.addWidget(self.preview_btn)

        self.dry_run_btn = QPushButton("Dry Run")
        self.dry_run_btn.clicked.connect(lambda: self._execute_operations(True))
        button_layout.addWidget(self.dry_run_btn)

        self.execute_btn = QPushButton("Execute")
        self.execute_btn.clicked.connect(lambda: self._execute_operations(False))
        self.execute_btn.setStyleSheet(
            "QPushButton { background-color: #4CAF50; color: white; }"
        )
        button_layout.addWidget(self.execute_btn)

        layout.addLayout(button_layout)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("font-weight: bold;")
        layout.addWidget(self.status_label)

    def set_media_items(self, items: List[VideoMetadata]) -> None:
        """Set the media items to preview."""
        self._media_items = items
        self._update_preview()

    def _update_preview(self) -> None:
        """Update the preview with current templates."""
        if not hasattr(self, "_media_items") or not self._media_items:
            self.status_label.setText("No media items to preview")
            return

        movie_template = self.movie_template_edit.text()
        tv_template = self.tv_template_edit.text()

        try:
            self._operations = self._renaming_engine.preview_renames(
                self._media_items, movie_template, tv_template
            )
            self._populate_table()
            self.status_label.setText(f"Preview: {len(self._operations)} operations")
            self.operations_changed.emit(self._operations)
        except Exception as e:
            self.status_label.setText(f"Error generating preview: {e}")

    def _populate_table(self) -> None:
        """Populate the preview table with operations."""
        self.preview_table.setRowCount(len(self._operations))

        for row, operation in enumerate(self._operations):
            # Checkbox for selection
            checkbox = QCheckBox()
            checkbox.setChecked(True)
            checkbox.stateChanged.connect(self._on_selection_changed)
            self.preview_table.setCellWidget(row, 0, checkbox)

            # Original path
            original_item = QTableWidgetItem(str(operation.source_path))
            original_item.setFlags(original_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.preview_table.setItem(row, 1, original_item)

            # Target path
            target_item = QTableWidgetItem(str(operation.target_path))
            target_item.setFlags(target_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.preview_table.setItem(row, 2, target_item)

            # Media type
            type_item = QTableWidgetItem(operation.metadata.media_type.value)
            type_item.setFlags(type_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.preview_table.setItem(row, 3, type_item)

            # Status
            status_item = QTableWidgetItem("Ready")
            status_item.setFlags(status_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
            self.preview_table.setItem(row, 4, status_item)

        # Resize columns to content
        self.preview_table.resizeColumnsToContents()

    def _select_all(self) -> None:
        """Select all operations."""
        for row in range(self.preview_table.rowCount()):
            checkbox = self.preview_table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(True)

    def _select_none(self) -> None:
        """Deselect all operations."""
        for row in range(self.preview_table.rowCount()):
            checkbox = self.preview_table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox):
                checkbox.setChecked(False)

    def _get_selected_operations(self) -> List[RenameOperation]:
        """Get list of selected operations."""
        selected = []
        for row in range(self.preview_table.rowCount()):
            checkbox = self.preview_table.cellWidget(row, 0)
            if isinstance(checkbox, QCheckBox) and checkbox.isChecked():
                selected.append(self._operations[row])
        return selected

    def _execute_operations(self, dry_run: bool) -> None:
        """Execute the selected operations."""
        selected_operations = self._get_selected_operations()

        if not selected_operations:
            self.status_label.setText("No operations selected")
            return

        self.execute_requested.emit(selected_operations, dry_run)

    def _on_selection_changed(self) -> None:
        """Handle selection change."""
        selected_count = len(self._get_selected_operations())
        self.status_label.setText(
            f"Preview: {len(self._operations)} operations, {selected_count} selected"
        )

    def update_operation_status(
        self, operation: RenameOperation, status: str, success: bool = True
    ) -> None:
        """Update the status of an operation in the table."""
        for row, op in enumerate(self._operations):
            if op == operation:
                status_item = self.preview_table.item(row, 4)
                if status_item:
                    status_item.setText(status)
                    if success:
                        status_item.setBackground(Qt.GlobalColor.green)
                    else:
                        status_item.setBackground(Qt.GlobalColor.red)
                break

    def get_templates(self) -> dict[str, str]:
        """Get current template values."""
        return {
            "movie": self.movie_template_edit.text(),
            "tv_episode": self.tv_template_edit.text(),
        }

    def set_templates(self, templates: dict[str, str]) -> None:
        """Set template values."""
        if "movie" in templates:
            self.movie_template_edit.setText(templates["movie"])
        if "tv_episode" in templates:
            self.tv_template_edit.setText(templates["tv_episode"])
