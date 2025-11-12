"""Logic-only tests for media views that don't require PySide6."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_repository_logic():
    """Test repository logic without database."""
    try:
        # Test that the repository class can be defined
        from media_manager.persistence.repositories import MediaItemRepository
        
        # Check class definition
        assert MediaItemRepository is not None
        
        # Check method definitions
        methods = ['get_all', 'get_by_library', 'get_by_id', 'search']
        for method in methods:
            assert hasattr(MediaItemRepository, method), f"Missing method: {method}"
        
        print("✓ MediaItemRepository class structure is correct")
        return True
        
    except Exception as e:
        print(f"✗ Repository logic test failed: {e}")
        return False

def test_imports_without_qt():
    """Test imports without actually importing Qt components."""
    try:
        # Test that we can import the persistence components
        from media_manager.persistence.models import MediaItem, Library, MediaFile, Artwork
        from media_manager.persistence.repositories import MediaItemRepository
        
        print("✓ Persistence components import correctly")
        
        # Test basic model creation
        library = Library(id=1, name="Test Library", path="/test", media_type="movie")
        assert library.id == 1
        assert library.name == "Test Library"
        
        media_item = MediaItem(
            id=1,
            library_id=1,
            title="Test Movie",
            media_type="movie",
            year=2023
        )
        assert media_item.title == "Test Movie"
        assert media_item.media_type == "movie"
        
        print("✓ Model creation works correctly")
        return True
        
    except Exception as e:
        print(f"✗ Non-QT imports test failed: {e}")
        return False

def test_file_structure():
    """Test that all required files exist and have basic structure."""
    try:
        base_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'media_manager')
        
        required_files = [
            'library_view_model.py',
            'media_grid_view.py', 
            'media_table_view.py',
            'detail_panel.py'
        ]
        
        for filename in required_files:
            filepath = os.path.join(base_path, filename)
            assert os.path.exists(filepath), f"Missing file: {filename}"
            
            # Check file has content
            with open(filepath, 'r') as f:
                content = f.read()
                assert len(content) > 1000, f"File too small: {filename}"
                
                # Check for key classes/functions
                if filename == 'library_view_model.py':
                    assert 'class LibraryViewModel' in content
                    assert 'QAbstractItemModel' in content
                elif filename == 'media_grid_view.py':
                    assert 'class MediaGridView' in content
                    assert 'QListView' in content
                elif filename == 'media_table_view.py':
                    assert 'class MediaTableView' in content
                    assert 'QTableView' in content
                elif filename == 'detail_panel.py':
                    assert 'class DetailPanel' in content
                    assert 'QFrame' in content
        
        print("✓ All required files exist with proper structure")
        return True
        
    except Exception as e:
        print(f"✗ File structure test failed: {e}")
        return False

def test_main_window_integration():
    """Test that main window has been updated to include new components."""
    try:
        base_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'media_manager')
        main_window_path = os.path.join(base_path, 'main_window.py')
        
        with open(main_window_path, 'r') as f:
            content = f.read()
            
            # Check for new imports
            assert 'from .detail_panel import DetailPanel' in content
            assert 'from .library_view_model import LibraryViewModel' in content
            assert 'from .media_grid_view import MediaGridView' in content
            assert 'from .media_table_view import MediaTableView' in content
            
            # Check for new component initialization
            assert 'self.library_view_model = LibraryViewModel' in content
            assert 'self.media_grid_view = MediaGridView' in content
            assert 'self.media_table_view = MediaTableView' in content
            assert 'self.detail_panel = DetailPanel' in content
            
            # Check for view switching functionality
            assert '_switch_view' in content
            assert '_set_media_filter' in content
            assert 'view_stack' in content
        
        print("✓ MainWindow integration is correct")
        return True
        
    except Exception as e:
        print(f"✗ MainWindow integration test failed: {e}")
        return False

def test_persistence_integration():
    """Test that persistence layer has been extended properly."""
    try:
        base_path = os.path.join(os.path.dirname(__file__), '..', 'src', 'media_manager', 'persistence')
        repos_path = os.path.join(base_path, 'repositories.py')
        
        with open(repos_path, 'r') as f:
            content = f.read()
            
            # Check for MediaItemRepository
            assert 'class MediaItemRepository:' in content
            assert 'def get_all(self)' in content
            assert 'def get_by_library(self' in content
            assert 'def get_by_id(self' in content
            assert 'def search(self' in content
            
            # Check for proper imports
            assert 'from sqlalchemy.orm import selectinload' in content
            assert 'from .models import Library, MediaItem' in content
        
        print("✓ Persistence layer integration is correct")
        return True
        
    except Exception as e:
        print(f"✗ Persistence integration test failed: {e}")
        return False

def main():
    """Run all logic-only tests."""
    print("Running logic-only tests for media views...")
    print()
    
    tests = [
        ("Repository Logic Test", test_repository_logic),
        ("Non-QT Imports Test", test_imports_without_qt),
        ("File Structure Test", test_file_structure),
        ("MainWindow Integration Test", test_main_window_integration),
        ("Persistence Integration Test", test_persistence_integration),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Running {test_name}...")
        if test_func():
            passed += 1
        print()
    
    print(f"Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All logic-only tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())