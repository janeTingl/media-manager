"""Reusable dialog for displaying person and company details."""

from __future__ import annotations

from typing import Optional, Union
from pathlib import Path

from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QScrollArea,
    QWidget,
    QTextEdit,
    QGroupBox,
    QSplitter,
)

from .person_service import PersonDetails, PersonService
from .company_service import CompanyDetails, CompanyService


class EntityDetailDialog(QDialog):
    """Reusable dialog for displaying person or company details."""
    
    # Signals
    media_item_selected = Signal(int)  # media_item_id
    
    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        
        self._person_service = PersonService()
        self._company_service = CompanyService()
        self._current_entity: Optional[Union[PersonDetails, CompanyDetails]] = None
        
        self.setWindowTitle("Entity Details")
        self.resize(900, 700)
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Setup the dialog UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Create splitter for main content
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left panel: Image and basic info
        left_panel = self._create_left_panel()
        splitter.addWidget(left_panel)
        
        # Right panel: Biography/description and credits
        right_panel = self._create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        layout.addWidget(splitter)
        
        # Bottom buttons
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        self._close_button = QPushButton("Close")
        self._close_button.clicked.connect(self.accept)
        button_layout.addWidget(self._close_button)
        
        layout.addLayout(button_layout)
    
    def _create_left_panel(self) -> QWidget:
        """Create the left panel with image and basic info."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Image container
        image_group = QGroupBox("Photo")
        image_layout = QVBoxLayout(image_group)
        
        self._image_label = QLabel()
        self._image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._image_label.setMinimumSize(200, 300)
        self._image_label.setMaximumSize(300, 450)
        self._image_label.setScaledContents(False)
        self._image_label.setStyleSheet("""
            QLabel {
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f9f9f9;
            }
        """)
        image_layout.addWidget(self._image_label)
        
        layout.addWidget(image_group)
        
        # Basic info container
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)
        
        self._name_label = QLabel()
        self._name_label.setStyleSheet("font-size: 16px; font-weight: bold;")
        self._name_label.setWordWrap(True)
        info_layout.addWidget(self._name_label)
        
        self._info_label = QLabel()
        self._info_label.setWordWrap(True)
        self._info_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        info_layout.addWidget(self._info_label)
        
        info_layout.addStretch()
        
        layout.addWidget(info_group)
        
        return panel
    
    def _create_right_panel(self) -> QWidget:
        """Create the right panel with biography and credits."""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Biography/description section
        bio_group = QGroupBox("Biography")
        bio_layout = QVBoxLayout(bio_group)
        
        self._biography_text = QTextEdit()
        self._biography_text.setReadOnly(True)
        self._biography_text.setMaximumHeight(200)
        bio_layout.addWidget(self._biography_text)
        
        layout.addWidget(bio_group)
        
        # Credits/productions table
        credits_group = QGroupBox("Filmography")
        credits_layout = QVBoxLayout(credits_group)
        
        self._credits_table = QTableWidget()
        self._credits_table.setColumnCount(5)
        self._credits_table.setHorizontalHeaderLabels(["Title", "Year", "Role", "Character", "Rating"])
        self._credits_table.horizontalHeader().setStretchLastSection(False)
        self._credits_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._credits_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._credits_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._credits_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self._credits_table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeMode.ResizeToContents)
        self._credits_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self._credits_table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self._credits_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._credits_table.doubleClicked.connect(self._on_credit_double_clicked)
        
        credits_layout.addWidget(self._credits_table)
        
        layout.addWidget(credits_group)
        
        return panel
    
    def show_person(self, person_id: int) -> None:
        """Show details for a person.
        
        Args:
            person_id: Database person ID
        """
        person = self._person_service.get_person_by_id(person_id)
        if not person:
            return
        
        self._current_entity = person
        self.setWindowTitle(f"Person Details - {person.name}")
        
        # Update name
        self._name_label.setText(person.name)
        
        # Update info
        info_parts = []
        if person.known_for_department:
            info_parts.append(f"Known for: {person.known_for_department}")
        if person.birthday:
            info_parts.append(f"Born: {person.birthday}")
            if person.deathday:
                info_parts.append(f"Died: {person.deathday}")
        if person.place_of_birth:
            info_parts.append(f"Birthplace: {person.place_of_birth}")
        
        self._info_label.setText("\n".join(info_parts) if info_parts else "No additional information")
        
        # Update biography
        if person.biography:
            self._biography_text.setPlainText(person.biography)
        else:
            self._biography_text.setPlainText("No biography available.")
        
        # Update image
        self._load_person_headshot(person_id)
        
        # Update filmography table
        self._credits_table.setRowCount(len(person.filmography))
        for row, entry in enumerate(person.filmography):
            # Title
            title_item = QTableWidgetItem(entry.media_item_title)
            title_item.setData(Qt.ItemDataRole.UserRole, entry.media_item_id)
            self._credits_table.setItem(row, 0, title_item)
            
            # Year
            year_text = str(entry.year) if entry.year else "-"
            self._credits_table.setItem(row, 1, QTableWidgetItem(year_text))
            
            # Role
            self._credits_table.setItem(row, 2, QTableWidgetItem(entry.role.capitalize()))
            
            # Character
            character_text = entry.character_name or "-"
            self._credits_table.setItem(row, 3, QTableWidgetItem(character_text))
            
            # Rating
            if entry.rating:
                rating_text = f"{entry.rating:.1f}/10"
                stars = "★" * int(entry.rating / 2) + "☆" * (5 - int(entry.rating / 2))
                rating_text += f" {stars}"
            else:
                rating_text = "-"
            self._credits_table.setItem(row, 4, QTableWidgetItem(rating_text))
        
        self._credits_table.resizeRowsToContents()
    
    def show_company(self, company_id: int) -> None:
        """Show details for a company.
        
        Args:
            company_id: Database company ID
        """
        company = self._company_service.get_company_by_id(company_id)
        if not company:
            return
        
        self._current_entity = company
        self.setWindowTitle(f"Company Details - {company.name}")
        
        # Update name
        self._name_label.setText(company.name)
        
        # Update info
        info_parts = []
        if company.headquarters:
            info_parts.append(f"Headquarters: {company.headquarters}")
        if company.homepage:
            info_parts.append(f"Website: {company.homepage}")
        
        self._info_label.setText("\n".join(info_parts) if info_parts else "No additional information")
        
        # Update description
        if company.description:
            self._biography_text.setPlainText(company.description)
        else:
            self._biography_text.setPlainText("No description available.")
        
        # Update image (logo)
        self._load_company_logo(company_id)
        
        # Update productions table
        self._credits_table.setColumnCount(4)
        self._credits_table.setHorizontalHeaderLabels(["Title", "Year", "Type", "Rating"])
        self._credits_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self._credits_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self._credits_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self._credits_table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self._credits_table.setRowCount(len(company.productions))
        for row, production in enumerate(company.productions):
            # Title
            title_item = QTableWidgetItem(production.media_item_title)
            title_item.setData(Qt.ItemDataRole.UserRole, production.media_item_id)
            self._credits_table.setItem(row, 0, title_item)
            
            # Year
            year_text = str(production.year) if production.year else "-"
            self._credits_table.setItem(row, 1, QTableWidgetItem(year_text))
            
            # Type
            self._credits_table.setItem(row, 2, QTableWidgetItem(production.media_type.capitalize()))
            
            # Rating
            if production.rating:
                rating_text = f"{production.rating:.1f}/10"
                stars = "★" * int(production.rating / 2) + "☆" * (5 - int(production.rating / 2))
                rating_text += f" {stars}"
            else:
                rating_text = "-"
            self._credits_table.setItem(row, 3, QTableWidgetItem(rating_text))
        
        self._credits_table.resizeRowsToContents()
    
    def _load_person_headshot(self, person_id: int) -> None:
        """Load and display person headshot.
        
        Args:
            person_id: Database person ID
        """
        # Try to get cached headshot
        headshot_path = self._person_service.get_headshot_path(person_id)
        
        if not headshot_path:
            # Try to download
            headshot_path = self._person_service.download_headshot(person_id)
        
        if headshot_path and headshot_path.exists():
            pixmap = QPixmap(str(headshot_path))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    QSize(300, 450),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._image_label.setPixmap(scaled_pixmap)
                return
        
        # No image available
        self._image_label.setText("No photo available")
    
    def _load_company_logo(self, company_id: int) -> None:
        """Load and display company logo.
        
        Args:
            company_id: Database company ID
        """
        # Try to get cached logo
        logo_path = self._company_service.get_logo_path(company_id)
        
        if not logo_path:
            # Try to download
            logo_path = self._company_service.download_logo(company_id)
        
        if logo_path and logo_path.exists():
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                scaled_pixmap = pixmap.scaled(
                    QSize(300, 200),
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
                self._image_label.setPixmap(scaled_pixmap)
                return
        
        # No logo available
        self._image_label.setText("No logo available")
    
    def _on_credit_double_clicked(self) -> None:
        """Handle double-click on credit/production row."""
        current_row = self._credits_table.currentRow()
        if current_row >= 0:
            title_item = self._credits_table.item(current_row, 0)
            if title_item:
                media_item_id = title_item.data(Qt.ItemDataRole.UserRole)
                if media_item_id:
                    self.media_item_selected.emit(media_item_id)
                    self.accept()
