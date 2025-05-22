import datetime
import unittest
import uuid

from vault.models import Note


class TestNote(unittest.TestCase):
    """
    Test cases for the Note model.
    """

    def setUp(self):
        """Set up test fixtures."""
        self.valid_title = "Test Note"
        self.valid_content = (
            "This is a test note with sufficient content for validation."
        )
        self.valid_tags = "test, note, unittest"

    def test_init_minimal(self):
        """Test creation of a Note with minimal parameters."""
        note = Note(title=self.valid_title, content=self.valid_content)

        # Check required attributes
        self.assertEqual(note.title, self.valid_title)
        self.assertEqual(note.content, self.valid_content)

        # Check defaults
        self.assertIsNone(note.tags)
        self.assertTrue(note.id)  # Should have generated UUID
        self.assertIsInstance(note.created_at, datetime.datetime)
        self.assertIsInstance(note.last_modified, datetime.datetime)
        self.assertEqual(note.last_modified, note.created_at)
        self.assertTrue(note.filename.endswith(".txt"))
        self.assertIn(note.id, note.filename)  # Filename should contain ID

    def test_init_with_all_params(self):
        """Test creation of a Note with all parameters specified."""
        test_id = str(uuid.uuid4())
        test_created = datetime.datetime(2023, 1, 1, tzinfo=datetime.timezone.utc)
        test_modified = datetime.datetime(2023, 1, 2, tzinfo=datetime.timezone.utc)
        test_filename = "custom_filename.md"

        note = Note(
            title=self.valid_title,
            content=self.valid_content,
            tags=self.valid_tags,
            id=test_id,
            created_at=test_created,
            last_modified=test_modified,
            filename=test_filename,
        )

        # Check all attributes
        self.assertEqual(note.title, self.valid_title)
        self.assertEqual(note.content, self.valid_content)
        self.assertEqual(note.tags, ["test", "note", "unittest"])
        self.assertEqual(note.id, test_id)
        self.assertEqual(note.created_at, test_created)
        self.assertEqual(note.last_modified, test_modified)
        self.assertEqual(note.filename, test_filename)

    def test_init_with_string_dates(self):
        """Test creation of a Note with string datetime values."""
        test_created = "2023-01-01T00:00:00+00:00"
        test_modified = "2023-01-02T00:00:00+00:00"

        note = Note(
            title=self.valid_title,
            content=self.valid_content,
            created_at=test_created,
            last_modified=test_modified,
        )

        # Check datetime conversion
        self.assertIsInstance(note.created_at, datetime.datetime)
        self.assertIsInstance(note.last_modified, datetime.datetime)
        self.assertEqual(note.created_at.year, 2023)
        self.assertEqual(note.created_at.month, 1)
        self.assertEqual(note.created_at.day, 1)
        self.assertEqual(note.last_modified.year, 2023)
        self.assertEqual(note.last_modified.month, 1)
        self.assertEqual(note.last_modified.day, 2)

    def test_init_with_tag_list(self):
        """Test creation of a Note with tags provided as a list."""
        tag_list = ["test", "note", "unittest"]

        note = Note(title=self.valid_title, content=self.valid_content, tags=tag_list)

        self.assertEqual(note.tags, tag_list)

    def test_validation_title(self):
        """Test that the title field is properly validated."""
        # Test required validation
        with self.assertRaises(ValueError):
            Note(title=None, content=self.valid_content)

        # Test length validation
        with self.assertRaises(ValueError):
            Note(title="A" * 101, content=self.valid_content)

        # Test character validation
        with self.assertRaises(ValueError):
            Note(title="Invalid-Title!", content=self.valid_content)

    def test_validation_content(self):
        """Test that the content field is properly validated."""
        # Test required validation
        with self.assertRaises(ValueError):
            Note(title=self.valid_title, content=None)

        # Test minimum length validation
        with self.assertRaises(ValueError):
            Note(title=self.valid_title, content="Too short")

        # Test maximum length validation
        with self.assertRaises(ValueError):
            Note(title=self.valid_title, content="A" * 10001)

    def test_validation_tags(self):
        """Test that the tags field is properly validated."""
        # Test maximum tag count
        too_many_tags = ",".join([f"tag{i}" for i in range(21)])  # 21 tags
        with self.assertRaises(ValueError):
            Note(title=self.valid_title, content=self.valid_content, tags=too_many_tags)

        # Test maximum tag length
        long_tag = "A" * 31  # 31 characters
        with self.assertRaises(ValueError):
            Note(
                title=self.valid_title,
                content=self.valid_content,
                tags=f"normal,{long_tag}",
            )

    def test_attribute_access(self):
        """Test accessing attributes directly and via descriptors."""
        note = Note(
            title=self.valid_title, content=self.valid_content, tags=self.valid_tags
        )

        # Direct access
        self.assertEqual(note.title, self.valid_title)
        self.assertEqual(note.content, self.valid_content)
        self.assertEqual(note.tags, ["test", "note", "unittest"])

        # Descriptor access from class should return descriptor instance
        self.assertNotEqual(Note.title, self.valid_title)
        self.assertNotEqual(Note.content, self.valid_content)
        self.assertNotEqual(Note.tags, ["test", "note", "unittest"])

    def test_to_dict(self):
        """Test conversion of Note to dictionary."""
        note = Note(
            title=self.valid_title, content=self.valid_content, tags=self.valid_tags
        )

        result = note.to_dict()

        # Check structure
        self.assertIsInstance(result, dict)
        self.assertIn("id", result)
        self.assertIn("title", result)
        self.assertIn("tags", result)
        self.assertIn("created_at", result)
        self.assertIn("last_modified", result)
        self.assertIn("filename", result)

        # Check values
        self.assertEqual(result["id"], note.id)
        self.assertEqual(result["title"], self.valid_title)
        self.assertEqual(result["tags"], ["test", "note", "unittest"])

        # Check timestamps format (should be ISO strings)
        self.assertIsInstance(result["created_at"], str)
        self.assertIsInstance(result["last_modified"], str)

    def test_to_dict_without_tags(self):
        """Test conversion of Note without tags to dictionary."""
        note = Note(title=self.valid_title, content=self.valid_content)

        result = note.to_dict()

        # Tags should be an empty list
        self.assertEqual(result["tags"], [])

    def test_from_dict(self):
        """Test creation of Note from dictionary and content."""
        test_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc)
        now_iso = now.isoformat()

        data = {
            "id": test_id,
            "title": self.valid_title,
            "tags": ["test", "note", "unittest"],
            "created_at": now_iso,
            "last_modified": now_iso,
            "filename": f"{test_id}.txt",
        }

        note = Note.from_dict(data, self.valid_content)

        # Check attributes
        self.assertEqual(note.id, test_id)
        self.assertEqual(note.title, self.valid_title)
        self.assertEqual(note.content, self.valid_content)
        self.assertEqual(note.tags, ["test", "note", "unittest"])
        self.assertEqual(note.filename, f"{test_id}.txt")

        # Check timestamp conversion
        self.assertIsInstance(note.created_at, datetime.datetime)
        self.assertEqual(note.created_at.isoformat(), now_iso)

    def test_from_dict_minimal(self):
        """Test creation of Note from minimal dictionary."""
        # Only provide required fields
        data = {
            "id": str(uuid.uuid4()),
            "title": self.valid_title,
        }

        note = Note.from_dict(data, self.valid_content)

        # Check required fields
        self.assertEqual(note.id, data["id"])
        self.assertEqual(note.title, self.valid_title)
        self.assertEqual(note.content, self.valid_content)

        # Check defaults
        self.assertEqual(note.tags, [])  # Empty list from to_dict

    def test_update_methods(self):
        """Test the update methods for title, content, and tags."""
        note = Note(
            title=self.valid_title, content=self.valid_content, tags=self.valid_tags
        )

        original_modified = note.last_modified

        # Wait a small amount to ensure timestamps will differ
        import time

        time.sleep(0.001)

        # Test update_title
        new_title = "Updated Title"
        note.update_title(new_title)
        self.assertEqual(note.title, new_title)
        self.assertGreater(note.last_modified, original_modified)

        # Save the new last_modified time
        title_modified = note.last_modified
        time.sleep(0.001)

        # Test update_content
        new_content = "This is updated content with sufficient length for validation."
        note.update_content(new_content)
        self.assertEqual(note.content, new_content)
        self.assertGreater(note.last_modified, title_modified)

        # Save the new last_modified time
        content_modified = note.last_modified
        time.sleep(0.001)

        # Test update_tags
        new_tags = "updated, tags"
        note.update_tags(new_tags)
        self.assertEqual(note.tags, ["updated", "tags"])
        self.assertGreater(note.last_modified, content_modified)

    def test_repr(self):
        """Test the string representation of a Note."""
        note = Note(title=self.valid_title, content=self.valid_content)

        repr_str = repr(note)

        # Check that the representation includes the title
        self.assertIn(self.valid_title, repr_str)
        self.assertIn("Note", repr_str)


if __name__ == "__main__":
    unittest.main()
