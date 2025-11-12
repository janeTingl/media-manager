"""Basic smoke test for the new media views implementation."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def test_imports():
    """Test that all new components can be imported."""
    try:
        from media_manager.library_view_model import LibraryViewModel
        from media_manager.media_grid_view import MediaGridView
        from media_manager.media_table_view import MediaTableView
        from media_manager.detail_panel import DetailPanel
        print("✓ All imports successful")
        return True
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality without Qt GUI."""
    try:
        # Test view model creation
        from media_manager.library_view_model import LibraryViewModel
        model = LibraryViewModel()
        
        # Test basic properties
        assert model.rowCount() == 0
        assert model.columnCount() == 8
        assert model.total_count() == 0
        assert model.filtered_count() == 0
        assert not model.is_loading()
        
        print("✓ LibraryViewModel basic functionality works")
        
        # Test data access methods
        assert model.get_item_at_row(0) is None
        assert model.get_items_for_indices([]) == []
        
        print("✓ LibraryViewModel data access methods work")
        
        # Test header data
        header = model.headerData(0, 1, 0)  # DisplayRole
        expected_headers = ["Title", "Year", "Type", "Rating", "Duration", "Added", "Size", "Status"]
        for i, expected in enumerate(expected_headers):
            header = model.headerData(i, 1, 0)  # Horizontal, DisplayRole
            assert header == expected, f"Header {i}: expected '{expected}', got '{header}'"
        
        print("✓ LibraryViewModel header data works")
        
        return True
        
    except Exception as e:
        print(f"✗ Basic functionality test failed: {e}")
        return False

def test_repository_integration():
    """Test repository integration."""
    try:
        from media_manager.persistence.repositories import MediaItemRepository
        
        # Test repository creation
        repo = MediaItemRepository()
        assert repo is not None
        
        print("✓ MediaItemRepository creation works")
        
        # Test repository methods exist
        assert hasattr(repo, 'get_all')
        assert hasattr(repo, 'get_by_library')
        assert hasattr(repo, 'get_by_id')
        assert hasattr(repo, 'search')
        
        print("✓ MediaItemRepository has required methods")
        
        return True
        
    except Exception as e:
        print(f"✗ Repository integration test failed: {e}")
        return False

def test_model_structure():
    """Test that the model structure is correct."""
    try:
        from media_manager.library_view_model import LibraryViewModel
        
        model = LibraryViewModel()
        
        # Test custom roles
        assert hasattr(model, 'MediaItemRole')
        assert hasattr(model, 'PosterRole')
        assert hasattr(model, 'RatingRole')
        assert hasattr(model, 'YearRole')
        assert hasattr(model, 'MediaTypeRole')
        
        print("✓ Custom roles defined")
        
        # Test signals
        assert hasattr(model, 'data_loaded')
        assert hasattr(model, 'loading_started')
        assert hasattr(model, 'loading_finished')
        assert hasattr(model, 'error_occurred')
        
        print("✓ Signals defined")
        
        return True
        
    except Exception as e:
        print(f"✗ Model structure test failed: {e}")
        return False

def main():
    """Run all smoke tests."""
    print("Running smoke tests for media views...")
    print()
    
    tests = [
        ("Import Test", test_imports),
        ("Basic Functionality Test", test_basic_functionality),
        ("Repository Integration Test", test_repository_integration),
        ("Model Structure Test", test_model_structure),
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
        print("🎉 All smoke tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())