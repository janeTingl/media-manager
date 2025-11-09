"""NFO metadata exporter for movies and TV episodes."""

from __future__ import annotations

from pathlib import Path
from xml.etree import ElementTree as ET

from media_manager.models import MediaMatch


class NFOExporter:
    """Export media metadata to NFO (XML) files."""

    def __init__(self) -> None:
        """Initialize the NFO exporter."""
        pass

    def export_nfo(
        self,
        media_match: MediaMatch,
        output_path: Path | None = None,
        target_subfolder: str | None = None,
    ) -> Path:
        """
        Export media match metadata to an NFO file.

        Args:
            media_match: The media match containing metadata
            output_path: Optional path to export to (defaults to media file location)
            target_subfolder: Optional subfolder within the media directory

        Returns:
            The path to the generated NFO file

        Raises:
            ValueError: If media match has no matched data
            OSError: If NFO file cannot be written
        """
        if not media_match.is_matched():
            raise ValueError("Cannot export NFO for unmatched media")

        # Determine output path
        if output_path is None:
            output_path = media_match.metadata.path.parent

        if target_subfolder:
            output_path = output_path / target_subfolder
            output_path.mkdir(parents=True, exist_ok=True)

        # Generate NFO filename
        nfo_filename = media_match.metadata.path.stem + ".nfo"
        nfo_file = output_path / nfo_filename

        # Generate appropriate XML based on media type
        if media_match.metadata.is_movie():
            root = self._generate_movie_nfo(media_match)
        else:
            root = self._generate_episode_nfo(media_match)

        # Write to file with UTF-8 encoding
        tree = ET.ElementTree(root)
        tree.write(
            nfo_file,
            encoding="utf-8",
            xml_declaration=True,
        )

        return nfo_file

    def _generate_movie_nfo(self, media_match: MediaMatch) -> ET.Element:
        """Generate XML root element for a movie NFO file."""
        root = ET.Element("movie")

        # Basic information
        self._add_element(root, "title", media_match.matched_title or "")
        self._add_element(root, "originaltitle", media_match.matched_title or "")

        if media_match.matched_year:
            self._add_element(root, "year", str(media_match.matched_year))

        if media_match.aired_date:
            self._add_element(root, "aired", media_match.aired_date)

        if media_match.runtime:
            self._add_element(root, "runtime", str(media_match.runtime))

        if media_match.overview:
            self._add_element(root, "plot", media_match.overview)

        # IDs
        if media_match.external_id:
            if media_match.source == "tmdb":
                self._add_element(root, "tmdbid", media_match.external_id)
            elif media_match.source == "tvdb":
                self._add_element(root, "tvdbid", media_match.external_id)
            else:
                self._add_element(root, "id", media_match.external_id)

        # Cast
        for actor in media_match.cast:
            actor_elem = ET.SubElement(root, "actor")
            self._add_element(actor_elem, "name", actor)

        return root

    def _generate_episode_nfo(self, media_match: MediaMatch) -> ET.Element:
        """Generate XML root element for an episode NFO file."""
        root = ET.Element("episodedetails")

        # Basic information
        self._add_element(root, "title", media_match.matched_title or "")

        if media_match.metadata.season is not None:
            self._add_element(root, "season", str(media_match.metadata.season))

        if media_match.metadata.episode is not None:
            self._add_element(root, "episode", str(media_match.metadata.episode))

        if media_match.aired_date:
            self._add_element(root, "aired", media_match.aired_date)

        if media_match.runtime:
            self._add_element(root, "runtime", str(media_match.runtime))

        if media_match.overview:
            self._add_element(root, "plot", media_match.overview)

        # IDs
        if media_match.external_id:
            if media_match.source == "tmdb":
                self._add_element(root, "tmdbid", media_match.external_id)
            elif media_match.source == "tvdb":
                self._add_element(root, "tvdbid", media_match.external_id)
            else:
                self._add_element(root, "id", media_match.external_id)

        # Cast
        for actor in media_match.cast:
            actor_elem = ET.SubElement(root, "actor")
            self._add_element(actor_elem, "name", actor)

        return root

    @staticmethod
    def _add_element(
        parent: ET.Element,
        tag: str,
        text: str,
    ) -> ET.Element:
        """Add a subelement with text content to a parent element."""
        elem = ET.SubElement(parent, tag)
        if text:
            elem.text = text
        return elem

    def validate_nfo(self, nfo_path: Path) -> bool:
        """
        Validate that an NFO file is valid XML.

        Args:
            nfo_path: Path to the NFO file

        Returns:
            True if valid XML, False otherwise
        """
        try:
            ET.parse(nfo_path)
            return True
        except ET.ParseError:
            return False

    def read_nfo(self, nfo_path: Path) -> dict:
        """
        Read and parse an NFO file.

        Args:
            nfo_path: Path to the NFO file

        Returns:
            Dictionary representation of the NFO data
        """
        tree = ET.parse(nfo_path)
        root = tree.getroot()
        return self._element_to_dict(root)

    @staticmethod
    def _element_to_dict(element: ET.Element) -> dict:
        """Convert an XML element to a dictionary."""
        result = {"_tag": element.tag, "_text": element.text}

        for child in element:
            child_dict = NFOExporter._element_to_dict(child)
            if child.tag in result:
                # Handle multiple children with same tag
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_dict)
            else:
                result[child.tag] = child_dict

        return result
