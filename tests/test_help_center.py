"""Tests for the help center dialog and onboarding wizard."""

import json
import tempfile
from pathlib import Path

import pytest
from pytestqt.qtbot import QtBot

from src.media_manager.help_center_dialog import HelpCenterDialog
from src.media_manager.onboarding_wizard import OnboardingWizard
from src.media_manager.settings import SettingsManager

HELP_DOCS_LOCALE = "zh-CN"
HELP_DOCS_PATH = Path(__file__).parent.parent / "docs" / HELP_DOCS_LOCALE


class TestHelpCenterDialog:
    """Tests for the HelpCenterDialog."""

    def test_help_center_initializes(self, qtbot: QtBot) -> None:
        """Test that the help center dialog initializes successfully."""
        dialog = HelpCenterDialog()
        qtbot.addWidget(dialog)

        assert dialog.windowTitle() == "Help Center"
        assert dialog._topics_list is not None
        assert dialog._content_browser is not None

    def test_help_index_loads(self, qtbot: QtBot) -> None:
        """Test that the help index is loaded correctly."""
        dialog = HelpCenterDialog()
        qtbot.addWidget(dialog)

        # Check that topics were loaded
        assert len(dialog._topics) > 0
        assert dialog._topics_list.count() > 0

    def test_help_files_exist(self) -> None:
        """Test that all referenced help files exist."""
        docs_path = HELP_DOCS_PATH
        index_file = docs_path / "index.json"

        assert index_file.exists(), "Help index file should exist"

        with open(index_file, encoding="utf-8") as f:
            index_data = json.load(f)

        topics = index_data.get("topics", [])
        assert len(topics) > 0, "Index should contain topics"

        # Check that all referenced files exist
        for topic in topics:
            topic_file = docs_path / topic["file"]
            assert topic_file.exists(), f"Help file should exist: {topic['file']}"

    def test_help_files_have_no_broken_links(self) -> None:
        """Test that help files don't reference missing files."""
        docs_path = HELP_DOCS_PATH
        index_file = docs_path / "index.json"

        with open(index_file, encoding="utf-8") as f:
            index_data = json.load(f)

        topics = index_data.get("topics", [])
        topic_files = {topic["file"] for topic in topics}

        # Check each help file for internal links
        for topic in topics:
            topic_file = docs_path / topic["file"]

            with open(topic_file, encoding="utf-8") as f:
                content = f.read()

            # Find all local href links
            import re
            links = re.findall(r'href="([^"]+\.html)"', content)

            for link in links:
                # Skip external links
                if link.startswith("http"):
                    continue

                # Check that referenced file exists
                assert link in topic_files, f"Broken link in {topic['file']}: {link}"

    def test_zh_cn_help_locale_exists(self) -> None:
        """Ensure the Simplified Chinese help locale is present and complete."""
        docs_path = HELP_DOCS_PATH
        index_file = docs_path / "index.json"

        assert index_file.exists(), "Chinese help index should exist"

        with open(index_file, encoding="utf-8") as f:
            index_data = json.load(f)

        assert index_data.get("locale") == HELP_DOCS_LOCALE

        topics = index_data.get("topics", [])
        assert topics, "Chinese help index should list topics"

        for topic in topics:
            topic_file = docs_path / topic["file"]
            assert topic_file.exists(), f"Chinese help file should exist: {topic['file']}"

    def test_topic_navigation(self, qtbot: QtBot) -> None:
        """Test navigating between topics."""
        dialog = HelpCenterDialog()
        qtbot.addWidget(dialog)

        # Initially should show welcome topic
        assert "welcome" in dialog._history

        # Show a different topic
        dialog.show_topic("library-setup")

        # Should be in history
        assert "library-setup" in dialog._history
        assert len(dialog._history) >= 2

    def test_search_filters_topics(self, qtbot: QtBot) -> None:
        """Test that search filtering works."""
        dialog = HelpCenterDialog()
        qtbot.addWidget(dialog)

        initial_visible = sum(
            1 for i in range(dialog._topics_list.count())
            if not dialog._topics_list.item(i).isHidden()
        )

        # Search for a specific term
        dialog._search_box.setText("library")

        visible_after = sum(
            1 for i in range(dialog._topics_list.count())
            if not dialog._topics_list.item(i).isHidden()
        )

        # Should filter results
        assert visible_after <= initial_visible
        assert visible_after > 0

    def test_navigation_buttons(self, qtbot: QtBot) -> None:
        """Test back and forward navigation."""
        dialog = HelpCenterDialog()
        qtbot.addWidget(dialog)

        # Initially, back should be disabled
        assert not dialog._back_button.isEnabled()
        assert not dialog._forward_button.isEnabled()

        # Navigate to a new topic
        dialog.show_topic("library-setup")

        # Back should now be enabled
        assert dialog._back_button.isEnabled()
        assert not dialog._forward_button.isEnabled()

        # Go back
        dialog._navigate_back()

        # Forward should now be enabled
        assert dialog._forward_button.isEnabled()

    def test_context_help_initial_topic(self, qtbot: QtBot) -> None:
        """Test that initial topic can be set."""
        dialog = HelpCenterDialog(initial_topic="providers")
        qtbot.addWidget(dialog)

        # Should start with providers topic
        assert "providers" in dialog._history


