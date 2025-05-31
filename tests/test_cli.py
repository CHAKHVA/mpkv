"""
Tests for the MPKV CLI functionality.
"""

import io
import sys
import unittest
from unittest.mock import patch

from cli import handle_add
from vault.errors import DuplicateTitleError, StorageError


class TestCLI(unittest.TestCase):
    """Test cases for CLI functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.args = type("Args", (), {})()
        self.args.title = None
        self.args.content = None
        self.args.tags = None

    def test_handle_add_with_args(self):
        """Test handle_add with all arguments provided."""
        self.args.title = "Test Note"
        self.args.content = "Test content"
        self.args.tags = "tag1,tag2"

        with patch("vault.core.create_note") as mock_create:
            mock_create.return_value = type("Note", (), {"title": "Test Note"})()
            handle_add(self.args)
            mock_create.assert_called_once_with(
                "Test Note", "Test content", ["tag1", "tag2"]
            )

    def test_handle_add_interactive_title(self):
        """Test handle_add with interactive title input."""
        self.args.content = "Test content"
        self.args.tags = "tag1,tag2"

        with (
            patch("builtins.input", side_effect=["", "Test Note"]),
            patch("vault.core.create_note") as mock_create,
        ):
            mock_create.return_value = type("Note", (), {"title": "Test Note"})()
            handle_add(self.args)
            mock_create.assert_called_once_with(
                "Test Note", "Test content", ["tag1", "tag2"]
            )

    def test_handle_add_interactive_tags(self):
        """Test handle_add with interactive tags input."""
        self.args.title = "Test Note"
        self.args.content = "Test content"

        with (
            patch("builtins.input", return_value="tag1,tag2"),
            patch("vault.core.create_note") as mock_create,
        ):
            mock_create.return_value = type("Note", (), {"title": "Test Note"})()
            handle_add(self.args)
            mock_create.assert_called_once_with(
                "Test Note", "Test content", ["tag1", "tag2"]
            )

    def test_handle_add_interactive_content(self):
        """Test handle_add with interactive content input."""
        self.args.title = "Test Note"
        self.args.tags = "tag1,tag2"

        with (
            patch("builtins.input", side_effect=["Line 1", "Line 2", ""]),
            patch("vault.core.create_note") as mock_create,
        ):
            mock_create.return_value = type("Note", (), {"title": "Test Note"})()
            handle_add(self.args)
            mock_create.assert_called_once_with(
                "Test Note", "Line 1\nLine 2", ["tag1", "tag2"]
            )

    def test_handle_add_duplicate_title(self):
        """Test handle_add with duplicate title error."""
        self.args.title = "Test Note"
        self.args.content = "Test content"

        with (
            patch("vault.core.create_note") as mock_create,
            patch("sys.exit") as mock_exit,
        ):
            mock_create.side_effect = DuplicateTitleError("Test Note")
            handle_add(self.args)
            mock_exit.assert_called_once_with(1)

    def test_handle_add_storage_error(self):
        """Test handle_add with storage error."""
        self.args.title = "Test Note"
        self.args.content = "Test content"

        with (
            patch("vault.core.create_note") as mock_create,
            patch("sys.exit") as mock_exit,
        ):
            mock_create.side_effect = StorageError("Test error")
            handle_add(self.args)
            mock_exit.assert_called_once_with(1)

    def test_handle_add_value_error(self):
        """Test handle_add with value error."""
        self.args.title = "Test Note"
        self.args.content = "Test content"

        with (
            patch("vault.core.create_note") as mock_create,
            patch("sys.exit") as mock_exit,
        ):
            mock_create.side_effect = ValueError("Invalid data")
            handle_add(self.args)
            mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
