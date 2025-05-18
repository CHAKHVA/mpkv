import unittest

from vault.fields import BaseField, ContentField, TagsField, TitleField


class TestModel:
    """
    Dummy model class for testing descriptors.
    """

    title = TitleField()
    optional_title = TitleField(required=False)
    content = ContentField()
    optional_content = ContentField(required=False)
    tags = TagsField()
    required_tags = TagsField(required=True)


class TestFields(unittest.TestCase):
    """
    Test cases for field validation descriptors.
    """

    def test_base_field_required(self):
        """Test that BaseField validates required fields."""

        class TestBaseModel:
            field = BaseField()

        model = TestBaseModel()
        with self.assertRaises(ValueError) as context:
            model.field = None
        self.assertIn("required", str(context.exception))

    def test_base_field_optional(self):
        """Test that BaseField allows None for optional fields."""

        class TestBaseModel:
            field = BaseField(required=False)

        model = TestBaseModel()
        model.field = None
        self.assertIsNone(model.field)

    def test_title_field_valid(self):
        """Test that TitleField accepts valid titles."""
        model = TestModel()
        valid_titles = ["Test Title", "Title123", "Simple", "A" * 100]

        for title in valid_titles:
            model.title = title
            self.assertEqual(model.title, title)

    def test_title_field_required(self):
        """Test that TitleField enforces required constraint."""
        model = TestModel()

        # Should raise error when setting required field to None
        with self.assertRaises(ValueError) as context:
            model.title = None
        self.assertIn("required", str(context.exception))

        # Should not raise error when setting optional field to None
        model.optional_title = None
        self.assertIsNone(model.optional_title)

    def test_title_field_max_length(self):
        """Test that TitleField enforces maximum length."""
        model = TestModel()
        too_long_title = "A" * 101  # One character too many

        with self.assertRaises(ValueError) as context:
            model.title = too_long_title
        self.assertIn("must not exceed", str(context.exception))

    def test_title_field_invalid_characters(self):
        """Test that TitleField validates character constraints."""
        model = TestModel()
        invalid_titles = ["Test-Title", "Title#123", "Simple!", "Title@home"]

        for title in invalid_titles:
            with self.assertRaises(ValueError) as context:
                model.title = title
            self.assertIn("invalid character", str(context.exception))

    def test_title_field_get_set(self):
        """Test that TitleField properly gets and sets values."""
        model = TestModel()
        model.title = "My Title"
        self.assertEqual(model.title, "My Title")

        # Test that accessing descriptor from class returns the descriptor itself
        self.assertIsInstance(TestModel.title, TitleField)

    def test_content_field_valid(self):
        """Test that ContentField accepts valid content."""
        model = TestModel()

        # Just above minimum length
        model.content = "A" * 10
        self.assertEqual(model.content, "A" * 10)

        # Typical content
        typical_content = "This is some typical content for testing purposes."
        model.content = typical_content
        self.assertEqual(model.content, typical_content)

        # Just below maximum length
        model.content = "A" * 9999
        self.assertEqual(model.content, "A" * 9999)

    def test_content_field_required(self):
        """Test that ContentField enforces required constraint."""
        model = TestModel()

        # Should raise error when setting required field to None
        with self.assertRaises(ValueError) as context:
            model.content = None
        self.assertIn("required", str(context.exception))

        # Should not raise error when setting optional field to None
        model.optional_content = None
        self.assertIsNone(model.optional_content)

    def test_content_field_min_length(self):
        """Test that ContentField enforces minimum length."""
        model = TestModel()
        too_short_content = "A" * 9  # One character too few

        with self.assertRaises(ValueError) as context:
            model.content = too_short_content
        self.assertIn("must be at least", str(context.exception))

    def test_content_field_max_length(self):
        """Test that ContentField enforces maximum length."""
        model = TestModel()
        too_long_content = "A" * 10001  # One character too many

        with self.assertRaises(ValueError) as context:
            model.content = too_long_content
        self.assertIn("must not exceed", str(context.exception))

    def test_content_field_get_set(self):
        """Test that ContentField properly gets and sets values."""
        model = TestModel()
        content = "This is some content that is at least 10 characters."
        model.content = content
        self.assertEqual(model.content, content)

        # Test that accessing descriptor from class returns the descriptor itself
        self.assertIsInstance(TestModel.content, ContentField)

    def test_tags_field_valid_string_to_list(self):
        """Test that TagsField converts comma-separated strings to lists."""
        model = TestModel()

        # Single tag
        model.tags = "python"
        self.assertEqual(model.tags, ["python"])

        # Multiple tags
        model.tags = "python, tutorial, code"
        self.assertEqual(model.tags, ["python", "tutorial", "code"])

    def test_tags_field_stripping_whitespace(self):
        """Test that TagsField strips whitespace from tags."""
        model = TestModel()

        model.tags = "  python  ,  tutorial  ,  code  "
        self.assertEqual(model.tags, ["python", "tutorial", "code"])

    def test_tags_field_empty_input(self):
        """Test that TagsField handles empty input."""
        model = TestModel()

        # Empty string
        model.tags = ""
        self.assertEqual(model.tags, [])

        # String with only commas and spaces
        model.tags = " , , "
        self.assertEqual(model.tags, [])

        # None for optional field
        model.tags = None
        self.assertIsNone(model.tags)

    def test_tags_field_required(self):
        """Test that TagsField enforces required constraint."""
        model = TestModel()

        # Should raise error when setting required field to None
        with self.assertRaises(ValueError) as context:
            model.required_tags = None
        self.assertIn("required", str(context.exception))

    def test_tags_field_list_input(self):
        """Test that TagsField accepts list input."""
        model = TestModel()

        # List of tags
        model.tags = ["python", "tutorial", "code"]
        self.assertEqual(model.tags, ["python", "tutorial", "code"])

        # List with spaces to strip
        model.tags = ["  python  ", "  tutorial  ", "  code  "]
        self.assertEqual(model.tags, ["python", "tutorial", "code"])

    def test_tags_field_max_tags(self):
        """Test that TagsField enforces maximum number of tags."""
        model = TestModel()

        # Create a list with 21 tags (exceeding the default max of 20)
        too_many_tags = [f"tag{i}" for i in range(21)]

        with self.assertRaises(ValueError) as context:
            model.tags = too_many_tags
        self.assertIn("cannot have more than", str(context.exception))

    def test_tags_field_max_tag_length(self):
        """Test that TagsField enforces maximum tag length."""
        model = TestModel()

        # Tag that exceeds the default max length of 30
        too_long_tag = "A" * 31

        with self.assertRaises(ValueError) as context:
            model.tags = [too_long_tag]
        self.assertIn("exceeds maximum length", str(context.exception))

    def test_tags_field_get_set(self):
        """Test that TagsField properly gets and sets values."""
        model = TestModel()
        model.tags = "python, tutorial"
        self.assertEqual(model.tags, ["python", "tutorial"])

        # Test that accessing descriptor from class returns the descriptor itself
        self.assertIsInstance(TestModel.tags, TagsField)


if __name__ == "__main__":
    unittest.main()
