#!/usr/bin/env python3
"""
Demo script for testing the new media views MVC architecture.
This script creates a simple application to showcase the new components.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget, QHBoxLayout, QSplitter
from PySide6.QtCore import Qt

from media_manager.library_view_model import LibraryViewModel
from media_manager.media_grid_view import MediaGridView
from media_manager.media_table_view import MediaTableView
from media_manager.detail_panel import DetailPanel


class MediaViewsDemo(QMainWindow):
    """Demo application for testing media views."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Media Views Demo - MVC Architecture")
        self.setGeometry(100, 100, 1400, 900)
        
        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QHBoxLayout(central_widget)
        
        # Create splitter
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # Create view model
        self.view_model = LibraryViewModel()
        
        # Create views
        self.grid_view = MediaGridView()
        self.table_view = MediaTableView()
        self.detail_panel = DetailPanel()
        
        # Set up models
        self.grid_view.set_model(self.view_model)
        self.table_view.set_model(self.view_model)
        
        # Add views to splitter
        splitter.addWidget(self.grid_view)
        splitter.addWidget(self.detail_panel)
        
        # Set splitter sizes
        splitter.setSizes([1000, 400])
        
        # Connect signals
        self._connect_signals()
        
        # Load some demo data
        self._load_demo_data()
    
    def _connect_signals(self):
        """Connect signals between components."""
        # Grid view signals
        self.grid_view.item_selected.connect(self.detail_panel.set_media_item)
        self.grid_view.item_activated.connect(self._on_item_activated)
        
        # Table view signals
        self.table_view.item_selected.connect(self.detail_panel.set_media_item)
        self.table_view.item_activated.connect(self._on_item_activated)
        
        # Detail panel signals
        self.detail_panel.edit_requested.connect(self._on_edit_requested)
        self.detail_panel.play_requested.connect(self._on_play_requested)
        
        # View model signals
        self.view_model.data_loaded.connect(self._on_data_loaded)
        self.view_model.error_occurred.connect(self._on_error)
    
    def _load_demo_data(self):
        """Load demo data for testing."""
        # Since we don't have a real database, create some mock data
        # In a real application, this would come from the repository
        
        # Create mock media items
        from media_manager.persistence.models import MediaItem, MediaFile, Artwork, Library
        from pathlib import Path
        
        # Mock library
        library = Library(id=1, name="Demo Library", path="/demo", media_type="movie")
        
        # Mock media items
        items = []
        
        # Movie 1
        movie1 = MediaItem(
            id=1,
            library_id=1,
            title="The Matrix",
            media_type="movie",
            year=1999,
            description="A computer hacker learns about the true nature of reality.",
            rating=8.7,
            runtime=136
        )
        
        # Add file
        file1 = MediaFile(
            id=1,
            media_item_id=1,
            path="/demo/matrix.mkv",
            filename="matrix.mkv",
            file_size=2*1024*1024*1024,  # 2GB
            resolution="1920x1080"
        )
        movie1.files = [file1]
        
        # Add poster
        poster1 = Artwork(
            id=1,
            media_item_id=1,
            artwork_type="poster",
            local_path=Path(__file__).parent / "demo_poster.jpg",  # Won't exist but that's fine
            url="https://example.com/matrix_poster.jpg"
        )
        movie1.artworks = [poster1]
        
        items.append(movie1)
        
        # Movie 2
        movie2 = MediaItem(
            id=2,
            library_id=1,
            title="Inception",
            media_type="movie",
            year=2010,
            description="A thief who steals corporate secrets through dream-sharing technology.",
            rating=8.8,
            runtime=148
        )
        
        file2 = MediaFile(
            id=2,
            media_item_id=2,
            path="/demo/inception.mkv",
            filename="inception.mkv",
            file_size=2.5*1024*1024*1024,  # 2.5GB
            resolution="1920x1080"
        )
        movie2.files = [file2]
        
        poster2 = Artwork(
            id=2,
            media_item_id=2,
            artwork_type="poster",
            local_path=Path(__file__).parent / "inception_poster.jpg",
            url="https://example.com/inception_poster.jpg"
        )
        movie2.artworks = [poster2]
        
        items.append(movie2)
        
        # TV Episode
        episode1 = MediaItem(
            id=3,
            library_id=1,
            title="Pilot",
            media_type="tv",
            year=2023,
            season=1,
            episode=1,
            description="Series pilot episode.",
            rating=7.5,
            runtime=45
        )
        
        file3 = MediaFile(
            id=3,
            media_item_id=3,
            path="/demo/pilot.mkv",
            filename="pilot.mkv",
            file_size=500*1024*1024,  # 500MB
            resolution="1920x1080"
        )
        episode1.files = [file3]
        
        items.append(episode1)
        
        # Add items to view model directly (bypassing repository for demo)
        self.view_model._items = items
        self.view_model._filtered_items = items.copy()
        self.view_model._total_count = len(items)
        
        # Emit data loaded signal
        self.view_model.data_loaded.emit(len(items))
    
    def _on_item_activated(self, item):
        """Handle item activation."""
        print(f"Activated: {item.title}")
        if item.files:
            print(f"  File: {item.files[0].path}")
    
    def _on_edit_requested(self, item):
        """Handle edit request."""
        print(f"Edit requested for: {item.title}")
    
    def _on_play_requested(self, item):
        """Handle play request."""
        print(f"Play requested for: {item.title}")
    
    def _on_data_loaded(self, count):
        """Handle data loaded."""
        print(f"Loaded {count} media items")
    
    def _on_error(self, error):
        """Handle error."""
        print(f"Error: {error}")


def main():
    """Main entry point."""
    app = QApplication(sys.argv)
    
    # Create and show demo window
    window = MediaViewsDemo()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()