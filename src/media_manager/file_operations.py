"""File operations module for atomic renames with rollback support."""

import shutil
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .logging import get_logger
from .models import RenameOperation


class FileOperationManager:
    """Manager for file operations with atomic execution and rollback."""

    def __init__(self) -> None:
        self._logger = get_logger().get_logger(__name__)
        self._rollback_log: List[Tuple[str, str]] = []  # (source, target)

    def execute_atomic_renames(
        self, operations: List[RenameOperation], dry_run: bool = False
    ) -> Tuple[bool, List[str]]:
        """Execute rename operations atomically with rollback on failure.

        Args:
            operations: List of RenameOperation objects to execute
            dry_run: If True, only validate without executing

        Returns:
            Tuple of (success: bool, messages: List[str])
        """
        if not operations:
            return True, ["No operations to execute"]

        messages = []
        self._rollback_log.clear()

        try:
            # Phase 1: Validation
            validation_errors = self._validate_operations(operations)
            if validation_errors:
                return False, validation_errors

            if dry_run:
                return True, [
                    f"Dry run: {len(operations)} operations validated successfully"
                ]

            # Phase 2: Prepare parent directories
            dir_creation_errors = self._prepare_directories(operations)
            if dir_creation_errors:
                return False, dir_creation_errors

            # Phase 3: Execute operations with temporary staging
            success, exec_messages = self._execute_with_staging(operations)
            messages.extend(exec_messages)

            if success:
                messages.append(
                    f"Successfully executed {len(operations)} rename operations"
                )
                return True, messages
            else:
                # Rollback on failure
                rollback_success, rollback_messages = self._rollback()
                messages.extend(rollback_messages)
                return False, messages

        except Exception as e:
            messages.append(f"Unexpected error during rename execution: {e}")
            self._logger.exception("Unexpected error during rename execution")

            # Attempt rollback
            rollback_success, rollback_messages = self._rollback()
            messages.extend(rollback_messages)

            return False, messages

    def _validate_operations(self, operations: List[RenameOperation]) -> List[str]:
        """Validate operations for potential conflicts."""
        errors = []
        target_paths: Dict[str, RenameOperation] = {}

        for i, op in enumerate(operations):
            # Check source exists
            if not op.source_path.exists():
                errors.append(f"Source file does not exist: {op.source_path}")
                continue

            # Check source is a file
            if not op.source_path.is_file():
                errors.append(f"Source is not a file: {op.source_path}")
                continue

            # Check for duplicate targets
            target_key = str(op.target_path.resolve())
            if target_key in target_paths:
                errors.append(
                    f"Duplicate target path: {op.target_path} "
                    f"(also from {target_paths[target_key].source_path})"
                )
            else:
                target_paths[target_key] = op

            # Check if target already exists
            if op.target_path.exists():
                errors.append(f"Target file already exists: {op.target_path}")

            # Check for circular renames
            for j, other_op in enumerate(operations):
                if i != j:
                    if op.source_path == other_op.target_path:
                        errors.append(
                            f"Circular rename detected: {op.source_path} -> {op.target_path} "
                            f"and {other_op.source_path} -> {other_op.target_path}"
                        )

        return errors

    def _prepare_directories(self, operations: List[RenameOperation]) -> List[str]:
        """Create parent directories for target paths."""
        errors = []
        created_dirs = []

        try:
            for op in operations:
                target_parent = op.target_path.parent

                # Only create if different from source parent
                if target_parent != op.source_path.parent:
                    if not target_parent.exists():
                        target_parent.mkdir(parents=True, exist_ok=True)
                        created_dirs.append(target_parent)
                        self._logger.debug(f"Created directory: {target_parent}")

        except OSError as e:
            errors.append(f"Failed to create directories: {e}")

            # Cleanup created directories
            for dir_path in reversed(created_dirs):
                try:
                    if dir_path.exists() and not any(dir_path.iterdir()):
                        dir_path.rmdir()
                        self._logger.debug(f"Cleaned up directory: {dir_path}")
                except OSError:
                    pass

        return errors

    def _execute_with_staging(
        self, operations: List[RenameOperation]
    ) -> Tuple[bool, List[str]]:
        """Execute operations using temporary staging area for atomicity."""
        messages = []
        staged_files: Dict[Path, Path] = {}
        executed_operations: List[RenameOperation] = []

        try:
            # Create temporary staging directory
            with tempfile.TemporaryDirectory(
                prefix="media_manager_staging_"
            ) as staging_dir:
                staging_path = Path(staging_dir)

                # Phase 1: Stage all files to temporary location
                for op in operations:
                    try:
                        # Create temporary file path
                        temp_file = (
                            staging_path
                            / f"stage_{len(staged_files)}{op.source_path.suffix}"
                        )

                        # Copy to staging
                        shutil.copy2(op.source_path, temp_file)
                        staged_files[op.source_path] = temp_file

                        self._logger.debug(f"Staged {op.source_path} to {temp_file}")

                    except OSError as e:
                        messages.append(f"Failed to stage {op.source_path}: {e}")
                        return False, messages

                # Phase 2: Move from staging to final targets
                for op in operations:
                    try:
                        temp_file = staged_files[op.source_path]

                        # Move from staging to target
                        shutil.move(str(temp_file), str(op.target_path))

                        # Remove original source file
                        op.source_path.unlink()

                        # Record for rollback
                        self._rollback_log.append(
                            (str(op.target_path), str(op.source_path))
                        )
                        executed_operations.append(op)
                        op.executed = True

                        self._logger.info(
                            f"Renamed {op.source_path} -> {op.target_path}"
                        )
                        messages.append(
                            f"Renamed: {op.source_path.name} -> {op.target_path.name}"
                        )

                    except OSError as e:
                        messages.append(
                            f"Failed to move {op.source_path} to {op.target_path}: {e}"
                        )
                        return False, messages

            return True, messages

        except Exception as e:
            messages.append(f"Staging operation failed: {e}")
            return False, messages

    def _rollback(self) -> Tuple[bool, List[str]]:
        """Rollback all executed operations."""
        messages = []
        success = True

        self._logger.warning(f"Rolling back {len(self._rollback_log)} operations")

        # Rollback in reverse order
        for target_path, source_path in reversed(self._rollback_log):
            try:
                target = Path(target_path)
                source = Path(source_path)

                if target.exists():
                    # Move back to original location
                    shutil.move(str(target), str(source))
                    self._logger.info(f"Rolled back: {target} -> {source}")
                    messages.append(f"Rolled back: {target.name} -> {source.name}")

            except OSError as e:
                success = False
                self._logger.error(f"Failed to rollback {target_path}: {e}")
                messages.append(f"Failed to rollback {target_path}: {e}")

        if success:
            messages.append("Rollback completed successfully")
        else:
            messages.append("Rollback completed with errors")

        return success, messages

    def get_disk_space_info(
        self, operations: List[RenameOperation]
    ) -> Optional[Tuple[int, int]]:
        """Get disk space information for operations.

        Returns:
            Tuple of (required_bytes, available_bytes) or None if unavailable
        """
        if not operations:
            return None

        try:
            # Calculate total size of files to be moved
            total_size = 0
            for op in operations:
                if op.source_path.exists():
                    total_size += op.source_path.stat().st_size

            # Get available space on target filesystem
            if operations:
                target_path = operations[0].target_path.parent
                try:
                    stat = target_path.statvfs()
                    available_space = stat.f_bavail * stat.f_frsize
                except (AttributeError, OSError):
                    # statvfs not available (e.g., on Windows), skip space check
                    return None

                return total_size, available_space

        except (OSError, AttributeError):
            pass

        return None
