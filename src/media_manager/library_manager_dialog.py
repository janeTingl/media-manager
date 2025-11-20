"""Library manager dialog for creating, editing, and removing libraries."""

import json
from pathlib import Path
from typing import Optional

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .logging import get_logger
from .persistence.models import Library
from .persistence.repositories import LibraryRepository


class LibraryFormWidget(QWidget):
    """Form widget for creating/editing a library."""

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._current_library: Optional[Library] = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the form UI."""
        layout = QFormLayout(self)

        # Name field
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText(self.tr("e.g., My Movie Collection"))
        layout.addRow(self.tr("Name:"), self.name_edit)

        # Path field
        path_layout = QHBoxLayout()
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText(self.tr("/path/to/media/folder"))
        path_layout.addWidget(self.path_edit)
        self.browse_button = QPushButton(self.tr("Browse..."))
        self.browse_button.clicked.connect(self._on_browse_path)
        path_layout.addWidget(self.browse_button)
        layout.addRow(self.tr("Library Path:"), path_layout)

        # Media type combo
        self.media_type_combo = QComboBox()
        self.media_type_combo.addItems(
            [self.tr("movie"), self.tr("tv"), self.tr("mixed")]
        )
        layout.addRow(self.tr("Media Type:"), self.media_type_combo)

        # Default destination field
        dest_layout = QHBoxLayout()
        self.default_dest_edit = QLineEdit()
        self.default_dest_edit.setPlaceholderText(
            self.tr("/path/to/destination (optional)")
        )
        dest_layout.addWidget(self.default_dest_edit)
        self.browse_dest_button = QPushButton(self.tr("Browse..."))
        self.browse_dest_button.clicked.connect(self._on_browse_destination)
        dest_layout.addWidget(self.browse_dest_button)
        layout.addRow(self.tr("Default Destination:"), dest_layout)

        # Scan roots group
        scan_group = QGroupBox(self.tr("Scan Roots"))
        scan_layout = QVBoxLayout(scan_group)

        self.scan_roots_list = QListWidget()
        scan_layout.addWidget(self.scan_roots_list)

        scan_buttons_layout = QHBoxLayout()
        self.add_scan_root_button = QPushButton(self.tr("Add Root..."))
        self.add_scan_root_button.clicked.connect(self._on_add_scan_root)
        scan_buttons_layout.addWidget(self.add_scan_root_button)

        self.remove_scan_root_button = QPushButton(self.tr("Remove"))
        self.remove_scan_root_button.clicked.connect(self._on_remove_scan_root)
        scan_buttons_layout.addWidget(self.remove_scan_root_button)
        scan_layout.addLayout(scan_buttons_layout)

        layout.addRow(scan_group)

        # Color picker
        color_layout = QHBoxLayout()
        self.color_label = QLabel(self.tr("No color selected"))
        self.color_label.setStyleSheet("padding: 5px; border: 1px solid gray;")
        color_layout.addWidget(self.color_label)
        self.pick_color_button = QPushButton(self.tr("Pick Color..."))
        self.pick_color_button.clicked.connect(self._on_pick_color)
        color_layout.addWidget(self.pick_color_button)
        layout.addRow(self.tr("Color:"), color_layout)

        # Active checkbox
        self.active_checkbox = QCheckBox(self.tr("Active"))
        self.active_checkbox.setChecked(True)
        layout.addRow(self.tr("Status:"), self.active_checkbox)

        # Description field
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText(self.tr("Optional description..."))
        self.description_edit.setMaximumHeight(80)
        layout.addRow(self.tr("Description:"), self.description_edit)

    def _on_browse_path(self) -> None:
        """Handle browse path button click."""
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Select Library Path"), self.path_edit.text()
        )
        if folder:
            self.path_edit.setText(folder)

    def _on_browse_destination(self) -> None:
        """Handle browse destination button click."""
        folder = QFileDialog.getExistingDirectory(
            self, self.tr("Select Default Destination"), self.default_dest_edit.text()
        )
        if folder:
            self.default_dest_edit.setText(folder)

    def _on_add_scan_root(self) -> None:
        """Handle add scan root button click."""
        folder = QFileDialog.getExistingDirectory(self, self.tr("Select Scan Root"))
        if folder:
            self.scan_roots_list.addItem(folder)

    def _on_remove_scan_root(self) -> None:
        """Handle remove scan root button click."""
        current_item = self.scan_roots_list.currentItem()
        if current_item:
            self.scan_roots_list.takeItem(self.scan_roots_list.row(current_item))

    def _on_pick_color(self) -> None:
        """Handle pick color button click."""
        color = QColorDialog.getColor(parent=self)
        if color.isValid():
            self.color_label.setText(color.name())
            self.color_label.setStyleSheet(
                f"padding: 5px; border: 1px solid gray; background-color: {color.name()};"
            )

    def load_library(self, library: Library) -> None:
        """Load library data into the form."""
        self._current_library = library
        self.name_edit.setText(library.name)
        self.path_edit.setText(library.path)
        self.media_type_combo.setCurrentText(library.media_type)
        self.default_dest_edit.setText(library.default_destination or "")
        self.active_checkbox.setChecked(library.is_active)
        self.description_edit.setPlainText(library.description or "")

        # Load scan roots
        self.scan_roots_list.clear()
        if library.scan_roots:
            try:
                scan_roots = json.loads(library.scan_roots)
                for root in scan_roots:
                    self.scan_roots_list.addItem(root)
            except json.JSONDecodeError:
                self._logger.warning(
                    f"Failed to parse scan roots: {library.scan_roots}"
                )

        # Load color
        if library.color:
            self.color_label.setText(library.color)
            self.color_label.setStyleSheet(
                f"padding: 5px; border: 1px solid gray; background-color: {library.color};"
            )

    def clear_form(self) -> None:
        """Clear the form."""
        self._current_library = None
        self.name_edit.clear()
        self.path_edit.clear()
        self.media_type_combo.setCurrentIndex(0)
        self.default_dest_edit.clear()
        self.scan_roots_list.clear()
        self.active_checkbox.setChecked(True)
        self.description_edit.clear()
        self.color_label.setText("No color selected")
        self.color_label.setStyleSheet("padding: 5px; border: 1px solid gray;")

    def get_library_data(self) -> dict:
        """Get library data from the form."""
        # Collect scan roots
        scan_roots = []
        for i in range(self.scan_roots_list.count()):
            scan_roots.append(self.scan_roots_list.item(i).text())

        color_text = self.color_label.text()
        color = color_text if color_text != "No color selected" else None

        return {
            "name": self.name_edit.text().strip(),
            "path": self.path_edit.text().strip(),
            "media_type": self.media_type_combo.currentText(),
            "default_destination": self.default_dest_edit.text().strip() or None,
            "scan_roots": json.dumps(scan_roots) if scan_roots else None,
            "is_active": self.active_checkbox.isChecked(),
            "description": self.description_edit.toPlainText().strip() or None,
            "color": color,
        }

    def validate(self) -> tuple[bool, str]:
        """Validate form data."""
        if not self.name_edit.text().strip():
            return False, "Library name is required"

        if not self.path_edit.text().strip():
            return False, "Library path is required"

        path = Path(self.path_edit.text().strip())
        if not path.exists():
            return False, f"Library path does not exist: {path}"

        if not path.is_dir():
            return False, f"Library path is not a directory: {path}"

        return True, ""


class LibraryManagerDialog(QDialog):
    """Dialog for managing libraries."""

    # Signals
    library_created = Signal(object)
    library_updated = Signal(object)
    library_deleted = Signal(int)

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._repository = LibraryRepository()
        self._setup_ui()
        self._load_libraries()

    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        self.setWindowTitle("Library Manager")
        self.setMinimumSize(900, 600)

        layout = QVBoxLayout(self)

        # Splitter for list and form
        splitter = QSplitter(Qt.Orientation.Horizontal)
        layout.addWidget(splitter)

        # Left side - library list
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)

        left_layout.addWidget(QLabel("Libraries:"))
        self.library_list = QListWidget()
        self.library_list.itemSelectionChanged.connect(self._on_library_selected)
        left_layout.addWidget(self.library_list)

        # List buttons
        list_buttons_layout = QHBoxLayout()
        self.new_button = QPushButton("New")
        self.new_button.clicked.connect(self._on_new_library)
        list_buttons_layout.addWidget(self.new_button)

        self.delete_button = QPushButton("Delete")
        self.delete_button.clicked.connect(self._on_delete_library)
        self.delete_button.setEnabled(False)
        list_buttons_layout.addWidget(self.delete_button)

        left_layout.addLayout(list_buttons_layout)

        splitter.addWidget(left_widget)

        # Right side - library form
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        right_layout.addWidget(QLabel("Library Details:"))
        self.library_form = LibraryFormWidget()
        right_layout.addWidget(self.library_form)

        # Form buttons
        form_buttons_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._on_save_library)
        self.save_button.setEnabled(False)
        form_buttons_layout.addWidget(self.save_button)

        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel_edit)
        self.cancel_button.setEnabled(False)
        form_buttons_layout.addWidget(self.cancel_button)

        right_layout.addLayout(form_buttons_layout)

        splitter.addWidget(right_widget)

        # Set splitter sizes (30% left, 70% right)
        splitter.setSizes([270, 630])

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Close)
        button_box.rejected.connect(self.accept)
        layout.addWidget(button_box)

    def _load_libraries(self) -> None:
        """Load libraries from the database."""
        self.library_list.clear()
        libraries = self._repository.get_all()
        for library in libraries:
            item = QListWidgetItem(f"{library.name} ({library.media_type})")
            item.setData(Qt.ItemDataRole.UserRole, library)
            if not library.is_active:
                item.setText(f"{item.text()} [Inactive]")
            self.library_list.addItem(item)

    def _on_library_selected(self) -> None:
        """Handle library selection."""
        selected_items = self.library_list.selectedItems()
        if selected_items:
            library = selected_items[0].data(Qt.ItemDataRole.UserRole)
            self.library_form.load_library(library)
            self.delete_button.setEnabled(True)
            self.save_button.setEnabled(True)
            self.cancel_button.setEnabled(True)
        else:
            self.delete_button.setEnabled(False)
            self.save_button.setEnabled(False)
            self.cancel_button.setEnabled(False)

    def _on_new_library(self) -> None:
        """Handle new library button click."""
        self.library_list.clearSelection()
        self.library_form.clear_form()
        self.save_button.setEnabled(True)
        self.cancel_button.setEnabled(True)

    def _on_save_library(self) -> None:
        """Handle save library button click."""
        # Validate form
        is_valid, error_msg = self.library_form.validate()
        if not is_valid:
            QMessageBox.warning(self, "Validation Error", error_msg)
            return

        # Get form data
        data = self.library_form.get_library_data()

        try:
            # Check if editing existing or creating new
            current_library = self.library_form._current_library
            if current_library:
                # Update existing library
                for key, value in data.items():
                    setattr(current_library, key, value)
                self._repository.update(current_library)
                self.library_updated.emit(current_library)
                QMessageBox.information(self, "Success", "Library updated successfully")
            else:
                # Create new library
                library = Library(**data)
                library = self._repository.create(library)
                self.library_created.emit(library)
                QMessageBox.information(self, "Success", "Library created successfully")

            # Reload library list
            self._load_libraries()
            self.library_form.clear_form()
            self.save_button.setEnabled(False)
            self.cancel_button.setEnabled(False)

        except Exception as e:
            self._logger.error(f"Failed to save library: {e}")
            QMessageBox.critical(self, "Error", f"Failed to save library: {e}")

    def _on_delete_library(self) -> None:
        """Handle delete library button click."""
        selected_items = self.library_list.selectedItems()
        if not selected_items:
            return

        library = selected_items[0].data(Qt.ItemDataRole.UserRole)

        # Confirm deletion
        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete library '{library.name}'?\n\n"
            f"This will not delete the actual media files, only the library reference.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                # Check if library has media items
                item_count = self._repository.count_items(library.id)
                if item_count > 0:
                    reply = QMessageBox.question(
                        self,
                        "Library Has Items",
                        f"This library contains {item_count} media items. "
                        f"Delete anyway?\n\nItems will be removed from the database.",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No,
                    )
                    if reply == QMessageBox.No:
                        return

                self._repository.delete(library.id)
                self.library_deleted.emit(library.id)
                QMessageBox.information(self, "Success", "Library deleted successfully")

                # Reload library list
                self._load_libraries()
                self.library_form.clear_form()

            except Exception as e:
                self._logger.error(f"Failed to delete library: {e}")
                QMessageBox.critical(self, "Error", f"Failed to delete library: {e}")

    def _on_cancel_edit(self) -> None:
        """Handle cancel edit button click."""
        self.library_list.clearSelection()
        self.library_form.clear_form()
        self.save_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
