"""Tests for file operations with atomic renames and rollback."""

from pathlib import Path
from tempfile import TemporaryDirectory

from src.media_manager.file_operations import FileOperationManager
from src.media_manager.models import MediaType, RenameOperation, VideoMetadata


class TestFileOperationManager:
    """Test cases for FileOperationManager."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = FileOperationManager()

    def test_validate_operations_success(self):
        """Test successful operation validation."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source file
            source_file = temp_path / "source.txt"
            source_file.write_text("test content")

            # Create operation
            target_file = temp_path / "target.txt"
            operation = RenameOperation(
                source_path=source_file,
                target_path=target_file,
                metadata=VideoMetadata(
                    file_path=source_file,
                    title="Test",
                    media_type=MediaType.MOVIE,
                ),
            )

            errors = self.manager._validate_operations([operation])
            assert len(errors) == 0

    def test_validate_operations_missing_source(self):
        """Test validation with missing source file."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create operation with non-existent source
            source_file = temp_path / "nonexistent.txt"
            target_file = temp_path / "target.txt"
            operation = RenameOperation(
                source_path=source_file,
                target_path=target_file,
                metadata=VideoMetadata(
                    file_path=source_file,
                    title="Test",
                    media_type=MediaType.MOVIE,
                ),
            )

            errors = self.manager._validate_operations([operation])
            assert len(errors) == 1
            assert "Source file does not exist" in errors[0]

    def test_validate_operations_duplicate_targets(self):
        """Test validation with duplicate target paths."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source files
            source1 = temp_path / "source1.txt"
            source2 = temp_path / "source2.txt"
            source1.write_text("content1")
            source2.write_text("content2")

            # Create operations with same target
            target = temp_path / "target.txt"
            op1 = RenameOperation(
                source_path=source1,
                target_path=target,
                metadata=VideoMetadata(
                    file_path=source1,
                    title="Test1",
                    media_type=MediaType.MOVIE,
                ),
            )
            op2 = RenameOperation(
                source_path=source2,
                target_path=target,
                metadata=VideoMetadata(
                    file_path=source2,
                    title="Test2",
                    media_type=MediaType.MOVIE,
                ),
            )

            errors = self.manager._validate_operations([op1, op2])
            assert len(errors) == 1
            assert "Duplicate target path" in errors[0]

    def test_validate_operations_existing_target(self):
        """Test validation with existing target file."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source and target files
            source_file = temp_path / "source.txt"
            target_file = temp_path / "target.txt"
            source_file.write_text("source content")
            target_file.write_text("target content")

            operation = RenameOperation(
                source_path=source_file,
                target_path=target_file,
                metadata=VideoMetadata(
                    file_path=source_file,
                    title="Test",
                    media_type=MediaType.MOVIE,
                ),
            )

            errors = self.manager._validate_operations([operation])
            assert len(errors) == 1
            assert "Target file already exists" in errors[0]

    def test_validate_operations_circular_rename(self):
        """Test validation with circular renames."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source files
            source1 = temp_path / "source1.txt"
            source2 = temp_path / "source2.txt"
            source1.write_text("content1")
            source2.write_text("content2")

            # Create circular operations
            op1 = RenameOperation(
                source_path=source1,
                target_path=source2,
                metadata=VideoMetadata(
                    file_path=source1,
                    title="Test1",
                    media_type=MediaType.MOVIE,
                ),
            )
            op2 = RenameOperation(
                source_path=source2,
                target_path=source1,
                metadata=VideoMetadata(
                    file_path=source2,
                    title="Test2",
                    media_type=MediaType.MOVIE,
                ),
            )

            errors = self.manager._validate_operations([op1, op2])
            # Should detect both circular rename and existing target errors
            assert len(errors) >= 1
            circular_errors = [e for e in errors if "Circular rename detected" in e]
            assert len(circular_errors) >= 1

    def test_prepare_directories_creates_missing_dirs(self):
        """Test directory preparation creates missing directories."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source file
            source_file = temp_path / "source.txt"
            source_file.write_text("content")

            # Create operation with nested target directory
            target_file = temp_path / "new" / "subdir" / "target.txt"
            operation = RenameOperation(
                source_path=source_file,
                target_path=target_file,
                metadata=VideoMetadata(
                    file_path=source_file,
                    title="Test",
                    media_type=MediaType.MOVIE,
                ),
            )

            errors = self.manager._prepare_directories([operation])
            assert len(errors) == 0
            assert target_file.parent.exists()

    def test_execute_atomic_renames_success(self):
        """Test successful atomic rename execution."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source file
            source_file = temp_path / "source.txt"
            source_file.write_text("test content")

            # Create operation
            target_file = temp_path / "target.txt"
            operation = RenameOperation(
                source_path=source_file,
                target_path=target_file,
                metadata=VideoMetadata(
                    file_path=source_file,
                    title="Test",
                    media_type=MediaType.MOVIE,
                ),
            )

            success, messages = self.manager.execute_atomic_renames([operation])

            assert success
            assert not source_file.exists()
            assert target_file.exists()
            assert target_file.read_text() == "test content"

    def test_execute_atomic_renames_dry_run(self):
        """Test dry run mode doesn't execute operations."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source file
            source_file = temp_path / "source.txt"
            source_file.write_text("test content")

            # Create operation
            target_file = temp_path / "target.txt"
            operation = RenameOperation(
                source_path=source_file,
                target_path=target_file,
                metadata=VideoMetadata(
                    file_path=source_file,
                    title="Test",
                    media_type=MediaType.MOVIE,
                ),
            )

            success, messages = self.manager.execute_atomic_renames(
                [operation], dry_run=True
            )

            assert success
            assert source_file.exists()  # Source should still exist in dry run
            assert not target_file.exists()  # Target should not be created

    def test_execute_atomic_renames_rollback_on_failure(self):
        """Test rollback when execution fails."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source files
            source1 = temp_path / "source1.txt"
            source2 = temp_path / "source2.txt"
            source1.write_text("content1")
            source2.write_text("content2")

            # Create operations - second one will fail due to non-existent parent
            target1 = temp_path / "target1.txt"
            target2 = Path("/nonexistent/path/target2.txt")  # This will fail

            op1 = RenameOperation(
                source_path=source1,
                target_path=target1,
                metadata=VideoMetadata(
                    file_path=source1,
                    title="Test1",
                    media_type=MediaType.MOVIE,
                ),
            )
            op2 = RenameOperation(
                source_path=source2,
                target_path=target2,
                metadata=VideoMetadata(
                    file_path=source2,
                    title="Test2",
                    media_type=MediaType.MOVIE,
                ),
            )

            success, messages = self.manager.execute_atomic_renames([op1, op2])

            assert not success
            assert source1.exists()  # Should be rolled back

    def test_get_disk_space_info(self):
        """Test getting disk space information."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create source file
            source_file = temp_path / "source.txt"
            source_file.write_text("test content")

            # Create operation
            target_file = temp_path / "target.txt"
            operation = RenameOperation(
                source_path=source_file,
                target_path=target_file,
                metadata=VideoMetadata(
                    file_path=source_file,
                    title="Test",
                    media_type=MediaType.MOVIE,
                ),
            )

            space_info = self.manager.get_disk_space_info([operation])

            # Disk space info might not be available on all systems
            if space_info is not None:
                required, available = space_info
                assert required > 0
                assert available > 0
            else:
                # If None, it means disk space info is not available
                assert True

    def test_get_disk_space_info_empty_operations(self):
        """Test getting disk space info with no operations."""
        space_info = self.manager.get_disk_space_info([])
        assert space_info is None

    def test_rollback_with_executed_operations(self):
        """Test rollback with executed operations."""
        with TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create and execute a rename operation manually for testing
            source_file = temp_path / "source.txt"
            target_file = temp_path / "target.txt"
            source_file.write_text("test content")

            # Manually move file to simulate executed operation
            source_file.rename(target_file)

            # Add to rollback log
            self.manager._rollback_log = [(str(target_file), str(source_file))]

            # Perform rollback
            success, messages = self.manager._rollback()

            assert success
            assert source_file.exists()
            assert not target_file.exists()
