"""TMDB Settings Dialog for configuring alternative TMDB endpoints."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from .settings import SettingsManager


class TMDBSettingsDialog(QDialog):
    """Dialog for configuring alternative TMDB API endpoints and credentials."""

    def __init__(
        self, settings: SettingsManager, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle(self.tr("TMDB Alternative Endpoints"))
        self.setMinimumWidth(500)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.tmdb_api_edit = QLineEdit(self)
        self.tmdb_api_edit.setPlaceholderText("https://api.themoviedb.org")
        form.addRow(self.tr("Alternative TMDB API Address:"), self.tmdb_api_edit)

        self.tmdb_image_edit = QLineEdit(self)
        self.tmdb_image_edit.setPlaceholderText("https://image.tmdb.org")
        form.addRow(self.tr("Alternative TMDB Image Address:"), self.tmdb_image_edit)

        self.tmdb_key_edit = QLineEdit(self)
        self.tmdb_key_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self.tmdb_key_edit.setPlaceholderText(
            self.tr("Leave empty to use main API key")
        )
        form.addRow(self.tr("Alternative TMDB API Key:"), self.tmdb_key_edit)

        layout.addLayout(form)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.load_settings()

    def load_settings(self) -> None:
        """Load current settings into the dialog fields."""
        api_base = self.settings.get_tmdb_api_base()
        if api_base and api_base != "https://api.themoviedb.org/3":
            self.tmdb_api_edit.setText(api_base)
        else:
            self.tmdb_api_edit.setText("")

        image_base = self.settings.get_tmdb_image_base()
        if image_base and image_base != "https://image.tmdb.org/t/p":
            self.tmdb_image_edit.setText(image_base)
        else:
            self.tmdb_image_edit.setText("")

        alt_key = self.settings.get_tmdb_api_key_alternative()
        self.tmdb_key_edit.setText(alt_key or "")

    def save_settings(self) -> None:
        """Save dialog field values to settings."""
        self.settings.set_tmdb_api_base(self.tmdb_api_edit.text().strip())
        self.settings.set_tmdb_image_base(self.tmdb_image_edit.text().strip())
        self.settings.set_tmdb_api_key_alternative(self.tmdb_key_edit.text().strip())
