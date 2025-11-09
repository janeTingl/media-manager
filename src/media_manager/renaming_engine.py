"""Renaming engine with template rendering and atomic operations."""

import re
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .logging import get_logger
from .models import RenameOperation, VideoMetadata


class RenamingEngine:
    """Engine for renaming files using configurable templates."""

    def __init__(self) -> None:
        self._logger = get_logger().get_logger(__name__)

    def render_template(
        self, template: str, metadata: VideoMetadata, base_dir: Optional[Path] = None
    ) -> Path:
        """Render a template string with metadata to produce a target path.

        Args:
            template: Template string with placeholders like {title}, {year}, etc.
            metadata: VideoMetadata object containing file information
            base_dir: Base directory for relative paths (optional)

        Returns:
            Rendered Path object

        Raises:
            ValueError: If template contains invalid placeholders
        """
        try:
            # Get metadata dictionary for template rendering
            context = metadata.to_dict()

            # Add formatted season/episode for TV shows
            if metadata.season is not None:
                context["season02"] = f"{metadata.season:02d}"
            if metadata.episode is not None:
                context["episode02"] = f"{metadata.episode:02d}"
                if metadata.season is not None:
                    context["s00e00"] = f"S{metadata.season:02d}E{metadata.episode:02d}"
                    context["sxee"] = f"{metadata.season}x{metadata.episode}"

            # Render template
            rendered = template.format(**context)

            # Clean up the rendered path
            rendered = self._clean_path(rendered)

            # Create Path object
            target_path = Path(rendered)

            # If base_dir is provided, make it relative to that
            if base_dir and not target_path.is_absolute():
                target_path = base_dir / target_path

            return target_path

        except KeyError as e:
            raise ValueError(f"Invalid placeholder in template: {e}") from e
        except (ValueError, TypeError) as e:
            raise ValueError(f"Error rendering template: {e}") from e

    def _clean_path(self, path_str: str) -> str:
        """Clean up path string by removing invalid characters."""
        # Split path into segments to clean each part individually
        segments = path_str.split("/")
        cleaned_segments = []

        for i, segment in enumerate(segments):
            if not segment:  # Skip empty segments
                continue

            # For the last segment (filename), preserve the extension
            if i == len(segments) - 1 and "." in segment:
                name_part, ext = segment.rsplit(".", 1)
                # Clean the name part
                invalid_chars = r'[<>:"\\|?*]'
                cleaned_name = re.sub(invalid_chars, "_", name_part)
                cleaned_name = re.sub(r"_+", "_", cleaned_name)
                cleaned_name = cleaned_name.strip("_.")
                # Reconstruct with extension
                cleaned = f"{cleaned_name}.{ext}" if cleaned_name else f".{ext}"
            else:
                # Replace invalid characters with underscores (but not path separators)
                invalid_chars = r'[<>:"\\|?*]'
                cleaned = re.sub(invalid_chars, "_", segment)

                # Remove multiple consecutive underscores
                cleaned = re.sub(r"_+", "_", cleaned)

                # Remove leading/trailing underscores and dots
                cleaned = cleaned.strip("_.")

            if cleaned:  # Only add non-empty segments
                cleaned_segments.append(cleaned)

        return "/".join(cleaned_segments)

    def preview_renames(
        self,
        items: List[VideoMetadata],
        movie_template: str,
        tv_template: str,
        base_dir: Optional[Path] = None,
    ) -> List[RenameOperation]:
        """Preview rename operations for a list of media items.

        Args:
            items: List of VideoMetadata objects
            movie_template: Template for movies
            tv_template: Template for TV episodes
            base_dir: Base directory for target paths

        Returns:
            List of RenameOperation objects
        """
        operations = []

        for item in items:
            # Select appropriate template
            if item.media_type.value == "movie":
                template = movie_template
            else:
                template = tv_template

            try:
                target_path = self.render_template(template, item, base_dir)

                # Ensure the target has the correct extension
                if not target_path.suffix:
                    target_path = target_path.with_suffix(item.extension)

                operation = RenameOperation(item.file_path, target_path, item)
                operations.append(operation)

            except ValueError as e:
                self._logger.warning(
                    f"Failed to render template for {item.file_path}: {e}"
                )
                continue

        return operations

    def execute_renames(
        self, operations: List[RenameOperation], dry_run: bool = False
    ) -> Tuple[bool, List[str]]:
        """Execute rename operations atomically with rollback on failure.

        Args:
            operations: List of RenameOperation objects
            dry_run: If True, only validate operations without executing

        Returns:
            Tuple of (success: bool, messages: List[str])
        """
        if not operations:
            return True, ["No operations to execute"]

        messages = []
        executed_operations = []

        try:
            # Validate operations first
            validation_errors = self._validate_operations(operations)
            if validation_errors:
                return False, validation_errors

            if dry_run:
                return True, [
                    f"Dry run: {len(operations)} operations would be executed"
                ]

            # Create parent directories if needed
            for op in operations:
                if op.target_path.parent != op.source_path.parent:
                    op.target_path.parent.mkdir(parents=True, exist_ok=True)
                    messages.append(f"Created directory: {op.target_path.parent}")

            # Execute operations
            for op in operations:
                try:
                    # Check if target already exists
                    if op.target_path.exists():
                        raise FileExistsError(
                            f"Target file already exists: {op.target_path}"
                        )

                    # Perform the rename
                    shutil.move(str(op.source_path), str(op.target_path))
                    op.executed = True
                    executed_operations.append(op)
                    messages.append(
                        f"Renamed: {op.source_path.name} -> {op.target_path.name}"
                    )

                except (OSError, FileExistsError) as e:
                    messages.append(f"Failed to rename {op.source_path}: {e}")
                    # Rollback executed operations
                    self._rollback_operations(executed_operations)
                    return False, messages

            return True, messages

        except Exception as e:
            messages.append(f"Unexpected error: {e}")
            # Rollback executed operations
            self._rollback_operations(executed_operations)
            return False, messages

    def _validate_operations(self, operations: List[RenameOperation]) -> List[str]:
        """Validate rename operations for potential conflicts."""
        errors = []
        target_paths: Dict[str, RenameOperation] = {}

        for i, op in enumerate(operations):
            # Check if source exists
            if not op.source_path.exists():
                errors.append(f"Source file does not exist: {op.source_path}")
                continue

            # Check for duplicate target paths
            target_key = str(op.target_path.resolve())
            if target_key in target_paths:
                errors.append(
                    f"Duplicate target path: {op.target_path} "
                    f"(also from {target_paths[target_key].source_path})"
                )
            else:
                target_paths[target_key] = op

            # Check for circular rename (A -> B, B -> A)
            for j, other_op in enumerate(operations):
                if i != j and op.source_path == other_op.target_path:
                    errors.append(
                        f"Circular rename detected: {op.source_path} -> {op.target_path} "
                        f"and {other_op.source_path} -> {other_op.target_path}"
                    )

        return errors

    def _rollback_operations(self, operations: List[RenameOperation]) -> None:
        """Rollback executed operations."""
        self._logger.warning(f"Rolling back {len(operations)} operations")

        # Rollback in reverse order
        for op in reversed(operations):
            if op.executed and op.target_path.exists():
                try:
                    shutil.move(str(op.target_path), str(op.source_path))
                    self._logger.info(
                        f"Rolled back: {op.target_path} -> {op.source_path}"
                    )
                except OSError as e:
                    self._logger.error(f"Failed to rollback {op.target_path}: {e}")

    def get_default_templates(self) -> Dict[str, str]:
        """Get default renaming templates."""
        return {
            "movie": "Movies/{title} ({year})/{title} ({year}){extension}",
            "tv_episode": "TV/{title}/Season {season02}/{title} - {s00e00}{extension}",
        }
