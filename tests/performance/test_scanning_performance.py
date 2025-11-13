"""Scanning performance benchmarks."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from src.media_manager.scan_engine import ScanEngine
from src.media_manager.persistence.database import DatabaseService
from src.media_manager.persistence.repositories import LibraryRepository

from .data_factories import SyntheticDataFactory
from .conftest import perf_thresholds


@pytest.fixture
def scan_engine(benchmark_db: DatabaseService) -> ScanEngine:
    """Create scan engine for benchmarking."""
    return ScanEngine(benchmark_db)


@pytest.fixture
def temp_media_library(tmp_path: Path) -> Path:
    """Create a temporary media library structure."""
    library_path = tmp_path / "media_library"
    library_path.mkdir()
    
    # Create directory structure
    movies_dir = library_path / "movies"
    tv_dir = library_path / "tv"
    movies_dir.mkdir()
    tv_dir.mkdir()
    
    # Create movie files
    for i in range(100):
        movie_file = movies_dir / f"Movie_{i:03d}.mp4"
        movie_file.write_bytes(b"fake movie content" * 1000)  # ~22KB file
    
    # Create TV show structure
    for show in range(10):
        show_dir = tv_dir / f"TV_Show_{show:02d}"
        show_dir.mkdir()
        
        for season in range(3):
            season_dir = show_dir / f"Season_{season + 1:02d}"
            season_dir.mkdir()
            
            for episode in range(10):
                episode_file = season_dir / f"Episode_{episode + 1:02d}.mp4"
                episode_file.write_bytes(b"fake episode content" * 500)  # ~11KB file
    
    return library_path


@pytest.fixture
def test_library(benchmark_db: DatabaseService, temp_media_library: Path) -> Library:
    """Create a test library in the database."""
    with benchmark_db.get_session() as session:
        factory = SyntheticDataFactory(session)
        library = factory.create_library(
            name="Scan Test Library",
            path=str(temp_media_library),
            media_type="mixed"
        )
        return library


@pytest.mark.benchmark
def test_scan_discovery_performance(
    benchmark, scan_engine: ScanEngine, temp_media_library: Path
) -> None:
    """Benchmark file discovery during scanning."""
    # Mock the file processing to focus on discovery performance
    with patch.object(scan_engine, '_process_file'):
        discovered_files = benchmark(
            scan_engine._discover_files,
            temp_media_library
        )
    
    # Should discover all created files
    expected_files = 100 + (10 * 3 * 10)  # 100 movies + 300 episodes
    assert len(discovered_files) == expected_files


@pytest.mark.benchmark
def test_scan_file_processing_performance(
    benchmark, scan_engine: ScanEngine, test_library: Library
) -> None:
    """Benchmark individual file processing."""
    # Create a test file path
    test_file = Path(test_library.path) / "test_movie.mp4"
    test_file.write_bytes(b"fake content" * 1000)
    
    # Benchmark processing a single file
    with patch('media_manager.scan_engine.os.path.getsize') as mock_size:
        mock_size.return_value = 22000  # 22KB
        
        result = benchmark(
            scan_engine._process_file,
            test_file,
            test_library.id
        )
    
    assert result is not None


@pytest.mark.benchmark
def test_scan_full_library_performance(
    benchmark, scan_engine: ScanEngine, test_library: Library
) -> None:
    """Benchmark full library scanning."""
    thresholds = perf_thresholds()
    
    # Mock external operations to focus on scanning performance
    with patch.object(scan_engine, '_process_file') as mock_process:
        mock_process.return_value = Mock()
        
        # Time the full scan
        result = benchmark(
            scan_engine.scan_library,
            test_library.id
        )
    
    assert result is not None


@pytest.mark.benchmark
def test_scan_large_directory_performance(
    benchmark, scan_engine: ScanEngine, tmp_path: Path
) -> None:
    """Test scanning performance with large directory structures."""
    # Create a larger directory structure
    large_dir = tmp_path / "large_library"
    large_dir.mkdir()
    
    # Create 1000 files in nested directories
    for i in range(100):
        subdir = large_dir / f"subdir_{i:03d}"
        subdir.mkdir()
        
        for j in range(10):
            file_path = subdir / f"file_{j:03d}.mp4"
            file_path.write_bytes(b"content" * 100)
    
    # Benchmark discovery of large directory
    with patch.object(scan_engine, '_process_file'):
        discovered = benchmark(
            scan_engine._discover_files,
            large_dir
        )
    
    assert len(discovered) == 1000


@pytest.mark.benchmark
def test_scan_with_filters_performance(
    benchmark, scan_engine: ScanEngine, temp_media_library: Path
) -> None:
    """Benchmark scanning with file filters."""
    # Test with video file filter
    video_extensions = {'.mp4', '.mkv', '.avi', '.mov'}
    
    def filtered_discovery():
        all_files = scan_engine._discover_files(temp_media_library)
        return [
            f for f in all_files 
            if f.suffix.lower() in video_extensions
        ]
    
    with patch.object(scan_engine, '_process_file'):
        filtered_files = benchmark(filtered_discovery)
    
    # All our test files should be video files
    expected_files = 100 + (10 * 3 * 10)
    assert len(filtered_files) == expected_files


@pytest.mark.benchmark
def test_scan_metadata_extraction_performance(
    benchmark, scan_engine: ScanEngine, tmp_path: Path
) -> None:
    """Benchmark metadata extraction from files."""
    # Create test files with different sizes
    test_files = []
    for size in [1000, 10000, 100000, 1000000]:  # Different file sizes
        test_file = tmp_path / f"test_{size}.mp4"
        test_file.write_bytes(b"x" * size)
        test_files.append(test_file)
    
    # Benchmark metadata extraction
    def extract_metadata():
        results = []
        for test_file in test_files:
            with patch('media_manager.scan_engine.os.path.getsize') as mock_size:
                mock_size.return_value = size
                metadata = scan_engine._extract_file_metadata(test_file)
                results.append(metadata)
        return results
    
    metadata_results = benchmark(extract_metadata)
    assert len(metadata_results) == len(test_files)


# Performance regression tests
@pytest.mark.benchmark
def test_scan_performance_regression(
    benchmark, scan_engine: ScanEngine, test_library: Library
) -> None:
    """Test scanning performance doesn't regress."""
    thresholds = perf_thresholds()
    
    # Mock processing to focus on discovery
    with patch.object(scan_engine, '_process_file') as mock_process:
        mock_process.return_value = Mock()
        
        result = benchmark.pedantic(
            scan_engine.scan_library,
            args=(test_library.id,),
            iterations=3,
            warmup_rounds=1,
        )
        
        # Calculate time per discovered file
        # This is a rough estimate since we're mocking
        estimated_files = 400  # Approximate number of files
        time_per_file = result.min / estimated_files
        
        assert time_per_file < thresholds["scan_max_time_per_item"], (
            f"Scan performance regression: {time_per_file:.4f}s per file > "
            f"{thresholds['scan_max_time_per_item']}s per file"
        )


@pytest.mark.benchmark
def test_discovery_performance_regression(
    benchmark, scan_engine: ScanEngine, temp_media_library: Path
) -> None:
    """Test file discovery performance doesn't regress."""
    thresholds = perf_thresholds()
    
    with patch.object(scan_engine, '_process_file'):
        result = benchmark.pedantic(
            scan_engine._discover_files,
            args=(temp_media_library,),
            iterations=5,
            warmup_rounds=2,
        )
        
        # Calculate time per discovered file
        expected_files = 400  # 100 movies + 300 episodes
        time_per_file = result.min / expected_files
        
        assert time_per_file < thresholds["scan_max_time_per_item"], (
            f"Discovery performance regression: {time_per_file:.4f}s per file > "
            f"{thresholds['scan_max_time_per_item']}s per file"
        )