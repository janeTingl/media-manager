"""Metadata editor widget for editing media item information."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from .logging import get_logger
from .persistence.models import Collection, Favorite, MediaItem, Tag
from .persistence.repositories import transactional_context


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
        self.title_label = QLabel("未选择媒体")
        self.title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        layout.addWidget(self.title_label)

        # Tab widget for different sections
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # Create tabs
        self.tab_widget.addTab(self._create_general_info_tab(), "常规")
        self.tab_widget.addTab(self._create_episodic_tab(), "剧集")
        self.tab_widget.addTab(self._create_ratings_tab(), "评分")
        self.tab_widget.addTab(self._create_genres_keywords_tab(), "类型和关键词")
        self.tab_widget.addTab(self._create_collections_tab(), "收藏和标签")
        self.tab_widget.addTab(self._create_cast_crew_tab(), "演员和工作人员")

        # Action buttons
        button_layout = QHBoxLayout()
        layout.addLayout(button_layout)

        self.save_button = QPushButton("保存")
        self.save_button.clicked.connect(self._on_save_clicked)
        self.save_button.setEnabled(False)
        button_layout.addWidget(self.save_button)

        self.reset_button = QPushButton("重置")
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.reset_button.setEnabled(False)
        button_layout.addWidget(self.reset_button)

        button_layout.addStretch()

        self.open_tmdb_button = QPushButton("在 TMDB 中打开")
        self.open_tmdb_button.clicked.connect(self._on_open_tmdb_clicked)
        self.open_tmdb_button.setEnabled(False)
        button_layout.addWidget(self.open_tmdb_button)

        self.refresh_button = QPushButton("刷新")
        self.refresh_button.clicked.connect(self._on_refresh_clicked)
        self.refresh_button.setEnabled(False)
        button_layout.addWidget(self.refresh_button)

    def _create_general_info_tab(self) -> QWidget:
        """Create the general info tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Title
        title_group = QGroupBox("标题")
        title_layout = QVBoxLayout(title_group)
        self.title_input = QLineEdit()
        self.title_input.textChanged.connect(self._on_field_changed)
        title_layout.addWidget(QLabel("标题："))
        title_layout.addWidget(self.title_input)
        layout.addWidget(title_group)

        # Original Title
        orig_title_group = QGroupBox("原始标题")
        orig_title_layout = QVBoxLayout(orig_title_group)
        self.original_title_input = QLineEdit()
        self.original_title_input.textChanged.connect(self._on_field_changed)
        orig_title_layout.addWidget(QLabel("原始标题："))
        orig_title_layout.addWidget(self.original_title_input)
        layout.addWidget(orig_title_group)

        # Year
        year_group = QGroupBox("年份")
        year_layout = QVBoxLayout(year_group)
        self.year_input = QSpinBox()
        self.year_input.setMinimum(1800)
        self.year_input.setMaximum(2100)
        self.year_input.setValue(2024)
        self.year_input.valueChanged.connect(self._on_field_changed)
        year_layout.addWidget(QLabel("年份："))
        year_layout.addWidget(self.year_input)
        layout.addWidget(year_group)

        # Runtime
        runtime_group = QGroupBox("时长")
        runtime_layout = QVBoxLayout(runtime_group)
        self.runtime_input = QSpinBox()
        self.runtime_input.setMinimum(0)
        self.runtime_input.setMaximum(1000)
        self.runtime_input.setSuffix(" minutes")
        self.runtime_input.valueChanged.connect(self._on_field_changed)
        runtime_layout.addWidget(QLabel("时长："))
        runtime_layout.addWidget(self.runtime_input)
        layout.addWidget(runtime_group)

        # Plot/Description
        plot_group = QGroupBox("剧情 / 描述")
        plot_layout = QVBoxLayout(plot_group)
        self.plot_input = QTextEdit()
        self.plot_input.textChanged.connect(self._on_field_changed)
        plot_layout.addWidget(QLabel("剧情："))
        plot_layout.addWidget(self.plot_input)
        layout.addWidget(plot_group)

        layout.addStretch()
        return widget

    def _create_episodic_tab(self) -> QWidget:
        """Create the episodic data tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Season
        season_group = QGroupBox("季")
        season_layout = QVBoxLayout(season_group)
        self.season_input = QSpinBox()
        self.season_input.setMinimum(0)
        self.season_input.setMaximum(100)
        self.season_input.setValue(1)
        self.season_input.valueChanged.connect(self._on_field_changed)
        season_layout.addWidget(QLabel("季："))
        season_layout.addWidget(self.season_input)
        layout.addWidget(season_group)

        # Episode
        episode_group = QGroupBox("集")
        episode_layout = QVBoxLayout(episode_group)
        self.episode_input = QSpinBox()
        self.episode_input.setMinimum(0)
        self.episode_input.setMaximum(1000)
        self.episode_input.setValue(1)
        self.episode_input.valueChanged.connect(self._on_field_changed)
        episode_layout.addWidget(QLabel("集："))
        episode_layout.addWidget(self.episode_input)
        layout.addWidget(episode_group)

        # Aired Date
        aired_group = QGroupBox("播出日期")
        aired_layout = QVBoxLayout(aired_group)
        self.aired_input = QLineEdit()
        self.aired_input.setPlaceholderText("年-月-日")
        self.aired_input.textChanged.connect(self._on_field_changed)
        aired_layout.addWidget(QLabel("播出："))
        aired_layout.addWidget(self.aired_input)
        layout.addWidget(aired_group)

        layout.addStretch()
        return widget

    def _create_ratings_tab(self) -> QWidget:
        """Create the ratings tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Rating
        rating_group = QGroupBox("评分")
        rating_layout = QVBoxLayout(rating_group)
        self.rating_input = QSpinBox()
        self.rating_input.setMinimum(0)
        self.rating_input.setMaximum(100)
        self.rating_input.setSuffix(" / 100")
        self.rating_input.valueChanged.connect(self._on_field_changed)
        rating_layout.addWidget(QLabel("评分："))
        rating_layout.addWidget(self.rating_input)
        layout.addWidget(rating_group)

        layout.addStretch()
        return widget

    def _create_genres_keywords_tab(self) -> QWidget:
        """Create the genres and keywords tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Genres (stored as JSON in description for now)
        genres_group = QGroupBox("类型")
        genres_layout = QVBoxLayout(genres_group)
        self.genres_input = QLineEdit()
        self.genres_input.setPlaceholderText("逗号分隔的类型")
        self.genres_input.textChanged.connect(self._on_field_changed)
        genres_layout.addWidget(QLabel("类型（逗号分隔）："))
        genres_layout.addWidget(self.genres_input)
        layout.addWidget(genres_group)

        # Keywords
        keywords_group = QGroupBox("关键词")
        keywords_layout = QVBoxLayout(keywords_group)
        self.keywords_input = QTextEdit()
        self.keywords_input.setMaximumHeight(100)
        self.keywords_input.setPlaceholderText("每行一个")
        self.keywords_input.textChanged.connect(self._on_field_changed)
        keywords_layout.addWidget(QLabel("关键词（每行一个）："))
        keywords_layout.addWidget(self.keywords_input)
        layout.addWidget(keywords_group)

        layout.addStretch()
        return widget

    def _create_collections_tab(self) -> QWidget:
        """Create the collections and tags tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Favorite checkbox
        favorite_layout = QHBoxLayout()
        self.favorite_checkbox = QCheckBox("标记为收藏")
        self.favorite_checkbox.toggled.connect(self._on_field_changed)
        favorite_layout.addWidget(self.favorite_checkbox)
        favorite_layout.addStretch()
        layout.addLayout(favorite_layout)

        # Collections
        collections_group = QGroupBox("收藏")
        collections_layout = QVBoxLayout(collections_group)

        self.collections_list = QListWidget()
        self.collections_list.setMaximumHeight(120)
        self.collections_list.setSelectionMode(QListWidget.MultiSelection)
        collections_layout.addWidget(QLabel("选择收藏："))
        collections_layout.addWidget(self.collections_list)

        collections_btn_layout = QHBoxLayout()
        add_collection_btn = QPushButton("添加收藏")
        add_collection_btn.clicked.connect(self._on_add_collection)
        collections_btn_layout.addWidget(add_collection_btn)
        collections_btn_layout.addStretch()
        collections_layout.addLayout(collections_btn_layout)
        layout.addWidget(collections_group)

        # Tags
        tags_group = QGroupBox("标签")
        tags_layout = QVBoxLayout(tags_group)

        self.tags_list = QListWidget()
        self.tags_list.setMaximumHeight(120)
        self.tags_list.setSelectionMode(QListWidget.MultiSelection)
        tags_layout.addWidget(QLabel("选择标签："))
        tags_layout.addWidget(self.tags_list)

        tag_input_layout = QHBoxLayout()
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("输入新标签名称...")
        tag_input_layout.addWidget(self.tags_input)

        add_tag_btn = QPushButton("添加新标签")
        add_tag_btn.clicked.connect(self._on_add_new_tag)
        tag_input_layout.addWidget(add_tag_btn)

        tags_layout.addLayout(tag_input_layout)
        layout.addWidget(tags_group)

        layout.addStretch()
        return widget

    def _create_cast_crew_tab(self) -> QWidget:
        """Create the cast and crew tab."""
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # Cast table
        cast_group = QGroupBox("演员")
        cast_layout = QVBoxLayout(cast_group)
        self.cast_table = QTableWidget()
        self.cast_table.setColumnCount(4)
        self.cast_table.setHorizontalHeaderLabels(["姓名", "角色", "", ""])
        self.cast_table.horizontalHeader().setStretchLastSection(False)
        self.cast_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.cast_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.cast_table.itemChanged.connect(self._on_field_changed)
        cast_layout.addWidget(self.cast_table)

        cast_btn_layout = QHBoxLayout()
        add_cast_btn = QPushButton("添加演员")
        add_cast_btn.clicked.connect(self._on_add_cast_member)
        cast_btn_layout.addWidget(add_cast_btn)
        cast_btn_layout.addStretch()
        cast_layout.addLayout(cast_btn_layout)
        layout.addWidget(cast_group)

        # Crew table
        crew_group = QGroupBox("工作人员")
        crew_layout = QVBoxLayout(crew_group)
        self.crew_table = QTableWidget()
        self.crew_table.setColumnCount(4)
        self.crew_table.setHorizontalHeaderLabels(["姓名", "职位", "", ""])
        self.crew_table.horizontalHeader().setStretchLastSection(False)
        self.crew_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        self.crew_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.crew_table.itemChanged.connect(self._on_field_changed)
        crew_layout.addWidget(self.crew_table)

        crew_btn_layout = QHBoxLayout()
        add_crew_btn = QPushButton("添加工作人员")
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
            self.title_label.setText("未选择媒体")
            self._disable_controls()
        else:
            self._load_media_item(media_item)
            self.title_label.setText(f"编辑：{media_item.title}")
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

        # Load favorite status
        self.favorite_checkbox.setChecked(len(media_item.favorites) > 0)

    def _load_collections(self, media_item: MediaItem) -> None:
        """Load collections for the media item."""
        from .search_service import SearchService

        search_service = SearchService()
        all_collections = search_service.get_available_collections()

        self.collections_list.clear()
        selected_collection_ids = {c.id for c in media_item.collections}

        for collection in all_collections:
            item = QListWidgetItem(collection.name)
            item.setData(Qt.UserRole, collection.id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(
                Qt.Checked if collection.id in selected_collection_ids else Qt.Unchecked
            )
            self.collections_list.addItem(item)

    def _load_tags(self, media_item: MediaItem) -> None:
        """Load tags for the media item."""
        from .search_service import SearchService

        search_service = SearchService()
        all_tags = search_service.get_available_tags()

        self.tags_list.clear()
        selected_tag_ids = {t.id for t in media_item.tags}

        for tag in all_tags:
            item = QListWidgetItem(tag.name)
            item.setData(Qt.UserRole, tag.id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(
                Qt.Checked if tag.id in selected_tag_ids else Qt.Unchecked
            )
            self.tags_list.addItem(item)

        self.tags_input.clear()

    def _load_cast_crew(self, media_item: MediaItem) -> None:
        """Load cast and crew for the media item."""
        self.cast_table.setRowCount(0)
        self.crew_table.setRowCount(0)

        for credit in media_item.credits:
            if credit.role == "actor":
                self._add_cast_row(
                    credit.person.name,
                    credit.character_name or "",
                    credit.id,
                    credit.person.id,
                )
            else:
                self._add_crew_row(
                    credit.person.name, credit.role, credit.id, credit.person.id
                )

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
        self.tags_list.clear()
        self.collections_list.clear()
        self.favorite_checkbox.setChecked(False)
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
        self.save_button.setEnabled(
            self._is_dirty and self._current_media_item is not None
        )
        self.reset_button.setEnabled(
            self._is_dirty and self._current_media_item is not None
        )

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

            media_type = (
                "movie" if self._current_media_item.media_type == "movie" else "tv"
            )
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
            "刷新",
            "Refresh functionality would fetch fresh data from TMDB/TVDB.",
        )

    @Slot()
    def _on_add_collection(self) -> None:
        """Handle add collection button click."""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add New Collection")
        layout = QVBoxLayout(dialog)

        collection_input = QLineEdit()
        collection_input.setPlaceholderText(
            "Enter collection name (e.g., 'Watchlist', 'Kids')"
        )
        layout.addWidget(QLabel("Collection Name:"))
        layout.addWidget(collection_input)

        description_input = QTextEdit()
        description_input.setPlaceholderText("Optional description")
        description_input.setMaximumHeight(80)
        layout.addWidget(QLabel("Description:"))
        layout.addWidget(description_input)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)

        if dialog.exec() == QDialog.Accepted:
            name = collection_input.text().strip()
            if name:
                try:
                    with transactional_context() as uow:
                        collection_repo = uow.get_repository(Collection)
                        existing = collection_repo.filter_by(name=name)

                        if existing:
                            collection = existing[0]
                        else:
                            collection = Collection(
                                name=name,
                                description=description_input.toPlainText() or None,
                            )
                            collection_repo.create(collection)

                    # Reload collections
                    self._load_collections(self._current_media_item)
                    self._is_dirty = True
                    self._update_button_states()
                except Exception as e:
                    self._logger.error(f"Error creating collection: {e}")
                    QMessageBox.critical(
                        self, "Error", f"Failed to create collection: {str(e)}"
                    )

    @Slot()
    def _on_add_new_tag(self) -> None:
        """Handle add new tag button click."""
        tag_name = self.tags_input.text().strip()
        if not tag_name:
            QMessageBox.warning(self, "Invalid Input", "Please enter a tag name.")
            return

        try:
            with transactional_context() as uow:
                tag_repo = uow.get_repository(Tag)
                existing = tag_repo.filter_by(name=tag_name)

                if existing:
                    QMessageBox.information(
                        self, "Tag Exists", f"Tag '{tag_name}' already exists."
                    )
                else:
                    tag = Tag(name=tag_name)
                    tag_repo.create(tag)

            # Reload tags
            self.tags_input.clear()
            self._load_tags(self._current_media_item)
            self._is_dirty = True
            self._update_button_states()
        except Exception as e:
            self._logger.error(f"Error creating tag: {e}")
            QMessageBox.critical(self, "Error", f"Failed to create tag: {str(e)}")

    @Slot()
    def _on_add_cast_member(self) -> None:
        """Handle add cast member button click."""
        dialog = QDialog(self)
        dialog.setWindowTitle("添加演员")
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
        dialog.setWindowTitle("添加工作人员")
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
        remove_btn = QPushButton("移除")
        remove_btn.clicked.connect(lambda: self.collections_table.removeRow(row))
        self.collections_table.setCellWidget(row, 1, remove_btn)

    def _add_cast_row(
        self,
        name: str,
        character: str,
        credit_id: int | None,
        person_id: int | None = None,
    ) -> None:
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
            view_btn = QPushButton("查看")
            view_btn.clicked.connect(lambda: self._on_view_person_clicked(person_id))
            self.cast_table.setCellWidget(row, 2, view_btn)

        # Remove button
        remove_btn = QPushButton("移除")
        remove_btn.clicked.connect(lambda: self.cast_table.removeRow(row))
        self.cast_table.setCellWidget(row, 3, remove_btn)

    def _add_crew_row(
        self, name: str, role: str, credit_id: int | None, person_id: int | None = None
    ) -> None:
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
            view_btn = QPushButton("查看")
            view_btn.clicked.connect(lambda: self._on_view_person_clicked(person_id))
            self.crew_table.setCellWidget(row, 2, view_btn)

        # Remove button
        remove_btn = QPushButton("移除")
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
            QMessageBox.warning(
                self, "Validation Error", "Year must be between 1800 and 2100"
            )
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
        self._current_media_item.season = (
            self.season_input.value() if self.season_input.value() > 0 else None
        )
        self._current_media_item.episode = (
            self.episode_input.value() if self.episode_input.value() > 0 else None
        )
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
        if self._current_media_item is None:
            return

        try:
            # Save tags
            tag_repo = uow.get_repository(Tag)
            selected_tag_ids = []

            for i in range(self.tags_list.count()):
                item = self.tags_list.item(i)
                if item.checkState() == Qt.Checked:
                    tag_id = item.data(Qt.UserRole)
                    selected_tag_ids.append(tag_id)

            # Clear existing tags and add selected ones
            self._current_media_item.tags = []
            for tag_id in selected_tag_ids:
                tag = tag_repo.read(tag_id)
                if tag:
                    self._current_media_item.tags.append(tag)

            # Save collections
            collection_repo = uow.get_repository(Collection)
            selected_collection_ids = []

            for i in range(self.collections_list.count()):
                item = self.collections_list.item(i)
                if item.checkState() == Qt.Checked:
                    collection_id = item.data(Qt.UserRole)
                    selected_collection_ids.append(collection_id)

            # Clear existing collections and add selected ones
            self._current_media_item.collections = []
            for collection_id in selected_collection_ids:
                collection = collection_repo.read(collection_id)
                if collection:
                    self._current_media_item.collections.append(collection)

            # Save favorite status
            favorite_repo = uow.get_repository(Favorite)
            is_favorite = self.favorite_checkbox.isChecked()
            existing_favorite = favorite_repo.filter_by(
                media_item_id=self._current_media_item.id
            )

            if is_favorite and not existing_favorite:
                favorite = Favorite(media_item_id=self._current_media_item.id)
                favorite_repo.create(favorite)
            elif not is_favorite and existing_favorite:
                favorite_repo.delete(existing_favorite[0].id)

        except Exception as e:
            self._logger.error(f"Error saving collections and tags: {e}")
            raise
