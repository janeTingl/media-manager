"""Settings widget for poster download preferences."""

from __future__ import annotations

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .logging import get_logger
from .models import PosterSize, PosterType
from .settings import get_settings


class PosterSettingsWidget(QWidget):
    """Widget for configuring poster download settings."""

    # Signals
    settings_changed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._logger = get_logger().get_logger(__name__)
        self._settings = get_settings()

        self._setup_ui()
        self._load_settings()

    def _setup_ui(self) -> None:
        """Setup the poster settings UI."""
        layout = QVBoxLayout(self)

        # Auto-download section
        auto_group = QGroupBox("自动下载")
        auto_layout = QVBoxLayout(auto_group)

        self.auto_download_checkbox = QCheckBox("找到匹配时自动下载海报")
        self.auto_download_checkbox.stateChanged.connect(self._on_setting_changed)
        auto_layout.addWidget(self.auto_download_checkbox)

        layout.addWidget(auto_group)

        # Poster types section
        types_group = QGroupBox("海报类型")
        types_layout = QVBoxLayout(types_group)

        self.poster_checkbox = QCheckBox("下载海报")
        self.poster_checkbox.stateChanged.connect(self._on_setting_changed)
        types_layout.addWidget(self.poster_checkbox)

        self.fanart_checkbox = QCheckBox("下载同人画")
        self.fanart_checkbox.stateChanged.connect(self._on_setting_changed)
        types_layout.addWidget(self.fanart_checkbox)

        self.banner_checkbox = QCheckBox("下载横幅")
        self.banner_checkbox.stateChanged.connect(self._on_setting_changed)
        types_layout.addWidget(self.banner_checkbox)

        layout.addWidget(types_group)

        # Size preferences section
        size_group = QGroupBox("尺寸偏好")
        size_layout = QVBoxLayout(size_group)

        # Poster size
        poster_size_layout = QHBoxLayout()
        poster_size_layout.addWidget(QLabel("海报尺寸："))
        self.poster_size_combo = QComboBox()
        self.poster_size_combo.addItems([size.value for size in PosterSize])
        self.poster_size_combo.currentTextChanged.connect(self._on_setting_changed)
        poster_size_layout.addWidget(self.poster_size_combo)
        poster_size_layout.addStretch()
        size_layout.addLayout(poster_size_layout)

        # Fanart size
        fanart_size_layout = QHBoxLayout()
        fanart_size_layout.addWidget(QLabel("同人画尺寸："))
        self.fanart_size_combo = QComboBox()
        self.fanart_size_combo.addItems([size.value for size in PosterSize])
        self.fanart_size_combo.currentTextChanged.connect(self._on_setting_changed)
        fanart_size_layout.addWidget(self.fanart_size_combo)
        fanart_size_layout.addStretch()
        size_layout.addLayout(fanart_size_layout)

        # Banner size
        banner_size_layout = QHBoxLayout()
        banner_size_layout.addWidget(QLabel("横幅尺寸："))
        self.banner_size_combo = QComboBox()
        self.banner_size_combo.addItems([size.value for size in PosterSize])
        self.banner_size_combo.currentTextChanged.connect(self._on_setting_changed)
        banner_size_layout.addWidget(self.banner_size_combo)
        banner_size_layout.addStretch()
        size_layout.addLayout(banner_size_layout)

        layout.addWidget(size_group)

        # Download settings section
        download_group = QGroupBox("下载设置")
        download_layout = QVBoxLayout(download_group)

        # Max retries
        retries_layout = QHBoxLayout()
        retries_layout.addWidget(QLabel("最大重试次数："))
        self.max_retries_spinbox = QSpinBox()
        self.max_retries_spinbox.setMinimum(0)
        self.max_retries_spinbox.setMaximum(10)
        self.max_retries_spinbox.valueChanged.connect(self._on_setting_changed)
        retries_layout.addWidget(self.max_retries_spinbox)
        retries_layout.addStretch()
        download_layout.addLayout(retries_layout)

        # Timeout
        timeout_layout = QHBoxLayout()
        timeout_layout.addWidget(QLabel("超时（秒）："))
        self.timeout_spinbox = QSpinBox()
        self.timeout_spinbox.setMinimum(5)
        self.timeout_spinbox.setMaximum(300)
        self.timeout_spinbox.setValue(30)
        self.timeout_spinbox.valueChanged.connect(self._on_setting_changed)
        timeout_layout.addWidget(self.timeout_spinbox)
        timeout_layout.addStretch()
        download_layout.addLayout(timeout_layout)

        layout.addWidget(download_group)

        # Cache section
        cache_group = QGroupBox("缓存设置")
        cache_layout = QVBoxLayout(cache_group)

        # Cache directory
        cache_dir_layout = QHBoxLayout()
        cache_dir_layout.addWidget(QLabel("缓存目录："))
        self.cache_dir_edit = QLineEdit()
        self.cache_dir_edit.textChanged.connect(self._on_setting_changed)
        cache_dir_layout.addWidget(self.cache_dir_edit)

        self.browse_cache_button = QPushButton("浏览...")
        self.browse_cache_button.clicked.connect(self._on_browse_cache)
        cache_dir_layout.addWidget(self.browse_cache_button)
        cache_layout.addLayout(cache_dir_layout)

        # Clear cache button
        self.clear_cache_button = QPushButton("清空缓存")
        self.clear_cache_button.clicked.connect(self._on_clear_cache)
        cache_layout.addWidget(self.clear_cache_button)

        layout.addWidget(cache_group)

        layout.addStretch()

    def _load_settings(self) -> None:
        """Load settings from storage."""
        # Auto-download
        auto_download = self._settings.get_auto_download_posters()
        self.auto_download_checkbox.setChecked(auto_download)

        # Poster types
        enabled_types = self._settings.get_enabled_poster_types()
        self.poster_checkbox.setChecked(PosterType.POSTER.value in enabled_types)
        self.fanart_checkbox.setChecked(PosterType.FANART.value in enabled_types)
        self.banner_checkbox.setChecked(PosterType.BANNER.value in enabled_types)

        # Sizes
        self.poster_size_combo.setCurrentText(
            self._settings.get_poster_size(PosterType.POSTER.value)
        )
        self.fanart_size_combo.setCurrentText(
            self._settings.get_poster_size(PosterType.FANART.value)
        )
        self.banner_size_combo.setCurrentText(
            self._settings.get_poster_size(PosterType.BANNER.value)
        )

        # Download settings
        self.max_retries_spinbox.setValue(self._settings.get_max_retries())
        self.timeout_spinbox.setValue(self._settings.get_provider_timeout())

        # Cache directory
        cache_dir = self._settings.get_cache_dir()
        if cache_dir:
            self.cache_dir_edit.setText(cache_dir)

    def _save_settings(self) -> None:
        """Save settings to storage."""
        # Auto-download
        self._settings.set_auto_download_posters(
            self.auto_download_checkbox.isChecked()
        )

        # Poster types
        enabled_types = []
        if self.poster_checkbox.isChecked():
            enabled_types.append(PosterType.POSTER.value)
        if self.fanart_checkbox.isChecked():
            enabled_types.append(PosterType.FANART.value)
        if self.banner_checkbox.isChecked():
            enabled_types.append(PosterType.BANNER.value)
        self._settings.set_enabled_poster_types(enabled_types)

        # Sizes
        self._settings.set_poster_size(
            PosterType.POSTER.value, self.poster_size_combo.currentText()
        )
        self._settings.set_poster_size(
            PosterType.FANART.value, self.fanart_size_combo.currentText()
        )
        self._settings.set_poster_size(
            PosterType.BANNER.value, self.banner_size_combo.currentText()
        )

        # Download settings
        self._settings.set_max_retries(self.max_retries_spinbox.value())
        self._settings.set_provider_timeout(self.timeout_spinbox.value())

        # Cache directory
        cache_dir = self.cache_dir_edit.text().strip()
        if cache_dir:
            self._settings.set_cache_dir(cache_dir)

        # Save settings
        self._settings.save_settings()

    def save(self) -> None:
        """Persist the current poster preferences."""
        self._save_settings()

    def _on_setting_changed(self) -> None:
        """Handle setting change."""
        self._save_settings()
        self.settings_changed.emit()

    def _on_browse_cache(self) -> None:
        """Handle browse cache button click."""
        from PySide6.QtWidgets import QFileDialog

        directory = QFileDialog.getExistingDirectory(
            self, "选择缓存目录", self.cache_dir_edit.text()
        )
        if directory:
            self.cache_dir_edit.setText(directory)

    def _on_clear_cache(self) -> None:
        """Handle clear cache button click."""
        from PySide6.QtWidgets import QMessageBox

        reply = QMessageBox.question(
            self,
            "清空缓存",
            "确定要清空海报缓存吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )

        if reply == QMessageBox.Yes:
            try:
                # Import here to avoid circular imports
                from .poster_downloader import PosterDownloader

                cache_dir = self.cache_dir_edit.text().strip()
                if cache_dir:
                    downloader = PosterDownloader(cache_dir=cache_dir)
                else:
                    downloader = PosterDownloader()

                downloader.clear_cache()
                self._logger.info("Poster cache cleared")

                QMessageBox.information(self, "缓存已清空", "海报缓存已被清空。")
            except Exception as exc:
                self._logger.error(f"清空缓存失败：{exc}")
                QMessageBox.warning(self, "错误", f"清空缓存失败：{exc}")

    def get_enabled_poster_types(self) -> list[PosterType]:
        """Get the list of enabled poster types."""
        types = []
        if self.poster_checkbox.isChecked():
            types.append(PosterType.POSTER)
        if self.fanart_checkbox.isChecked():
            types.append(PosterType.FANART)
        if self.banner_checkbox.isChecked():
            types.append(PosterType.BANNER)
        return types
