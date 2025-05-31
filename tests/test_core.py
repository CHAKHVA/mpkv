import json
import os
import os.path
import shutil
import tempfile
import unittest
import uuid
from unittest.mock import mock_open, patch

import vault.core as vault
from vault.core import (
    NOTES_SUBDIR_NAME,
    VAULT_DIR_NAME,
    _create_note_internal,
    _delete_note_internal,
    _get_note_file_path,
    _get_note_internal,
    ensure_vault_dirs_exist,
    generate_note_id,
    get_all_titles,
    get_vault_path,
    load_index,
    read_note_content,
    save_index,
    write_note_content,
)
from vault.errors import NoteNotFoundError, StorageError
from vault.models import Note


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


class TestVaultPersistence(unittest.TestCase):
    def setUp(self):
        """Set up test fixtures before each test method."""
        self.home_dir = "/home/testuser"
        self.vault_path = os.path.join(self.home_dir, VAULT_DIR_NAME)
        self.notes_dir = os.path.join(self.vault_path, NOTES_SUBDIR_NAME)
        self.note_id = "123e4567-e89b-12d3-a456-426614174000"
        self.note_title = "Test Note"
        self.note_content = "This is a test note content"
        self.note_tags = ["test", "example"]
        self.note = Note(
            title=self.note_title,
            content=self.note_content,
            tags=self.note_tags,
            id=self.note_id,
        )
        self.index_data = {
            "notes": {
                self.note_id: {
                    "id": self.note_id,
                    "title": self.note_title,
                    "tags": self.note_tags,
                    "created_at": "2024-01-01T00:00:00+00:00",
                    "last_modified": "2024-01-01T00:00:00+00:00",
                    "filename": f"{self.note_id}.txt",
                }
            }
        }

    @patch("vault.core.write_note_content")
    @patch("vault.core.load_index")
    @patch("vault.core.save_index")
    def test_create_note_success(
        self, mock_save_index, mock_load_index, mock_write_content
    ):
        """Test successful note creation."""
        # Setup mocks
        mock_load_index.return_value = {"notes": {}}

        # Create note
        _create_note_internal(self.note)

        # Verify write_note_content was called
        mock_write_content.assert_called_once_with(
            self.note.id, self.note.content, None
        )

        # Verify index operations
        mock_load_index.assert_called_once()
        mock_save_index.assert_called_once()
        saved_index = mock_save_index.call_args[0][0]
        self.assertIn(self.note.id, saved_index["notes"])
        self.assertEqual(saved_index["notes"][self.note.id]["title"], self.note_title)

    @patch("vault.core.write_note_content")
    @patch("vault.core.load_index")
    def test_create_note_storage_error(self, mock_load_index, mock_write_content):
        """Test handling of StorageError during note creation."""
        # Setup mocks
        mock_write_content.side_effect = StorageError("Write failed")

        with self.assertRaises(StorageError) as context:
            _create_note_internal(self.note)

        # Verify error
        self.assertIn("Failed to create note", str(context.exception))
        self.assertIsInstance(context.exception.original_error, StorageError)
        mock_write_content.assert_called_once()
        mock_load_index.assert_not_called()

    @patch("vault.core.load_index")
    @patch("vault.core.read_note_content")
    def test_get_note_success(self, mock_read_content, mock_load_index):
        """Test successful note retrieval."""
        # Setup mocks
        mock_load_index.return_value = self.index_data
        mock_read_content.return_value = self.note_content

        # Get note
        result = _get_note_internal(self.note_id)

        # Verify result
        self.assertIsInstance(result, Note)
        self.assertEqual(result.id, self.note_id)
        self.assertEqual(result.title, self.note_title)
        self.assertEqual(result.content, self.note_content)
        self.assertEqual(result.tags, self.note_tags)

        # Verify mocks
        mock_load_index.assert_called_once()
        mock_read_content.assert_called_once_with(self.note_id, None)

    @patch("vault.core.load_index")
    def test_get_note_not_found(self, mock_load_index):
        """Test handling of non-existent note."""
        # Setup mocks
        mock_load_index.return_value = {"notes": {}}

        with self.assertRaises(NoteNotFoundError) as context:
            _get_note_internal(self.note_id)

        # Verify error
        self.assertEqual(context.exception.note_id, self.note_id)
        mock_load_index.assert_called_once()

    @patch("vault.core.load_index")
    @patch("vault.core.read_note_content")
    def test_get_note_storage_error(self, mock_read_content, mock_load_index):
        """Test handling of StorageError during note retrieval."""
        # Setup mocks
        mock_load_index.return_value = self.index_data
        mock_read_content.side_effect = StorageError("Read failed")

        with self.assertRaises(StorageError) as context:
            _get_note_internal(self.note_id)

        # Verify error
        self.assertIn("Failed to get note", str(context.exception))
        self.assertIsInstance(context.exception.original_error, StorageError)
        mock_load_index.assert_called_once()
        mock_read_content.assert_called_once()

    @patch("vault.core.load_index")
    @patch("os.remove")
    def test_delete_note_success(self, mock_remove, mock_load_index):
        """Test successful note deletion."""
        # Setup mocks
        mock_load_index.return_value = self.index_data

        # Delete note
        _delete_note_internal(self.note_id)

        # Verify file removal
        mock_remove.assert_called_once()

        # Verify index operations
        mock_load_index.assert_called_once()

    @patch("vault.core.load_index")
    def test_delete_note_not_found(self, mock_load_index):
        """Test handling of non-existent note deletion."""
        # Setup mocks
        mock_load_index.return_value = {"notes": {}}

        with self.assertRaises(NoteNotFoundError) as context:
            _delete_note_internal(self.note_id)

        # Verify error
        self.assertEqual(context.exception.note_id, self.note_id)
        mock_load_index.assert_called_once()

    @patch("vault.core.load_index")
    @patch("os.remove")
    def test_delete_note_file_not_found(self, mock_remove, mock_load_index):
        """Test handling of missing note file during deletion."""
        # Setup mocks
        mock_load_index.return_value = self.index_data
        mock_remove.side_effect = FileNotFoundError()

        # Delete note (should not raise error)
        _delete_note_internal(self.note_id)

        # Verify file removal was attempted
        mock_remove.assert_called_once()

    @patch("vault.core.load_index")
    @patch("os.remove")
    def test_delete_note_storage_error(self, mock_remove, mock_load_index):
        """Test handling of StorageError during note deletion."""
        # Setup mocks
        mock_load_index.return_value = self.index_data
        mock_remove.side_effect = OSError("Permission denied")

        with self.assertRaises(StorageError) as context:
            _delete_note_internal(self.note_id)

        # Verify error
        self.assertIn("Failed to remove note file", str(context.exception))
        self.assertIsInstance(context.exception.original_error, OSError)
        mock_load_index.assert_called_once()
        mock_remove.assert_called_once()

    @patch("vault.core.load_index")
    def test_get_all_titles_success(self, mock_load_index):
        """Test get_all_titles with successful retrieval."""
        # Setup mock
        index_data = {
            "notes": {
                "note1": {"title": "Note 1"},
                "note2": {"title": "Note 2"},
                "note3": {"title": "Note 3"},
            }
        }
        mock_load_index.return_value = index_data

        # Get titles
        titles = get_all_titles()

        # Verify result
        self.assertEqual(titles, ["Note 1", "Note 2", "Note 3"])
        mock_load_index.assert_called_once()

    @patch("vault.core.load_index")
    def test_get_all_titles_empty(self, mock_load_index):
        """Test get_all_titles with empty index."""
        # Setup mock
        mock_load_index.return_value = {}

        # Get titles
        titles = get_all_titles()

        # Verify result
        self.assertEqual(titles, [])
        mock_load_index.assert_called_once()

    @patch("vault.core.load_index")
    def test_get_all_titles_no_notes(self, mock_load_index):
        """Test get_all_titles with no notes in index."""
        # Setup mock
        mock_load_index.return_value = {"other": "data"}

        # Get titles
        titles = get_all_titles()

        # Verify result
        self.assertEqual(titles, [])
        mock_load_index.assert_called_once()

    @patch("vault.core.load_index")
    def test_get_all_titles_storage_error(self, mock_load_index):
        """Test get_all_titles with storage error."""
        # Setup mock
        mock_load_index.side_effect = StorageError("Test error")

        # Get titles and verify error
        with self.assertRaises(StorageError) as context:
            get_all_titles()

        # Verify error
        self.assertIn("Failed to get note titles", str(context.exception))
        self.assertIsInstance(context.exception.original_error, StorageError)
        mock_load_index.assert_called_once()

    def test_search_notes_success(self):
        """Test search_notes with successful matches."""
        # Create test notes
        note1 = self.create_test_note("Test Note 1", "Content 1", ["tag1"])
        note2 = self.create_test_note("Test Note 2", "Content 2", ["tag2"])
        note3 = self.create_test_note("Other Note", "Test content", ["tag3"])

        # Test search in title
        results = vault.search_notes("Test")
        self.assertEqual(len(results), 2)
        self.assertEqual(
            {note.title for note in results}, {"Test Note 1", "Test Note 2"}
        )

        # Test search in content
        results = vault.search_notes("content")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Other Note")

        # Test search in tags
        results = vault.search_notes("tag1")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Test Note 1")

    def test_search_notes_case_insensitive(self):
        """Test search_notes with case-insensitive matching."""
        # Create test note
        self.create_test_note("Test Note", "Content", ["Tag"])

        # Test different cases
        results = vault.search_notes("test")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Test Note")

        results = vault.search_notes("TEST")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Test Note")

        results = vault.search_notes("tag")
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Test Note")

    def test_search_notes_no_matches(self):
        """Test search_notes with no matching notes."""
        # Create test note
        self.create_test_note("Test Note", "Content", ["tag"])

        # Search for non-existent term
        results = vault.search_notes("nonexistent")
        self.assertEqual(len(results), 0)

    def test_search_notes_empty_index(self):
        """Test search_notes with empty index."""
        # Ensure index is empty
        self._clear_index()

        # Search in empty index
        results = vault.search_notes("test")
        self.assertEqual(len(results), 0)

    def test_search_notes_storage_error(self):
        """Test search_notes with storage error."""
        # Create test note
        self.create_test_note("Test Note", "Content", ["tag"])

        # Simulate storage error
        with patch("mpkv.vault.core.load_index") as mock_load:
            mock_load.side_effect = StorageError("Test error")
            with self.assertRaises(StorageError) as context:
                vault.search_notes("test")
            self.assertIn("Failed to search notes", str(context.exception))

    def test_search_notes_graceful_error_handling(self):
        """Test search_notes gracefully handles errors for individual notes."""
        # Create test notes
        self.create_test_note("Test Note 1", "Content 1", ["tag1"])
        self.create_test_note("Test Note 2", "Content 2", ["tag2"])

        # Simulate error reading one note
        with patch("mpkv.vault.core._get_note_internal") as mock_get:
            mock_get.side_effect = [
                StorageError("Test error"),
                self.create_test_note("Test Note 2", "Content 2", ["tag2"]),
            ]
            results = vault.search_notes("Test")
            self.assertEqual(len(results), 1)
            self.assertEqual(results[0].title, "Test Note 2")

    def test_get_all_tags_with_counts_success(self):
        """Test get_all_tags_with_counts with successful retrieval."""
        # Create test notes with tags
        self.create_test_note("Note 1", "Content 1", ["work", "personal"])
        self.create_test_note("Note 2", "Content 2", ["work", "ideas"])
        self.create_test_note("Note 3", "Content 3", ["personal"])

        # Get tag counts
        tag_counts = vault.get_all_tags_with_counts()

        # Verify results
        self.assertEqual(tag_counts, {"work": 2, "personal": 2, "ideas": 1})

    def test_get_all_tags_with_counts_empty(self):
        """Test get_all_tags_with_counts with no tags."""
        # Create test note without tags
        self.create_test_note("Note 1", "Content 1")

        # Get tag counts
        tag_counts = vault.get_all_tags_with_counts()

        # Verify results
        self.assertEqual(tag_counts, {})

    def test_get_all_tags_with_counts_no_notes(self):
        """Test get_all_tags_with_counts with no notes."""
        # Ensure index is empty
        self._clear_index()

        # Get tag counts
        tag_counts = vault.get_all_tags_with_counts()

        # Verify results
        self.assertEqual(tag_counts, {})

    def test_get_all_tags_with_counts_storage_error(self):
        """Test get_all_tags_with_counts with storage error."""
        # Create test note
        self.create_test_note("Note 1", "Content 1", ["tag1"])

        # Simulate storage error
        with patch("vault.core.load_index") as mock_load:
            mock_load.side_effect = StorageError("Test error")
            with self.assertRaises(StorageError) as context:
                vault.get_all_tags_with_counts()
            self.assertIn("Failed to get tag counts", str(context.exception))

    def test_export_notes_success(self):
        """Test export_notes with successful export."""
        # Create test notes
        self.create_test_note("Test Note 1", "Content 1", ["tag1"])
        self.create_test_note("Test Note 2", "Content 2", ["tag2"])

        # Create temporary directory for export
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export notes
            vault.export_notes(temp_dir)

            # Verify files were created
            files = os.listdir(temp_dir)
            self.assertEqual(len(files), 2)
            self.assertIn("Test_Note_1.txt", files)
            self.assertIn("Test_Note_2.txt", files)

            # Verify file contents
            with open(
                os.path.join(temp_dir, "Test_Note_1.txt"), "r", encoding="utf-8"
            ) as f:
                content = f.read()
                self.assertIn("Title: Test Note 1", content)
                self.assertIn("Content 1", content)

    def test_export_notes_filename_sanitization(self):
        """Test export_notes with filename sanitization."""
        # Create test note with special characters
        self.create_test_note("Test/Note*With?Special:Chars", "Content")

        # Create temporary directory for export
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export notes
            vault.export_notes(temp_dir)

            # Verify file was created with sanitized name
            files = os.listdir(temp_dir)
            self.assertEqual(len(files), 1)
            self.assertIn("Test_Note_With_Special_Chars.txt", files)

    def test_export_notes_empty_title(self):
        """Test export_notes with empty title."""
        # Create test note with empty title
        self.create_test_note("", "Content")

        # Create temporary directory for export
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export notes
            vault.export_notes(temp_dir)

            # Verify file was created with default name
            files = os.listdir(temp_dir)
            self.assertEqual(len(files), 1)
            self.assertIn("untitled.txt", files)

    def test_export_notes_no_notes(self):
        """Test export_notes with no notes."""
        # Create temporary directory for export
        with tempfile.TemporaryDirectory() as temp_dir:
            # Export notes
            vault.export_notes(temp_dir)

            # Verify no files were created
            self.assertEqual(len(os.listdir(temp_dir)), 0)

    def test_export_notes_storage_error(self):
        """Test export_notes with storage error."""
        # Create test note
        self.create_test_note("Test Note", "Content")

        # Create temporary directory for export
        with tempfile.TemporaryDirectory() as temp_dir:
            # Simulate storage error
            with patch("vault.core.load_index") as mock_load:
                mock_load.side_effect = StorageError("Test error")
                with self.assertRaises(StorageError) as context:
                    vault.export_notes(temp_dir)
                self.assertIn("Failed to export notes", str(context.exception))

    def test_export_notes_os_error(self):
        """Test export_notes with OSError."""
        # Create test note
        self.create_test_note("Test Note", "Content")

        # Simulate OSError
        with patch("os.makedirs") as mock_makedirs:
            mock_makedirs.side_effect = OSError("Permission denied")
            with self.assertRaises(OSError) as context:
                vault.export_notes("/invalid/path")
            self.assertIn("Failed to create output directory", str(context.exception))

    def test_export_notes_graceful_error_handling(self):
        """Test export_notes gracefully handles errors for individual notes."""
        # Create test notes
        self.create_test_note("Test Note 1", "Content 1")
        self.create_test_note("Test Note 2", "Content 2")

        # Create temporary directory for export
        with tempfile.TemporaryDirectory() as temp_dir:
            # Simulate error reading one note
            with patch("vault.core.read_note_content") as mock_read:
                mock_read.side_effect = [StorageError("Test error"), "Content 2"]
                vault.export_notes(temp_dir)

                # Verify only the successful note was exported
                files = os.listdir(temp_dir)
                self.assertEqual(len(files), 1)
                self.assertIn("Test_Note_2.txt", files)


if __name__ == "__main__":
    unittest.main()
