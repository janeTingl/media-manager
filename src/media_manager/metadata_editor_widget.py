"""Metadata editor widget for editing media item information."""

from __future__ import annotations

import json
from typing import Any, Optional

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QAbstractItemView,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHeaderView,
    QLabel,
    QLineEdit,
    QSpinBox,
    QTabWidget,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QWidget,
    QMessageBox,
    QComboBox,
)

from .logging import get_logger
from .persistence.models import MediaItem, Credit, Person, Tag, Collection
from .persistence.repositories import UnitOfWork, transactional_context


class MetadataEditorWidget(QWidget):
    """Widget for editing media item metadata."""

    # Signals
    match_updated = Signal(object)  # MediaItem
    save_requested = Signal(object)  # MediaItem
    validation_error = Signal(str)  # Error message

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._current_media_item: MediaItem | None = None
        self._original_data: dict[str, Any] = {}
        self._is_dirty = False

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        """Setup the metadata editor UI."""
        layout = QVBoxLayout(self)

        # Title bar with media info
        self.title_label = QLabel("No media selected")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)

        # Tab widget for different sections
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.tab_widget.addTab(self._create_general_info_tab(), "General")
        self.tab_widget.addTab(self._create_episodic_tab(), "Episodic")
        self.tab_widget.addTab(self._create_ratings_tab(), "Ratings")
        self.tab_widget.addTab(self._create_genres_keywords_tab(), "Genres & Keywords")
        self.tab_widget.addTab(self._create_collections_tab(), "Collections & Tags")
        self.tab_widget.addTab(self._create_cast_crew_tab(), "Cast & Crew")

        # Action buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self._on_save_clicked)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)

        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.reset_button.setEnabled(False)
        button_layout.addWidget(self.reset_button)

        button_layout.addStretch()

        self.open_tmdb_button = QPushButton("Open in TMDB")
        self.open_tmdb_button.clicked.connect(self._on_open_tmdb_clicked)
        self.open_tmdb_button.setEnabled(False)
        button_layout.addWidget(self.open_tmdb_button)

        self.refresh_button = QPushButton("Refresh")
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        self.refresh_button.setEnabled(False)
        button_layout.addWidget(self.refresh_button)

    def _create_general_info_tab(self) -> QWidget:
        """Create the general info tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Title
        title_group = QGroupBox("Title")
        title_layout = QVBoxLayout(title_group)
        self.title_input = QLineEdit()
        self.title_input.textChanged.connect(self._on_field_changed)
        title_layout.addWidget(QLabel("Title:"))
        title_layout.addWidget(self.title_input)
        layout.addWidget(title_group)

        # Original Title
        orig_title_group = QGroupBox("Original Title")
        orig_title_layout = QVBoxLayout(orig_title_group)
        self.original_title_input = QLineEdit()
        self.original_title_input.textChanged.connect(self._on_field_changed)
        orig_title_layout.addWidget(QLabel("Original Title:"))
        orig_title_layout.addWidget(self.original_title_input)
        layout.addWidget(orig_title_group)

        # Year
        year_group = QGroupBox("Year")
        year_layout = QVBoxLayout(year_group)
        self.year_input = QSpinBox()
        self.year_input.setMinimum(1800)
        self.year_input.setMaximum(2100)
        self.year_input.setValue(2024)
        self.year_input.valueChanged.connect(self._on_field_changed)
        year_layout.addWidget(QLabel("Year:"))
        year_layout.addWidget(self.year_input)
        layout.addWidget(year_group)

        # Runtime
        runtime_group = QGroupBox("Runtime")
        runtime_layout = QVBoxLayout(runtime_group)
        self.runtime_input = QSpinBox()
        self.runtime_input.setMinimum(0)
        self.runtime_input.setMaximum(1000)
        self.runtime_input.setSuffix(" minutes")
        self.runtime_input.valueChanged.connect(self._on_field_changed)
        runtime_layout.addWidget(QLabel("Runtime:"))
        runtime_layout.addWidget(self.runtime_input)
        layout.addWidget(runtime_group)

        # Plot/Description
        plot_group = QGroupBox("Plot / Description")
        plot_layout = QVBoxLayout(plot_group)
        self.plot_input = QTextEdit()
        self.plot_input.textChanged.connect(self._on_field_changed)
        plot_layout.addWidget(QLabel("Plot:"))
        plot_layout.addWidget(self.plot_input)
        layout.addWidget(plot_group)

        layout.addStretch()
        return widget

    def _create_episodic_tab(self) -> QWidget:
        """Create the episodic data tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Season
        season_group = QGroupBox("Season")
        season_layout = QVBoxLayout(season_group)
        self.season_input = QSpinBox()
        self.season_input.setMinimum(0)
        self.season_input.setMaximum(100)
        self.season_input.setValue(1)
        self.season_input.valueChanged.connect(self._on_field_changed)
        season_layout.addWidget(QLabel("Season:"))
        season_layout.addWidget(self.season_input)
        layout.addWidget(season_group)

        # Episode
        episode_group = QGroupBox("Episode")
        episode_layout = QVBoxLayout(episode_group)
        self.episode_input = QSpinBox()
        self.episode_input.setMinimum(0)
        self.episode_input.setMaximum(1000)
        self.episode_input.setValue(1)
        self.episode_input.valueChanged.connect(self._on_field_changed)
        episode_layout.addWidget(QLabel("Episode:"))
        episode_layout.addWidget(self.episode_input)
        layout.addWidget(episode_group)

        # Aired Date
        aired_group = QGroupBox("Aired Date")
        aired_layout = QVBoxLayout(aired_group)
        self.aired_input = QLineEdit()
        self.aired_input.setPlaceholderText("YYYY-MM-DD")
        self.aired_input.textChanged.connect(self._on_field_changed)
        aired_layout.addWidget(QLabel("Aired:"))
        aired_layout.addWidget(self.aired_input)
        layout.addWidget(aired_group)

        layout.addStretch()
        return widget

    def _create_ratings_tab(self) -> QWidget:
        """Create the ratings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Rating
        rating_group = QGroupBox("Rating")
        rating_layout = QVBoxLayout(rating_group)
        self.rating_input = QSpinBox()
        self.rating_input.setMinimum(0)
        self.rating_input.setMaximum(100)
        self.rating_input.setSuffix(" / 100")
        self.rating_input.valueChanged.connect(self._on_field_changed)
        rating_layout.addWidget(QLabel("Rating:"))
        rating_layout.addWidget(self.rating_input)
        layout.addWidget(rating_group)

        layout.addStretch()
        return widget

    def _create_genres_keywords_tab(self) -> QWidget:
        """Create the genres and keywords tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Genres (stored as JSON in description for now)
        genres_group = QGroupBox("Genres")
        genres_layout = QVBoxLayout(genres_group)
        self.genres_input = QLineEdit()
        self.genres_input.setPlaceholderText("Comma-separated genres")
        self.genres_input.textChanged.connect(self._on_field_changed)
        genres_layout.addWidget(QLabel("Genres (comma-separated):"))
        genres_layout.addWidget(self.genres_input)
        layout.addWidget(genres_group)

        # Keywords
        keywords_group = QGroupBox("Keywords")
        keywords_layout = QVBoxLayout(keywords_group)
        self.keywords_input = QTextEdit()
        self.keywords_input.setMaximumHeight(100)
        self.keywords_input.setPlaceholderText("One per line")
        self.keywords_input.textChanged.connect(self._on_field_changed)
        keywords_layout.addWidget(QLabel("Keywords (one per line):"))
        keywords_layout.addWidget(self.keywords_input)
        layout.addWidget(keywords_group)

        layout.addStretch()
        return widget

    def _create_collections_tab(self) -> QWidget:
        """Create the collections and tags tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Collections
        collections_group = QGroupBox("Collections")
        collections_layout = QVBoxLayout(collections_group)
        self.collections_table = QTableWidget()
        self.collections_table.setColumnCount(2)
        self.collections_table.setHorizontalHeaderLabels(["Name", ""])
        self.collections_table.horizontalHeader().setStretchLastSection(False)
        self.collections_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.collections_table.setMaximumHeight(150)
        collections_layout.addWidget(self.collections_table)

        collections_btn_layout = QHBoxLayout()
        add_collection_btn = QPushButton("Add Collection")
        add_collection_btn.clicked.connect(self._on_add_collection)
        collections_btn_layout.addWidget(add_collection_btn)
        collections_btn_layout.addStretch()
        collections_layout.addLayout(collections_btn_layout)
        layout.addWidget(collections_group)

        # Tags
        tags_group = QGroupBox("Tags")
        tags_layout = QVBoxLayout(tags_group)
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Comma-separated tags")
        self.tags_input.textChanged.connect(self._on_field_changed)
        tags_layout.addWidget(QLabel("Tags (comma-separated):"))
        tags_layout.addWidget(self.tags_input)
        layout.addWidget(tags_group)

        layout.addStretch()
        return widget

    def _create_cast_crew_tab(self) -> QWidget:
        """Create the cast and crew tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Cast table
        cast_group = QGroupBox("Cast")
        cast_layout = QVBoxLayout(cast_group)
        self.cast_table = QTableWidget()
        self.cast_table.setColumnCount(4)
        self.cast_table.setHorizontalHeaderLabels(["Name", "Character", "", ""])
        self.cast_table.horizontalHeader().setStretchLastSection(False)
        self.cast_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cast_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.cast_table.itemChanged.connect(self._on_field_changed)
        cast_layout.addWidget(self.cast_table)

        cast_btn_layout = QHBoxLayout()
        add_cast_btn = QPushButton("Add Cast Member")
        add_cast_btn.clicked.connect(self._on_add_cast_member)
        cast_btn_layout.addWidget(add_cast_btn)
        cast_btn_layout.addStretch()
        cast_layout.addLayout(cast_btn_layout)
        layout.addWidget(cast_group)

        # Crew table
        crew_group = QGroupBox("Crew")
        crew_layout = QVBoxLayout(crew_group)
        self.crew_table = QTableWidget()
        self.crew_table.setColumnCount(4)
        self.crew_table.setHorizontalHeaderLabels(["Name", "Role", "", ""])
        self.crew_table.horizontalHeader().setStretchLastSection(False)
        self.crew_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.crew_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.crew_table.itemChanged.connect(self._on_field_changed)
        crew_layout.addWidget(self.crew_table)

        crew_btn_layout = QHBoxLayout()
        add_crew_btn = QPushButton("Add Crew Member")
        add_crew_btn.clicked.connect(self._on_add_crew_member)
        crew_btn_layout.addWidget(add_crew_btn)
        crew_btn_layout.addStretch()
        crew_layout.addLayout(crew_btn_layout)
        layout.addWidget(crew_group)

        return widget

    def _connect_signals(self) -> None:
        """Connect internal signals."""
        pass

    def set_media_item(self, media_item: MediaItem | None) -> None:
        """Set the media item to edit.

        Args:
            media_item: The MediaItem to edit, or None to clear
        """
        self._current_media_item = media_item

        if media_item is None:
            self._clear_form()
            self.title_label.setText("No media selected")
            self._disable_controls()
        else:
            self._load_media_item(media_item)
            self.title_label.setText(f"Editing: {media_item.title}")
            self._enable_controls()

        self._is_dirty = False
        self._update_button_states()

    def _load_media_item(self, media_item: MediaItem) -> None:
        """Load media item data into the form."""
        # Store original data for undo
        self._original_data = {
            "title": media_item.title,
            "media_type": media_item.media_type,
            "year": media_item.year,
            "runtime": media_item.runtime,
            "description": media_item.description,
            "season": media_item.season,
            "episode": media_item.episode,
            "aired_date": media_item.aired_date,
            "rating": media_item.rating,
        }

        # General info
        self.title_input.setText(media_item.title or "")
        self.original_title_input.setText("")  # Could be added to MediaItem model
        self.year_input.setValue(media_item.year or 2024)
        self.runtime_input.setValue(media_item.runtime or 0)
        self.plot_input.setPlainText(media_item.description or "")

        # Episodic info
        self.season_input.setValue(media_item.season or 1)
        self.episode_input.setValue(media_item.episode or 1)
        self.aired_input.setText(media_item.aired_date or "")

        # Ratings
        self.rating_input.setValue(int(media_item.rating or 0))

        # Genres and keywords
        self.genres_input.setText(media_item.genres or "")
        self.keywords_input.clear()

        # Load collections
        self._load_collections(media_item)

        # Load tags
        self._load_tags(media_item)

        # Load cast and crew
        self._load_cast_crew(media_item)

    def _load_collections(self, media_item: MediaItem) -> None:
        """Load collections for the media item."""
        self.collections_table.setRowCount(0)
        for collection in media_item.collections:
            self._add_collection_row(collection.name, collection.id)

    def _load_tags(self, media_item: MediaItem) -> None:
        """Load tags for the media item."""
        tag_names = [tag.name for tag in media_item.tags]
        self.tags_input.setText(", ".join(tag_names))

    def _load_cast_crew(self, media_item: MediaItem) -> None:
        """Load cast and crew for the media item."""
        self.cast_table.setRowCount(0)
        self.crew_table.setRowCount(0)

        for credit in media_item.credits:
            if credit.role == "actor":
                self._add_cast_row(credit.person.name, credit.character_name or "", credit.id, credit.person.id)
            else:
                self._add_crew_row(credit.person.name, credit.role, credit.id, credit.person.id)

    def _clear_form(self) -> None:
        """Clear all form fields."""
        self.title_input.clear()
        self.original_title_input.clear()
        self.year_input.setValue(2024)
        self.runtime_input.setValue(0)
        self.plot_input.clear()
        self.season_input.setValue(1)
        self.episode_input.setValue(1)
        self.aired_input.clear()
        self.rating_input.setValue(0)
        self.genres_input.clear()
        self.keywords_input.clear()
        self.tags_input.clear()
        self.collections_table.setRowCount(0)
        self.cast_table.setRowCount(0)
        self.crew_table.setRowCount(0)

    def _enable_controls(self) -> None:
        """Enable all form controls."""
        for tab_index in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(tab_index)
            self._set_widget_enabled(tab_widget, True)
        self.open_tmdb_button.setEnabled(True)
        self.refresh_button.setEnabled(True)

    def _disable_controls(self) -> None:
        """Disable all form controls."""
        for tab_index in range(self.tab_widget.count()):
            tab_widget = self.tab_widget.widget(tab_index)
            self._set_widget_enabled(tab_widget, False)
        self.save_button.setEnabled(False)
        self.reset_button.setEnabled(False)
        self.open_tmdb_button.setEnabled(False)
        self.refresh_button.setEnabled(False)

    def _set_widget_enabled(self, widget: QWidget, enabled: bool) -> None:
        """Recursively set widget and children enabled state."""
        widget.setEnabled(enabled)
        for child in widget.findChildren(QWidget):
            child.setEnabled(enabled)

    def _update_button_states(self) -> None:
        """Update button enabled states based on dirty flag."""
        self.save_button.setEnabled(self._is_dirty and self._current_media_item is not None)
        self.reset_button.setEnabled(self._is_dirty and self._current_media_item is not None)

    @Slot()
    def _on_field_changed(self) -> None:
        """Handle field value changes."""
        if not self._is_dirty:
            self._is_dirty = True
            self._update_button_states()

    @Slot()
    def _on_save_clicked(self) -> None:
        """Handle save button click."""
        if self._current_media_item is None:
            return

        try:
            # Validate input
            if not self._validate_form():
                return

            # Update media item from form
            self._update_media_item_from_form()

            # Save to database
            self._save_to_database()

            # Reset dirty flag
            self._is_dirty = False
            self._update_button_states()

            # Emit signal
            self.match_updated.emit(self._current_media_item)
            self.save_requested.emit(self._current_media_item)

            self._logger.info(f"Saved metadata for {self._current_media_item.title}")

        except Exception as e:
            self._logger.error(f"Error saving metadata: {e}")
            self.validation_error.emit(f"Error saving metadata: {str(e)}")
            QMessageBox.critical(self, "Save Error", f"Error saving metadata: {str(e)}")

    @Slot()
    def _on_reset_clicked(self) -> None:
        """Handle reset button click."""
        if self._current_media_item is None:
            return

        reply = QMessageBox.question(
            self,
            "Reset Changes",
            "Are you sure you want to discard all changes?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            self._load_media_item(self._current_media_item)
            self._is_dirty = False
            self._update_button_states()

    @Slot()
    def _on_open_tmdb_clicked(self) -> None:
        """Handle open in TMDB button click."""
        if self._current_media_item is None:
            return

        # Try to find TMDB ID
        tmdb_id = None
        for ext_id in self._current_media_item.external_ids:
            if ext_id.source == "tmdb":
                tmdb_id = ext_id.external_id
                break

        if tmdb_id:
            import webbrowser

            media_type = "movie" if self._current_media_item.media_type == "movie" else "tv"
            url = f"https://www.themoviedb.org/{media_type}/{tmdb_id}"
            webbrowser.open(url)
            self._logger.info(f"Opened TMDB URL: {url}")
        else:
            QMessageBox.information(
                self,
                "No TMDB ID",
                "This item does not have a TMDB ID.",
            )

    @Slot()
    def _on_refresh_clicked(self) -> None:
        """Handle refresh button click."""
        if self._current_media_item is None:
            return

        # This would trigger a background refresh from the provider
        # For now, just show a message
        QMessageBox.information(
            self,
            "Refresh",
            "Refresh functionality would fetch fresh data from TMDB/TVDB.",
        )

    @Slot()
    def _on_add_collection(self) -> None:
        """Handle add collection button click."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Collection")
        layout = QVBoxLayout(dialog)

        combo = QComboBox()
        # TODO: Load collections from database
        combo.addItem("Sample Collection")
        layout.addWidget(QLabel("Select Collection:"))
        layout.addWidget(combo)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            self._add_collection_row(combo.currentText(), None)
            self._is_dirty = True
            self._update_button_states()

    @Slot()
    def _on_add_cast_member(self) -> None:
        """Handle add cast member button click."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Cast Member")
        layout = QVBoxLayout(dialog)

        name_input = QLineEdit()
        character_input = QLineEdit()
        layout.addWidget(QLabel("Actor Name:"))
        layout.addWidget(name_input)
        layout.addWidget(QLabel("Character Name:"))
        layout.addWidget(character_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            if name_input.text().strip():
                self._add_cast_row(name_input.text(), character_input.text(), None)
                self._is_dirty = True
                self._update_button_states()

    @Slot()
    def _on_add_crew_member(self) -> None:
        """Handle add crew member button click."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Crew Member")
        layout = QVBoxLayout(dialog)

        name_input = QLineEdit()
        role_input = QLineEdit()
        layout.addWidget(QLabel("Name:"))
        layout.addWidget(name_input)
        layout.addWidget(QLabel("Role (director, writer, producer, etc.):"))
        layout.addWidget(role_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            if name_input.text().strip():
                self._add_crew_row(name_input.text(), role_input.text() or "crew", None)
                self._is_dirty = True
                self._update_button_states()

    def _add_collection_row(self, name: str, collection_id: int | None) -> None:
        """Add a row to the collections table."""
        row = self.collections_table.rowCount()
        self.collections_table.insertRow(row)

        # Name
        item = QTableWidgetItem(name)
        item.setData(Qt.UserRole, collection_id)
        self.collections_table.setItem(row, 0, item)

        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.collections_table.removeRow(row))
        self.collections_table.setCellWidget(row, 1, remove_btn)

    def _add_cast_row(self, name: str, character: str, credit_id: int | None, person_id: int | None = None) -> None:
        """Add a row to the cast table."""
        row = self.cast_table.rowCount()
        self.cast_table.insertRow(row)

        # Name
        name_item = QTableWidgetItem(name)
        name_item.setData(Qt.UserRole, credit_id)
        name_item.setData(Qt.UserRole + 1, person_id)
        self.cast_table.setItem(row, 0, name_item)

        # Character
        char_item = QTableWidgetItem(character)
        self.cast_table.setItem(row, 1, char_item)

        # View details button
        if person_id:
            view_btn = QPushButton("View")
            view_btn.clicked.connect(lambda: self._on_view_person_clicked(person_id))
            self.cast_table.setCellWidget(row, 2, view_btn)

        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.cast_table.removeRow(row))
        self.cast_table.setCellWidget(row, 3, remove_btn)

    def _add_crew_row(self, name: str, role: str, credit_id: int | None, person_id: int | None = None) -> None:
        """Add a row to the crew table."""
        row = self.crew_table.rowCount()
        self.crew_table.insertRow(row)

        # Name
        name_item = QTableWidgetItem(name)
        name_item.setData(Qt.UserRole, credit_id)
        name_item.setData(Qt.UserRole + 1, person_id)
        self.crew_table.setItem(row, 0, name_item)

        # Role
        role_item = QTableWidgetItem(role)
        self.crew_table.setItem(row, 1, role_item)

        # View details button
        if person_id:
            view_btn = QPushButton("View")
            view_btn.clicked.connect(lambda: self._on_view_person_clicked(person_id))
            self.crew_table.setCellWidget(row, 2, view_btn)

        # Remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.crew_table.removeRow(row))
        self.crew_table.setCellWidget(row, 3, remove_btn)

    def _validate_form(self) -> bool:
        """Validate form inputs.

        Returns:
            True if valid, False otherwise
        """
        if not self.title_input.text().strip():
            self.validation_error.emit("Title is required")
            QMessageBox.warning(self, "Validation Error", "Title is required")
            return False

        # Validate year
        year = self.year_input.value()
        if year < 1800 or year > 2100:
            self.validation_error.emit("Year must be between 1800 and 2100")
            QMessageBox.warning(self, "Validation Error", "Year must be between 1800 and 2100")
            return False

        # Validate aired date format if provided
        aired = self.aired_input.text().strip()
        if aired and not self._is_valid_date(aired):
            self.validation_error.emit("Aired date must be in YYYY-MM-DD format")
            QMessageBox.warning(
                self,
                "Validation Error",
                "Aired date must be in YYYY-MM-DD format",
            )
            return False

        return True

    def _is_valid_date(self, date_str: str) -> bool:
        """Check if date string is in valid format."""
        try:
            from datetime import datetime

            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False

    def _update_media_item_from_form(self) -> None:
        """Update the current media item with form values."""
        if self._current_media_item is None:
            return

        self._current_media_item.title = self.title_input.text()
        self._current_media_item.year = self.year_input.value()
        self._current_media_item.runtime = self.runtime_input.value() or None
        self._current_media_item.description = self.plot_input.toPlainText() or None
        genres_text = self.genres_input.text().strip()
        self._current_media_item.genres = genres_text or None
        self._current_media_item.season = self.season_input.value() if self.season_input.value() > 0 else None
        self._current_media_item.episode = self.episode_input.value() if self.episode_input.value() > 0 else None
        self._current_media_item.aired_date = self.aired_input.text() or None
        rating = self.rating_input.value()
        self._current_media_item.rating = float(rating) if rating > 0 else None

    def _save_to_database(self) -> None:
        """Save the media item and related data to database."""
        if self._current_media_item is None:
            return

        try:
            with transactional_context() as uow:
                # Save media item
                media_repo = uow.get_repository(MediaItem)
                media_repo.update(self._current_media_item)

                # Save cast and crew
                self._save_cast_crew(uow)

                # Save collections and tags
                self._save_collections_and_tags(uow)

                uow.commit()

        except Exception as e:
            self._logger.error(f"Error saving to database: {e}")
            raise

    def _save_cast_crew(self, uow) -> None:
        """Save cast and crew changes."""
        # This would involve:
        # 1. Reading the tables
        # 2. Creating/updating Person records
        # 3. Creating/updating Credit records
        # For now, this is a placeholder
        pass
    
    def _on_view_person_clicked(self, person_id: int) -> None:
        """Handle view person details button click.
        
        Args:
            person_id: Database person ID
        """
        from .entity_detail_dialog import EntityDetailDialog
        
        dialog = EntityDetailDialog(self)
        dialog.show_person(person_id)
        dialog.exec()

    def _save_collections_and_tags(self, uow) -> None:
        """Save collections and tags changes."""
        # This would involve:
        # 1. Reading the tags input and collections table
        # 2. Creating/updating Tag and Collection records
        # 3. Updating the many-to-many relationships
        # For now, this is a placeholder
        pass
