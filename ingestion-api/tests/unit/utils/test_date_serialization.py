"""
Test for date serialization in metadata extraction.

This test verifies that dates in YAML frontmatter are properly converted to
JSON-serializable ISO format strings.
"""

import json

from app.utils.file_processor import MarkdownFileProcessor


class TestDateSerialization:
    """Test date serialization in metadata extraction."""

    def test_dates_are_json_serializable(self):
        """Test that dates in frontmatter are converted to JSON-serializable strings."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""---
title: Test Document
author: John Doe
created: 2023-01-01
updated: 2023-12-15
tags:
  - test
  - metadata
---

# Test Content

This is test content with dates in metadata.
"""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert - metadata should contain string dates, not date objects
        assert metadata["created"] == "2023-01-01"
        assert metadata["updated"] == "2023-12-15"
        assert isinstance(metadata["created"], str)
        assert isinstance(metadata["updated"], str)

        # Most importantly, the metadata should be JSON serializable
        json_str = json.dumps(metadata)
        assert json_str is not None

        # And we should be able to deserialize it back
        deserialized = json.loads(json_str)
        assert deserialized["created"] == "2023-01-01"
        assert deserialized["updated"] == "2023-12-15"

    def test_datetime_with_time_is_json_serializable(self):
        """Test that datetime objects with time components are also converted properly."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""---
title: Test Document
created_at: 2023-01-01T10:30:00Z
updated_at: 2023-12-15T15:45:30
---

# Test Content

This is test content with datetime metadata.
"""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert - datetime should also be converted to ISO strings
        assert isinstance(metadata["created_at"], str)
        assert isinstance(metadata["updated_at"], str)

        # Should be JSON serializable
        json_str = json.dumps(metadata)
        assert json_str is not None

    def test_non_date_metadata_remains_unchanged(self):
        """Test that non-date metadata values remain unchanged."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""---
title: Test Document
version: 1.0
published: true
tags:
  - test
  - metadata
config:
  debug: false
  max_items: 100
---

# Test Content

This is test content with mixed metadata types.
"""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert - non-date values should remain as their original types
        assert metadata["title"] == "Test Document"
        assert metadata["version"] == 1.0
        assert metadata["published"] is True
        assert metadata["tags"] == ["test", "metadata"]
        assert metadata["config"]["debug"] is False
        assert metadata["config"]["max_items"] == 100

        # Should be JSON serializable
        json_str = json.dumps(metadata)
        assert json_str is not None
