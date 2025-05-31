import io
import sys
import unittest
from unittest.mock import patch

from cli import handle_add, handle_delete, handle_list, handle_view
from vault.errors import DuplicateTitleError, NoteNotFoundError, StorageError


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

    def test_handle_view_success(self):
        """Test handle_view with successful note retrieval."""
        self.args.title = "Test Note"
        mock_note = type("Note", (), {"content": "Test content"})()

        with (
            patch("vault.core.get_note_by_title", return_value=mock_note),
            patch("sys.stdout", new=io.StringIO()) as mock_stdout,
        ):
            handle_view(self.args)
            self.assertEqual(mock_stdout.getvalue().strip(), "Test content")

    def test_handle_view_not_found(self):
        """Test handle_view with note not found error."""
        self.args.title = "Test Note"

        with (
            patch("vault.core.get_note_by_title") as mock_get,
            patch("sys.exit") as mock_exit,
        ):
            mock_get.side_effect = NoteNotFoundError("Test Note")
            handle_view(self.args)
            mock_exit.assert_called_once_with(1)

    def test_handle_view_storage_error(self):
        """Test handle_view with storage error."""
        self.args.title = "Test Note"

        with (
            patch("vault.core.get_note_by_title") as mock_get,
            patch("sys.exit") as mock_exit,
        ):
            mock_get.side_effect = StorageError("Test error")
            handle_view(self.args)
            mock_exit.assert_called_once_with(1)

    def test_handle_list_success(self):
        """Test handle_list with successful note retrieval."""
        with (
            patch("vault.core.get_all_titles", return_value=["Note 1", "Note 2"]),
            patch("sys.stdout", new=io.StringIO()) as mock_stdout,
        ):
            handle_list(self.args)
            expected_output = "\nNotes:\n- Note 1\n- Note 2"
            self.assertEqual(mock_stdout.getvalue().strip(), expected_output.strip())

    def test_handle_list_empty(self):
        """Test handle_list with no notes."""
        with (
            patch("vault.core.get_all_titles", return_value=[]),
            patch("sys.stdout", new=io.StringIO()) as mock_stdout,
        ):
            handle_list(self.args)
            self.assertEqual(mock_stdout.getvalue().strip(), "No notes found.")

    def test_handle_list_storage_error(self):
        """Test handle_list with storage error."""
        with (
            patch("vault.core.get_all_titles") as mock_get,
            patch("sys.exit") as mock_exit,
        ):
            mock_get.side_effect = StorageError("Test error")
            handle_list(self.args)
            mock_exit.assert_called_once_with(1)

    def test_handle_delete_success(self):
        """Test handle_delete with successful note deletion."""
        self.args.title = "Test Note"

        with (
            patch("vault.core.delete_note_by_title") as mock_delete,
            patch("sys.stdout", new=io.StringIO()) as mock_stdout,
        ):
            handle_delete(self.args)
            mock_delete.assert_called_once_with("Test Note")
            self.assertEqual(
                mock_stdout.getvalue().strip(), "Note 'Test Note' deleted successfully!"
            )

    def test_handle_delete_not_found(self):
        """Test handle_delete with note not found error."""
        self.args.title = "Test Note"

        with (
            patch("vault.core.delete_note_by_title") as mock_delete,
            patch("sys.exit") as mock_exit,
        ):
            mock_delete.side_effect = NoteNotFoundError("Test Note")
            handle_delete(self.args)
            mock_exit.assert_called_once_with(1)

    def test_handle_delete_storage_error(self):
        """Test handle_delete with storage error."""
        self.args.title = "Test Note"

        with (
            patch("vault.core.delete_note_by_title") as mock_delete,
            patch("sys.exit") as mock_exit,
        ):
            mock_delete.side_effect = StorageError("Test error")
            handle_delete(self.args)
            mock_exit.assert_called_once_with(1)


if __name__ == "__main__":
    unittest.main()