class TestOnboardingWizard:
    """Tests for the OnboardingWizard."""

    def test_onboarding_wizard_initializes(self, qtbot: QtBot) -> None:
        """Test that the onboarding wizard initializes."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            wizard = OnboardingWizard(settings)
            qtbot.addWidget(wizard)

            assert wizard.windowTitle() == "Welcome to 影藏·媒体管理器"
            assert wizard.pageIds() is not None

    def test_onboarding_has_required_pages(self, qtbot: QtBot) -> None:
        """Test that onboarding wizard has all required pages."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            wizard = OnboardingWizard(settings)
            qtbot.addWidget(wizard)

            # Should have multiple pages
            page_count = len(wizard.pageIds())
            assert page_count >= 4  # Welcome, Library, Provider, Tour, Complete

    def test_onboarding_completion_saves_setting(self, qtbot: QtBot) -> None:
        """Test that completing onboarding saves the completion flag."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            # Initially should not be completed
            assert not settings.get("onboarding_completed", False)

            wizard = OnboardingWizard(settings)
            qtbot.addWidget(wizard)

            # Simulate accepting the wizard
            wizard._on_wizard_finished(wizard.DialogCode.Accepted)

            # Should now be marked as completed
            assert settings.get("onboarding_completed", False)

    def test_onboarding_skip_library_allowed(self, qtbot: QtBot) -> None:
        """Test that library setup can be skipped."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            wizard = OnboardingWizard(settings)
            qtbot.addWidget(wizard)

            # Navigate to library setup page (page 1)
            wizard.next()

            current_page = wizard.currentPage()

            # Should have skip checkbox
            skip_checkbox = getattr(current_page, "skip_checkbox", None)
            assert skip_checkbox is not None

            # Should be able to check it
            skip_checkbox.setChecked(True)
            assert skip_checkbox.isChecked()

    def test_provider_keys_can_be_entered(self, qtbot: QtBot) -> None:
        """Test that provider keys can be entered during onboarding."""
        with tempfile.TemporaryDirectory() as temp_dir:
            settings_file = Path(temp_dir) / "test_settings.json"
            settings = SettingsManager(settings_file)

            wizard = OnboardingWizard(settings)
            qtbot.addWidget(wizard)

            # Navigate to provider page
            wizard.next()  # Skip welcome
            wizard.next()  # Skip library setup

            current_page = wizard.currentPage()

            # Should have API key fields
            tmdb_edit = getattr(current_page, "tmdb_key_edit", None)
            tvdb_edit = getattr(current_page, "tvdb_edit", None)

            assert tmdb_edit is not None
            assert tvdb_edit is not None


class TestHelpIntegration:
    """Integration tests for help system."""

    def test_help_content_is_valid_html(self) -> None:
        """Test that all help content is valid HTML."""
        from html.parser import HTMLParser

        docs_path = HELP_DOCS_PATH
        index_file = docs_path / "index.json"

        with open(index_file, encoding="utf-8") as f:
            index_data = json.load(f)

        topics = index_data.get("topics", [])

        for topic in topics:
            topic_file = docs_path / topic["file"]

            with open(topic_file, encoding="utf-8") as f:
                content = f.read()

            # Try to parse as HTML - will raise exception if invalid
            parser = HTMLParser()
            try:
                parser.feed(content)
            except Exception as e:
                pytest.fail(f"Invalid HTML in {topic['file']}: {e}")

    def test_help_index_has_required_fields(self) -> None:
        """Test that help index has all required fields."""
        docs_path = HELP_DOCS_PATH
        index_file = docs_path / "index.json"

        with open(index_file, encoding="utf-8") as f:
            index_data = json.load(f)

        # Check top-level fields
        assert "title" in index_data
        assert "topics" in index_data
        assert "locale" in index_data

        # Check each topic has required fields
        topics = index_data.get("topics", [])
        for topic in topics:
            assert "id" in topic, f"Topic missing 'id': {topic}"
            assert "title" in topic, f"Topic missing 'title': {topic}"
            assert "file" in topic, f"Topic missing 'file': {topic}"
            assert "keywords" in topic, f"Topic missing 'keywords': {topic}"
            assert isinstance(topic["keywords"], list), f"Keywords should be a list: {topic}"
