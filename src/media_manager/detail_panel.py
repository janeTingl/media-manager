"""Detail panel showing artwork and key facts for selected media items."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from media_manager.logging import get_logger
from media_manager.persistence.models import MediaItem


class DetailPanel(QFrame):
    """
    Collapsible detail panel showing artwork and key facts.

    Displays comprehensive information about selected media items including
    posters, metadata, cast, and available actions.
    """

    # Signals
    edit_requested = Signal(object)  # MediaItem
    play_requested = Signal(object)  # MediaItem
    poster_download_requested = Signal(object)  # MediaItem
    external_link_clicked = Signal(str)  # URL

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # Setup frame properties
        self.setFrameStyle(QFrame.Shape.StyledPanel | QFrame.Shadow.Sunken)
        self.setMinimumWidth(300)
        self.setMaximumWidth(500)

        # Current item
        self._current_item: MediaItem | None = None

        # Logger
        self._logger = get_logger().get_logger(__name__)

        # Setup UI
        self._setup_ui()

        # Initially collapsed
        self._collapsed = True

    def _setup_ui(self) -> None:
        """Setup the detail panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Header with collapse button
        header_layout = QHBoxLayout()

        self._title_label = QLabel("详情")
        self._title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(self._title_label)

        header_layout.addStretch()

        self._collapse_button = QToolButton()
        self._collapse_button.setText("▲")
        self._collapse_button.setStyleSheet(
            "QToolButton { border: none; padding: 2px; }"
        )
        self._collapse_button.clicked.connect(self.toggle_collapse)
        header_layout.addWidget(self._collapse_button)

        layout.addLayout(header_layout)

        # Main content area
        self._content_widget = QWidget()
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(10)

        # Create scroll area for content
        scroll_area = QScrollArea()
        scroll_area.setWidget(self._content_widget)
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        layout.addWidget(scroll_area)

        # Setup content sections
        self._setup_poster_section()
        self._setup_metadata_section()
        self._setup_cast_section()
        self._setup_actions_section()
        self._setup_files_section()

    def _setup_poster_section(self) -> None:
        """Setup the poster display section."""
        self._poster_container = QGroupBox("海报")
        self._poster_layout = QVBoxLayout(self._poster_container)

        # Poster label
        self._poster_label = QLabel()
        self._poster_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._poster_label.setMinimumHeight(225)
        self._poster_label.setMaximumHeight(375)
        self._poster_label.setScaledContents(False)
        self._poster_label.setStyleSheet(
            """
            QLabel {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
        """
        )

        self._poster_layout.addWidget(self._poster_label)

        self._content_layout.addWidget(self._poster_container)

    def _setup_metadata_section(self) -> None:
        """Setup the metadata display section."""
        self._metadata_container = QGroupBox("信息")
        self._metadata_layout = QGridLayout(self._metadata_container)
        self._metadata_layout.setContentsMargins(10, 10, 10, 10)
        self._metadata_layout.setSpacing(5)

        # Create metadata labels
        self._metadata_labels = {}
        metadata_fields = [
            ("title", "标题"),
            ("year", "年份"),
            ("type", "类型"),
            ("rating", "评分"),
            ("runtime", "时长"),
            ("aired", "播出日期"),
            ("added", "添加日期"),
        ]

        for i, (key, label) in enumerate(metadata_fields):
            # Label
            label_widget = QLabel(f"{label}:")
            label_widget.setStyleSheet("font-weight: bold;")
            self._metadata_layout.addWidget(label_widget, i, 0)

            # Value
            value_widget = QLabel("-")
            value_widget.setWordWrap(True)
            value_widget.setTextInteractionFlags(
                Qt.TextInteractionFlag.TextSelectableByMouse
            )
            self._metadata_labels[key] = value_widget
            self._metadata_layout.addWidget(value_widget, i, 1)

        self._content_layout.addWidget(self._metadata_container)

    def _setup_cast_section(self) -> None:
        """Setup the cast display section."""
        self._cast_container = QGroupBox("演员")
        self._cast_layout = QVBoxLayout(self._cast_container)

        self._cast_label = QLabel("无演员信息")
        self._cast_label.setWordWrap(True)
        self._cast_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
            | Qt.TextInteractionFlag.LinksAccessibleByMouse
        )
        self._cast_label.setOpenExternalLinks(False)
        self._cast_label.linkActivated.connect(self._on_cast_link_clicked)

        self._cast_layout.addWidget(self._cast_label)

        self._content_layout.addWidget(self._cast_container)

    def _setup_actions_section(self) -> None:
        """Setup the action buttons section."""
        self._actions_container = QGroupBox("操作")
        self._actions_layout = QVBoxLayout(self._actions_container)

        # Action buttons
        self._play_button = QPushButton("播放")
        self._play_button.clicked.connect(self._on_play_clicked)
        self._actions_layout.addWidget(self._play_button)

        self._edit_button = QPushButton("编辑元数据")
        self._edit_button.clicked.connect(self._on_edit_clicked)
        self._actions_layout.addWidget(self._edit_button)

        self._download_poster_button = QPushButton("下载海报")
        self._download_poster_button.clicked.connect(self._on_download_poster_clicked)
        self._actions_layout.addWidget(self._download_poster_button)

        self._content_layout.addWidget(self._actions_container)

    def _setup_files_section(self) -> None:
        """Setup the files information section."""
        self._files_container = QGroupBox("文件")
        self._files_layout = QVBoxLayout(self._files_container)

        self._files_label = QLabel("无文件信息")
        self._files_label.setWordWrap(True)
        self._files_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self._files_layout.addWidget(self._files_label)

        self._content_layout.addWidget(self._files_container)

    def set_media_item(self, item: MediaItem | None) -> None:
        """Set the media item to display."""
        self._current_item = item

        if item:
            self._update_poster(item)
            self._update_metadata(item)
            self._update_cast(item)
            self._update_files(item)
            self._update_actions(item)
            self._title_label.setText(f"Details: {item.title}")
        else:
            self._clear_content()
            self._title_label.setText("Details")

        # Expand if we have content
        if item and self._collapsed:
            self.toggle_collapse()

    def toggle_collapse(self) -> None:
        """Toggle the collapsed state of the panel."""
        self._collapsed = not self._collapsed

        if self._collapsed:
            self._content_widget.hide()
            self._collapse_button.setText("▼")
            self.setMaximumWidth(50)
        else:
            self._content_widget.show()
            self._collapse_button.setText("▲")
            self.setMaximumWidth(500)

    def _update_poster(self, item: MediaItem) -> None:
        """Update the poster display."""
        # Look for poster artwork
        poster_url = None
        poster_path = None

        for artwork in item.artworks:
            if artwork.artwork_type == "poster":
                poster_path = artwork.local_path
                poster_url = artwork.url
                break

        if poster_path and poster_path.exists():
            # Load local poster
            pixmap = QPixmap(str(poster_path))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    self._poster_label.size(),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
                self._poster_label.setPixmap(scaled_pixmap)
                self._poster_label.setText("")
            else:
                self._poster_label.setText("Failed to load poster")
        elif poster_url:
            # Could implement async loading for remote posters
            self._poster_label.setText("Poster available online")
        else:
            self._poster_label.setText("No poster available")

    def _update_metadata(self, item: MediaItem) -> None:
        """Update the metadata display."""
        # Title
        self._metadata_labels["title"].setText(item.title or "Unknown")

        # Year
        self._metadata_labels["year"].setText(
            str(item.year) if item.year else "Unknown"
        )

        # Type
        self._metadata_labels["type"].setText(
            item.media_type.capitalize() if item.media_type else "Unknown"
        )

        # Rating with stars
        if item.rating:
            stars = "★" * int(item.rating / 2) + "☆" * (5 - int(item.rating / 2))
            self._metadata_labels["rating"].setText(f"{item.rating:.1f}/10 {stars}")
        else:
            self._metadata_labels["rating"].setText("Not rated")

        # Runtime
        if item.runtime:
            hours = item.runtime // 60
            minutes = item.runtime % 60
            runtime_str = f"{hours}h {minutes}m" if hours else f"{minutes}m"
            self._metadata_labels["runtime"].setText(runtime_str)
        else:
            self._metadata_labels["runtime"].setText("Unknown")

        # Aired date
        if item.aired_date:
            self._metadata_labels["aired"].setText(item.aired_date)
        else:
            self._metadata_labels["aired"].setText("Unknown")

        # Added date
        if item.created_at:
            self._metadata_labels["added"].setText(
                item.created_at.strftime("%Y-%m-%d %H:%M")
            )
        else:
            self._metadata_labels["added"].setText("Unknown")

    def _update_cast(self, item: MediaItem) -> None:
        """Update the cast display."""
        # Get cast from credits
        cast_members = []
        for credit in sorted(item.credits, key=lambda c: c.order):
            if credit.role == "actor" and credit.person:
                name = credit.person.name
                character_info = ""
                if credit.character_name:
                    character_info = f" ({credit.character_name})"
                # Create clickable link with person ID as data
                link = f'<a href="person:{credit.person.id}" style="text-decoration: none; color: #0066cc;">{name}</a>{character_info}'
                cast_members.append(link)

        if cast_members:
            cast_html = "<br>".join(cast_members[:10])  # Show top 10
            if len(cast_members) > 10:
                cast_html += f"<br>... and {len(cast_members) - 10} more"
            self._cast_label.setText(cast_html)
        else:
            self._cast_label.setText("No cast information available")

    def _update_files(self, item: MediaItem) -> None:
        """Update the files information."""
        if item.files:
            files_info = []
            total_size = 0

            for file in item.files:
                file_info = f"📁 {file.filename}"
                if file.file_size:
                    size_str = self._format_file_size(file.file_size)
                    file_info += f" ({size_str})"
                    total_size += file.file_size

                if file.resolution:
                    file_info += f" [{file.resolution}]"

                files_info.append(file_info)

            files_text = "\n".join(files_info)

            if total_size > 0:
                total_size_str = self._format_file_size(total_size)
                files_text += f"\n\nTotal: {total_size_str}"

            self._files_label.setText(files_text)
        else:
            self._files_label.setText("No file information available")

    def _update_actions(self, item: MediaItem) -> None:
        """Update the action buttons availability."""
        # Enable/disable buttons based on item state
        self._play_button.setEnabled(bool(item.files))
        self._edit_button.setEnabled(True)
        self._download_poster_button.setEnabled(True)

    def _clear_content(self) -> None:
        """Clear all content displays."""
        self._poster_label.clear()
        self._poster_label.setText("No item selected")

        for label in self._metadata_labels.values():
            label.setText("-")

        self._cast_label.setText("No cast information available")
        self._files_label.setText("No file information available")

        self._play_button.setEnabled(False)
        self._edit_button.setEnabled(False)
        self._download_poster_button.setEnabled(False)

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human readable format."""
        for unit in ["B", "KB", "MB", "GB", "TB"]:
            if size_bytes < 1024:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024
        return f"{size_bytes:.1f} PB"

    def _on_play_clicked(self) -> None:
        """Handle play button click."""
        if self._current_item:
            self.play_requested.emit(self._current_item)

    def _on_edit_clicked(self) -> None:
        """Handle edit button click."""
        if self._current_item:
            self.edit_requested.emit(self._current_item)

    def _on_download_poster_clicked(self) -> None:
        """Handle download poster button click."""
        if self._current_item:
            self.poster_download_requested.emit(self._current_item)

    def is_collapsed(self) -> bool:
        """Check if the panel is collapsed."""
        return self._collapsed

    def expand(self) -> None:
        """Expand the panel."""
        if self._collapsed:
            self.toggle_collapse()

    def collapse(self) -> None:
        """Collapse the panel."""
        if not self._collapsed:
            self.toggle_collapse()

    def _on_cast_link_clicked(self, link: str) -> None:
        """Handle cast member link click.

        Args:
            link: Link URL in format "person:123"
        """
        if link.startswith("person:"):
            try:
                person_id = int(link.split(":")[1])
                self._show_person_dialog(person_id)
            except (ValueError, IndexError) as exc:
                self._logger.error(f"Invalid person link: {link}, error: {exc}")

    def _show_person_dialog(self, person_id: int) -> None:
        """Show person detail dialog.

        Args:
            person_id: Database person ID
        """
        from .entity_detail_dialog import EntityDetailDialog

        dialog = EntityDetailDialog(self)
        dialog.show_person(person_id)
        dialog.exec()
