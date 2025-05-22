import json
import os
import os.path
import unittest
import uuid
from unittest.mock import mock_open, patch

from vault.core import (
    NOTES_SUBDIR_NAME,
    VAULT_DIR_NAME,
    _get_note_file_path,
    ensure_vault_dirs_exist,
    generate_note_id,
    get_vault_path,
    load_index,
    read_note_content,
    save_index,
    write_note_content,
)
from vault.errors import NoteNotFoundError, StorageError


class TestVaultSetup(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.home_dir = "/home/testuser"
        self.expected_vault_path = os.path.join(self.home_dir, VAULT_DIR_NAME)
        self.expected_notes_path = os.path.join(
            self.expected_vault_path, NOTES_SUBDIR_NAME
        )

    @patch("os.path.expanduser")
    def test_get_vault_path_default(self, mock_expanduser):
        """Test get_vault_path with default (no custom path)."""
        mock_expanduser.return_value = self.home_dir
        result = get_vault_path()
        self.assertEqual(result, self.expected_vault_path)
        mock_expanduser.assert_called_once_with("~")

    @patch("os.path.expanduser")
    def test_get_vault_path_custom(self, mock_expanduser):
        """Test get_vault_path with custom path."""
        custom_path = "/custom/path"
        mock_expanduser.return_value = custom_path
        result = get_vault_path(custom_path)
        self.assertEqual(result, os.path.abspath(custom_path))
        mock_expanduser.assert_called_once_with(custom_path)

    @patch("os.path.expanduser")
    @patch("os.makedirs")
    def test_ensure_vault_dirs_exist_success(self, mock_makedirs, mock_expanduser):
        """Test successful creation of vault directories."""
        mock_expanduser.return_value = self.home_dir
        result = ensure_vault_dirs_exist()

        # Check return values
        self.assertEqual(result, (self.expected_vault_path, self.expected_notes_path))

        # Verify makedirs calls
        mock_makedirs.assert_any_call(self.expected_vault_path, exist_ok=True)
        mock_makedirs.assert_any_call(self.expected_notes_path, exist_ok=True)
        self.assertEqual(mock_makedirs.call_count, 2)

    @patch("os.path.expanduser")
    @patch("os.makedirs")
    def test_ensure_vault_dirs_exist_with_custom_path(
        self, mock_makedirs, mock_expanduser
    ):
        """Test directory creation with custom path."""
        custom_path = "/custom/path"
        mock_expanduser.return_value = custom_path
        expected_vault = os.path.abspath(custom_path)
        expected_notes = os.path.join(expected_vault, NOTES_SUBDIR_NAME)

        result = ensure_vault_dirs_exist(custom_path)

        # Check return values
        self.assertEqual(result, (expected_vault, expected_notes))

        # Verify makedirs calls
        mock_makedirs.assert_any_call(expected_vault, exist_ok=True)
        mock_makedirs.assert_any_call(expected_notes, exist_ok=True)
        self.assertEqual(mock_makedirs.call_count, 2)

    @patch("os.path.expanduser")
    @patch("os.makedirs")
    def test_ensure_vault_dirs_exist_oserror(self, mock_makedirs, mock_expanduser):
        """Test handling of OSError during directory creation."""
        mock_expanduser.return_value = self.home_dir
        mock_makedirs.side_effect = OSError("Permission denied")

        with self.assertRaises(OSError) as context:
            ensure_vault_dirs_exist()

        self.assertEqual(str(context.exception), "Permission denied")
        mock_makedirs.assert_called_once_with(self.expected_vault_path, exist_ok=True)


class TestVaultIndex(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.home_dir = "/home/testuser"
        self.vault_path = os.path.join(self.home_dir, VAULT_DIR_NAME)
        self.index_path = os.path.join(self.vault_path, "index.json")
        self.sample_index = {
            "notes": {"note1": {"title": "Test Note", "tags": ["test", "example"]}}
        }

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_load_index_valid(self, mock_json_load, mock_file):
        """Test loading a valid index file."""
        mock_json_load.return_value = self.sample_index
        result = load_index()

        # Verify file was opened correctly
        mock_file.assert_called_once_with(self.index_path, "r", encoding="utf-8")
        mock_json_load.assert_called_once()
        self.assertEqual(result, self.sample_index)

    @patch("builtins.open", new_callable=mock_open)
    def test_load_index_file_not_found(self, mock_file):
        """Test loading when index file doesn't exist."""
        mock_file.side_effect = FileNotFoundError()
        result = load_index()

        # Verify empty dict is returned
        self.assertEqual(result, {})
        mock_file.assert_called_once_with(self.index_path, "r", encoding="utf-8")

    @patch("builtins.open", new_callable=mock_open)
    @patch("json.load")
    def test_load_index_invalid_json(self, mock_json_load, mock_file):
        """Test loading an invalid JSON file."""
        mock_json_load.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)

        with self.assertRaises(StorageError) as context:
            load_index()

        # Verify StorageError was raised with correct message and original error
        self.assertIn("Invalid JSON in index file", str(context.exception))
        self.assertIsInstance(context.exception.original_error, json.JSONDecodeError)
        mock_file.assert_called_once_with(self.index_path, "r", encoding="utf-8")

    @patch("vault.core.ensure_vault_dirs_exist")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_save_index_success(self, mock_json_dump, mock_file, mock_ensure_dirs):
        """Test successful index save."""
        # Setup mocks
        mock_ensure_dirs.return_value = (
            self.vault_path,
            os.path.join(self.vault_path, NOTES_SUBDIR_NAME),
        )

        # Call save_index
        save_index(self.sample_index)

        # Verify ensure_vault_dirs_exist was called
        mock_ensure_dirs.assert_called_once()

        # Verify file was opened correctly
        mock_file.assert_called_once_with(self.index_path, "w", encoding="utf-8")

        # Verify json.dump was called with correct arguments
        mock_json_dump.assert_called_once_with(self.sample_index, mock_file(), indent=4)

    @patch("vault.core.ensure_vault_dirs_exist")
    @patch("builtins.open", new_callable=mock_open)
    def test_save_index_oserror(self, mock_file, mock_ensure_dirs):
        """Test handling of OSError during index save."""
        # Setup mocks
        mock_ensure_dirs.return_value = (
            self.vault_path,
            os.path.join(self.vault_path, NOTES_SUBDIR_NAME),
        )
        mock_file.side_effect = OSError("Permission denied")

        with self.assertRaises(StorageError) as context:
            save_index(self.sample_index)

        # Verify StorageError was raised with correct message and original error
        self.assertIn("Failed to save index", str(context.exception))
        self.assertIsInstance(context.exception.original_error, OSError)

        # Verify ensure_vault_dirs_exist was called
        mock_ensure_dirs.assert_called_once()

        # Verify file open was attempted
        mock_file.assert_called_once_with(self.index_path, "w", encoding="utf-8")

    @patch("vault.core.ensure_vault_dirs_exist")
    @patch("builtins.open", new_callable=mock_open)
    @patch("json.dump")
    def test_save_index_with_custom_path(
        self, mock_json_dump, mock_file, mock_ensure_dirs
    ):
        """Test saving index with custom vault path."""
        custom_path = "/custom/path"
        expected_vault = os.path.abspath(custom_path)
        expected_index = os.path.join(expected_vault, "index.json")

        # Setup mocks
        mock_ensure_dirs.return_value = (
            expected_vault,
            os.path.join(expected_vault, NOTES_SUBDIR_NAME),
        )

        # Call save_index with custom path
        save_index(self.sample_index, custom_path)

        # Verify ensure_vault_dirs_exist was called with custom path
        mock_ensure_dirs.assert_called_once_with(custom_path)

        # Verify file was opened with correct path
        mock_file.assert_called_once_with(expected_index, "w", encoding="utf-8")

        # Verify json.dump was called with correct arguments
        mock_json_dump.assert_called_once_with(self.sample_index, mock_file(), indent=4)


class TestVaultFiles(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.home_dir = "/home/testuser"
        self.vault_path = os.path.join(self.home_dir, VAULT_DIR_NAME)
        self.notes_dir = os.path.join(self.vault_path, NOTES_SUBDIR_NAME)
        self.note_id = "123e4567-e89b-12d3-a456-426614174000"
        self.note_content = "This is a test note content"
        self.expected_note_path = os.path.join(self.notes_dir, f"{self.note_id}.txt")

    @patch("uuid.uuid4")
    def test_generate_note_id(self, mock_uuid4):
        """Test note ID generation."""
        # Setup mock
        mock_uuid = uuid.UUID(self.note_id)
        mock_uuid4.return_value = mock_uuid

        # Generate ID
        result = generate_note_id()

        # Verify result
        self.assertEqual(result, self.note_id)
        mock_uuid4.assert_called_once()

    @patch("vault.core.get_vault_subdirs")
    def test_get_note_file_path(self, mock_get_subdirs):
        """Test note file path generation."""
        # Setup mock
        mock_get_subdirs.return_value = (self.vault_path, self.notes_dir)

        # Get path
        result = _get_note_file_path(self.note_id)

        # Verify result
        self.assertEqual(result, self.expected_note_path)
        mock_get_subdirs.assert_called_once()

    @patch("vault.core.get_vault_subdirs")
    def test_get_note_file_path_with_custom_path(self, mock_get_subdirs):
        """Test note file path generation with custom vault path."""
        # Setup
        custom_path = "/custom/path"
        expected_vault = os.path.abspath(custom_path)
        expected_notes = os.path.join(expected_vault, NOTES_SUBDIR_NAME)
        expected_note_path = os.path.join(expected_notes, f"{self.note_id}.txt")
        mock_get_subdirs.return_value = (expected_vault, expected_notes)

        # Get path with custom path
        result = _get_note_file_path(self.note_id, custom_path)

        # Verify result
        self.assertEqual(result, expected_note_path)
        mock_get_subdirs.assert_called_once_with(custom_path)

    @patch("builtins.open", new_callable=mock_open, read_data="Test content")
    def test_read_note_content_success(self, mock_file):
        """Test successful note content reading."""
        result = read_note_content(self.note_id)

        # Verify result
        self.assertEqual(result, "Test content")
        mock_file.assert_called_once_with(
            self.expected_note_path, "r", encoding="utf-8"
        )

    @patch("builtins.open", new_callable=mock_open)
    def test_read_note_content_not_found(self, mock_file):
        """Test reading non-existent note."""
        mock_file.side_effect = FileNotFoundError()

        with self.assertRaises(NoteNotFoundError) as context:
            read_note_content(self.note_id)

        # Verify error
        self.assertEqual(context.exception.note_id, self.note_id)
        mock_file.assert_called_once_with(
            self.expected_note_path, "r", encoding="utf-8"
        )

    @patch("builtins.open", new_callable=mock_open)
    def test_read_note_content_oserror(self, mock_file):
        """Test handling of OSError during note reading."""
        mock_file.side_effect = OSError("Permission denied")

        with self.assertRaises(StorageError) as context:
            read_note_content(self.note_id)

        # Verify error
        self.assertIn("Failed to read note content", str(context.exception))
        self.assertIsInstance(context.exception.original_error, OSError)
        mock_file.assert_called_once_with(
            self.expected_note_path, "r", encoding="utf-8"
        )

    @patch("vault.core.ensure_vault_dirs_exist")
    @patch("builtins.open", new_callable=mock_open)
    def test_write_note_content_success(self, mock_file, mock_ensure_dirs):
        """Test successful note content writing."""
        # Setup mock
        mock_ensure_dirs.return_value = (self.vault_path, self.notes_dir)

        # Write content
        write_note_content(self.note_id, self.note_content)

        # Verify ensure_vault_dirs_exist was called
        mock_ensure_dirs.assert_called_once()

        # Verify file was opened and written correctly
        mock_file.assert_called_once_with(
            self.expected_note_path, "w", encoding="utf-8"
        )
        mock_file().write.assert_called_once_with(self.note_content)

    @patch("vault.core.ensure_vault_dirs_exist")
    @patch("builtins.open", new_callable=mock_open)
    def test_write_note_content_oserror(self, mock_file, mock_ensure_dirs):
        """Test handling of OSError during note writing."""
        # Setup mocks
        mock_ensure_dirs.return_value = (self.vault_path, self.notes_dir)
        mock_file.side_effect = OSError("Permission denied")

        with self.assertRaises(StorageError) as context:
            write_note_content(self.note_id, self.note_content)

        # Verify error
        self.assertIn("Failed to write note content", str(context.exception))
        self.assertIsInstance(context.exception.original_error, OSError)

        # Verify ensure_vault_dirs_exist was called
        mock_ensure_dirs.assert_called_once()

        # Verify file open was attempted
        mock_file.assert_called_once_with(
            self.expected_note_path, "w", encoding="utf-8"
        )

    @patch("vault.core.ensure_vault_dirs_exist")
    @patch("builtins.open", new_callable=mock_open)
    def test_write_note_content_with_custom_path(self, mock_file, mock_ensure_dirs):
        """Test writing note content with custom vault path."""
        # Setup
        custom_path = "/custom/path"
        expected_vault = os.path.abspath(custom_path)
        expected_notes = os.path.join(expected_vault, NOTES_SUBDIR_NAME)
        expected_note_path = os.path.join(expected_notes, f"{self.note_id}.txt")
        mock_ensure_dirs.return_value = (expected_vault, expected_notes)

        # Write content with custom path
        write_note_content(self.note_id, self.note_content, custom_path)

        # Verify ensure_vault_dirs_exist was called with custom path
        mock_ensure_dirs.assert_called_once_with(custom_path)

        # Verify file was opened and written correctly
        mock_file.assert_called_once_with(expected_note_path, "w", encoding="utf-8")
        mock_file().write.assert_called_once_with(self.note_content)


if __name__ == "__main__":
    unittest.main()
