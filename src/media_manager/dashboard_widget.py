"""Dashboard widget for displaying media analytics and statistics."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from .logging import get_logger
from .persistence.repositories import LibraryRepository
from .stats_service import StatsService

if TYPE_CHECKING:
    from PySide6.QtWidgets import QMainWindow

logger_instance = get_logger()
logger = logger_instance.get_logger(__name__)


class StatsCard(QWidget):
    """A card widget displaying a statistic."""

    def __init__(self, title: str, value: str, subtitle: str = "") -> None:
        """Initialize stats card.

        Args:
            title: Card title
            value: Main value to display
            subtitle: Optional subtitle
        """
        super().__init__()
        self.setStyleSheet(
            """
            StatsCard {
                background-color: #f5f5f5;
                border-radius: 8px;
                padding: 16px;
                border: 1px solid #e0e0e0;
            }
        """
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)

        title_label = QLabel(title)
        title_font = QFont()
        title_font.setPointSize(10)
        title_label.setFont(title_font)
        title_label.setStyleSheet("color: #666666; font-weight: bold;")
        layout.addWidget(title_label)

        value_label = QLabel(value)
        value_font = QFont()
        value_font.setPointSize(18)
        value_font.setBold(True)
        value_label.setFont(value_font)
        value_label.setStyleSheet("color: #1976d2;")
        layout.addWidget(value_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_font = QFont()
            subtitle_font.setPointSize(9)
            subtitle_label.setFont(subtitle_font)
            subtitle_label.setStyleSheet("color: #999999;")
            layout.addWidget(subtitle_label)

        layout.addStretch()

    def set_value(self, value: str) -> None:
        """Update the displayed value."""
        # Find and update the value label (second widget)
        if self.layout().count() > 1:
            widget = self.layout().itemAt(1).widget()
            if isinstance(widget, QLabel):
                widget.setText(value)


class DashboardWidget(QWidget):
    """Main dashboard widget showing media analytics."""

    # Signals
    data_updated = Signal()

    def __init__(self, parent: QMainWindow | None = None) -> None:
        """Initialize dashboard widget.

        Args:
            parent: Parent widget
        """
        super().__init__(parent)
        self._parent = parent
        self._logger = logger
        self._stats_service = StatsService()
        self._library_repository = LibraryRepository()
        self._current_library_id: int | None = None
        self._auto_refresh_timer = QTimer()
        self._auto_refresh_timer.timeout.connect(self._refresh_data)

        self._setup_ui()
        self._load_data()

    def _setup_ui(self) -> None:
        """Setup the UI layout."""
        layout = QVBoxLayout(self)

        # Filter bar
        filter_layout = self._create_filter_bar()
        layout.addLayout(filter_layout)

        # Scroll area for content
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)

        # Summary cards
        content_layout.addLayout(self._create_summary_cards())

        # Charts and lists
        content_layout.addLayout(self._create_charts_layout())

        # Recent activity
        content_layout.addWidget(self._create_recent_activity_group())

        content_layout.addStretch()

        scroll.setWidget(content_widget)
        layout.addWidget(scroll)

    def _create_filter_bar(self) -> QHBoxLayout:
        """Create filter control bar."""
        layout = QHBoxLayout()

        # Library filter
        layout.addWidget(QLabel(self.tr("Library:")))
        self.library_combo = QComboBox()
        self.library_combo.addItem(self.tr("All Libraries"), None)
        libraries = self._library_repository.get_active()
        for lib in libraries:
            self.library_combo.addItem(lib.name, lib.id)
        self.library_combo.currentIndexChanged.connect(self._on_library_changed)
        layout.addWidget(self.library_combo)

        layout.addSpacing(20)

        # Date range filters
        layout.addWidget(QLabel(self.tr("From:")))
        self.date_from = QDateEdit()
        self.date_from.setDate(
            (datetime.utcnow()).replace(day=1).date()
        )  # First day of month
        self.date_from.dateChanged.connect(self._on_date_changed)
        layout.addWidget(self.date_from)

        layout.addWidget(QLabel(self.tr("To:")))
        self.date_to = QDateEdit()
        self.date_to.setDate(datetime.utcnow().date())
        self.date_to.dateChanged.connect(self._on_date_changed)
        layout.addWidget(self.date_to)

        # Refresh button
        refresh_btn = QPushButton(self.tr("Refresh"))
        refresh_btn.clicked.connect(self._refresh_data)
        layout.addWidget(refresh_btn)

        layout.addStretch()

        return layout

    def _create_summary_cards(self) -> QHBoxLayout:
        """Create summary stat cards."""
        layout = QHBoxLayout()

        self.card_total = StatsCard(self.tr("Total Items"), "0")
        layout.addWidget(self.card_total)

        self.card_movies = StatsCard(self.tr("Movies"), "0")
        layout.addWidget(self.card_movies)

        self.card_tv = StatsCard(self.tr("TV Shows"), "0")
        layout.addWidget(self.card_tv)

        self.card_runtime = StatsCard(self.tr("Total Runtime"), self.tr("0 hours"))
        layout.addWidget(self.card_runtime)

        self.card_storage = StatsCard(self.tr("Storage"), self.tr("0 GB"))
        layout.addWidget(self.card_storage)

        return layout

    def _create_charts_layout(self) -> QHBoxLayout:
        """Create charts and top lists layout."""
        layout = QHBoxLayout()

        # Top Directors
        layout.addWidget(
            self._create_top_list_group(self.tr("Top Directors"), "directors")
        )

        # Top Actors
        layout.addWidget(self._create_top_list_group(self.tr("Top Actors"), "actors"))

        return layout

    def _create_top_list_group(self, title: str, list_type: str) -> QGroupBox:
        """Create a top list group box."""
        group = QGroupBox(title)
        layout = QVBoxLayout(group)

        self.top_lists = getattr(self, "top_lists", {})
        list_widget = QWidget()
        list_layout = QVBoxLayout(list_widget)
        list_layout.setContentsMargins(0, 0, 0, 0)
        list_layout.setSpacing(4)

        self.top_lists[list_type] = list_layout

        scroll = QScrollArea()
        scroll.setWidget(list_widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        layout.addWidget(scroll)

        return group

    def _create_recent_activity_group(self) -> QGroupBox:
        """Create recent activity group."""
        group = QGroupBox(self.tr("Recent Activity"))
        layout = QVBoxLayout(group)

        self.activity_widget = QWidget()
        self.activity_layout = QVBoxLayout(self.activity_widget)
        self.activity_layout.setContentsMargins(0, 0, 0, 0)
        self.activity_layout.setSpacing(4)

        scroll = QScrollArea()
        scroll.setWidget(self.activity_widget)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; }")
        layout.addWidget(scroll, 1)

        return group

    def _refresh_data(self) -> None:
        """Refresh dashboard data."""
        try:
            self._logger.debug("Refreshing dashboard data")
            library_id = self.library_combo.currentData()
            self._current_library_id = library_id

            # Clear cache to get fresh data
            self._stats_service.clear_cache()

            # Get item counts
            counts = self._stats_service.get_item_counts(library_id=library_id)
            self.card_total.set_value(str(counts["total"]))
            self.card_movies.set_value(str(counts["movies"]))
            self.card_tv.set_value(str(counts["tv"]))

            # Get runtime
            runtime_minutes = self._stats_service.get_total_runtime(
                library_id=library_id
            )
            runtime_hours = runtime_minutes / 60
            self.card_runtime.set_value(f"{runtime_hours:.1f} hours")

            # Get storage
            storage_bytes = self._stats_service.get_storage_usage(library_id=library_id)
            storage_gb = storage_bytes / (1024**3)
            self.card_storage.set_value(f"{storage_gb:.1f} GB")

            # Get top directors
            directors = self._stats_service.get_top_directors(
                limit=10, library_id=library_id
            )
            self._update_top_list("directors", directors)

            # Get top actors
            actors = self._stats_service.get_top_actors(limit=10, library_id=library_id)
            self._update_top_list("actors", actors)

            # Get recent activity
            activity = self._stats_service.get_recent_activity(
                limit=20, library_id=library_id
            )
            self._update_activity_list(activity)

            self.data_updated.emit()
            self._logger.debug("Dashboard data refreshed")
        except Exception as e:
            self._logger.error(f"Failed to refresh dashboard: {e}")

    def _update_top_list(self, list_type: str, items: list[dict]) -> None:
        """Update a top list."""
        # Clear existing items
        layout = self.top_lists[list_type]
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new items
        for item in items:
            label = QLabel(f"{item['name']} ({item['count']})")
            label.setStyleSheet("color: #333333; padding: 4px 0px;")
            layout.addWidget(label)

        # Add stretch
        layout.addStretch()

    def _update_activity_list(self, activities: list[dict]) -> None:
        """Update activity list."""
        # Clear existing items
        while self.activity_layout.count():
            item = self.activity_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Add new items
        for activity in activities:
            timestamp = datetime.fromisoformat(activity["timestamp"])
            time_str = timestamp.strftime("%Y-%m-%d %H:%M")
            label = QLabel(f"[{time_str}] {activity['type']}: {activity['title']}")
            label.setStyleSheet("color: #555555; padding: 4px 0px;")
            label.setWordWrap(True)
            self.activity_layout.addWidget(label)

        # Add stretch
        self.activity_layout.addStretch()

    def _on_library_changed(self) -> None:
        """Handle library selection change."""
        self._refresh_data()

    def _on_date_changed(self) -> None:
        """Handle date range change."""
        # For now, we refresh - in future, could use for activity filtering
        self._refresh_data()

    def _load_data(self) -> None:
        """Load initial data."""
        self._refresh_data()

    def start_auto_refresh(self, interval_ms: int = 30000) -> None:
        """Start auto-refresh timer.

        Args:
            interval_ms: Refresh interval in milliseconds
        """
        self._auto_refresh_timer.start(interval_ms)
        self._logger.debug(f"Auto-refresh started with interval {interval_ms}ms")

    def stop_auto_refresh(self) -> None:
        """Stop auto-refresh timer."""
        self._auto_refresh_timer.stop()
        self._logger.debug("Auto-refresh stopped")

    def on_data_mutation(self) -> None:
        """Called when data mutates (called by parent window)."""
        self._logger.debug("Data mutation detected, refreshing dashboard")
        self._refresh_data()
