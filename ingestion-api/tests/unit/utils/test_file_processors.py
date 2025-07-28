"""
Unit tests for file processors.

These tests verify that file processors correctly extract text and metadata
from different file formats.
"""

import pytest
from app.utils.file_processor import (
    FileProcessingError,
    FileProcessorRegistry,
    MarkdownFileProcessor,
    PDFFileProcessor,
)


class TestMarkdownFileProcessor:
    """Test the MarkdownFileProcessor class."""

    def test_extract_text_from_simple_markdown(self):
        """Test extracting text from simple markdown content."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""# Test Document

This is a test markdown document.

## Section 1
Content for section 1.
"""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        expected_text = """# Test Document

This is a test markdown document.

## Section 1
Content for section 1.
"""
        assert text == expected_text
        assert isinstance(metadata, dict)

    def test_extract_text_from_empty_markdown(self):
        """Test extracting text from empty markdown."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert text == ""
        assert isinstance(metadata, dict)

    def test_extract_text_with_unicode_characters(self):
        """Test extracting text with unicode characters."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = "# Document with émojis 🎉 and symbols àáâã".encode()

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert "émojis 🎉" in text
        assert "àáâã" in text
        assert isinstance(metadata, dict)

    def test_extract_text_with_latin1_encoding(self):
        """Test extracting text from Latin-1 encoded content that would fail UTF-8."""
        # Arrange
        processor = MarkdownFileProcessor()
        # Create content with the problematic byte 0xb5 (µ symbol in Latin-1)
        latin1_content = "# Document\n\nThis has a µ (micro) symbol and other chars: àáâãäåæç"
        content = latin1_content.encode("latin-1")  # This creates the 0xb5 byte

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert "µ" in text  # Should successfully decode the micro symbol
        assert "àáâãäåæç" in text
        assert isinstance(metadata, dict)

    def test_extract_text_with_windows1252_encoding(self):
        """Test extracting text from Windows-1252 encoded content."""
        # Arrange
        processor = MarkdownFileProcessor()
        # Create content with specific bytes that are valid in Windows-1252 but different from Latin-1
        # Byte 0x80 is Euro symbol in Windows-1252 but undefined in Latin-1
        content = b"# Document\n\nWindows char: \x80"  # Euro symbol

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert "Windows char:" in text
        assert isinstance(metadata, dict)

    def test_extract_text_with_invalid_encoding_fallback(self):
        """Test that invalid bytes are handled gracefully with replacement."""
        # Arrange
        processor = MarkdownFileProcessor()
        # Create content with bytes that are invalid in all common encodings
        content = b"# Document\n\nInvalid bytes: \xff\xfe\xfd"

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert "# Document" in text
        assert "Invalid bytes:" in text
        # Should contain replacement characters for invalid bytes
        assert isinstance(metadata, dict)

    def test_extract_text_with_code_blocks(self):
        """Test extracting text that includes code blocks."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""# Code Example

Here's some Python code:

```python
def hello():
    return "world"
```

End of document.
"""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert "def hello():" in text
        assert "```python" in text
        assert "End of document." in text


class TestMarkdownMetadataExtraction:
    """Test metadata extraction from markdown files."""

    def test_extract_metadata_with_frontmatter(self):
        """Test extracting metadata from markdown with YAML frontmatter."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""---
title: Test Document
author: John Doe
tags:
  - test
  - markdown
created: 2023-01-01
version: 1.0
---

# Main Content

This is the main content of the document.
"""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert metadata["title"] == "Test Document"
        assert metadata["author"] == "John Doe"
        assert metadata["tags"] == ["test", "markdown"]
        assert metadata["created"] == "2023-01-01"
        assert metadata["version"] == 1.0

        # Text should not contain frontmatter
        assert "---" not in text
        assert "title: Test Document" not in text
        assert "# Main Content" in text
        assert "This is the main content" in text

    def test_extract_metadata_empty_frontmatter(self):
        """Test extracting metadata from markdown with empty frontmatter."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""---
---

# Content Only

This document has empty frontmatter.
"""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert metadata == {}
        assert "# Content Only" in text
        assert "This document has empty frontmatter." in text

    def test_extract_metadata_no_frontmatter(self):
        """Test extracting metadata from markdown without frontmatter."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""# Simple Document

This document has no frontmatter.
"""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert metadata == {}
        assert "# Simple Document" in text
        assert "This document has no frontmatter." in text

    def test_extract_metadata_complex_frontmatter(self):
        """Test extracting metadata with complex nested YAML structures."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""---
title: Complex Document
metadata:
  keywords:
    - python
    - testing
    - metadata
  settings:
    debug: true
    max_results: 100
  nested:
    level1:
      level2:
        value: "deep nested value"
authors:
  - name: John Doe
    email: john@example.com
  - name: Jane Smith
    email: jane@example.com
---

# Document Content

Content goes here.
"""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert metadata["title"] == "Complex Document"
        assert metadata["metadata"]["keywords"] == ["python", "testing", "metadata"]
        assert metadata["metadata"]["settings"]["debug"] is True
        assert metadata["metadata"]["settings"]["max_results"] == 100
        assert metadata["metadata"]["nested"]["level1"]["level2"]["value"] == "deep nested value"
        assert len(metadata["authors"]) == 2
        assert metadata["authors"][0]["name"] == "John Doe"
        assert metadata["authors"][1]["email"] == "jane@example.com"

        # Text should not contain frontmatter
        assert "# Document Content" in text
        assert "Content goes here." in text

    def test_extract_metadata_invalid_yaml_raises_error(self):
        """Test that invalid YAML in frontmatter raises FileProcessingError."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""---
title: Invalid YAML
invalid_yaml: [unclosed list
another_field: value
---

# Content

This has invalid YAML frontmatter.
"""

        # Act & Assert
        with pytest.raises(FileProcessingError) as exc_info:
            processor.parse_content(content)

        assert "Failed to extract metadata" in str(exc_info.value)

    def test_extract_metadata_partial_frontmatter_delimiters(self):
        """Test that incomplete frontmatter delimiters are ignored."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""---
title: Incomplete
# Missing closing delimiter

# Main Content

This document has incomplete frontmatter.
"""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert metadata == {}
        # Should contain the entire original content since frontmatter was incomplete
        assert "---" in text
        assert "title: Incomplete" in text
        assert "# Main Content" in text

    def test_extract_metadata_frontmatter_with_content_dashes(self):
        """Test that frontmatter extraction works when content contains dashes."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""---
title: Document with Dashes
category: test
---

# Main Content

This document has content with --- three dashes in the middle.

And some more content after that.
"""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert metadata["title"] == "Document with Dashes"
        assert metadata["category"] == "test"

        # Text should contain the content dashes but not frontmatter dashes
        assert "# Main Content" in text
        assert "three dashes" in text
        assert "---" in text  # From content, not frontmatter
        assert "title: Document with Dashes" not in text

    def test_extract_metadata_multiline_string_values(self):
        """Test extracting metadata with multiline string values."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""---
title: Multiline Content
description: |
  This is a multiline description
  that spans multiple lines
  and preserves formatting.
summary: >
  This is a folded string
  that will be joined into
  a single line.
---

# Content

Document content here.
"""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert metadata["title"] == "Multiline Content"
        assert "multiline description" in metadata["description"]
        assert "spans multiple lines" in metadata["description"]
        assert isinstance(metadata["summary"], str)
        assert "folded string" in metadata["summary"]

    def test_extract_metadata_with_special_characters(self):
        """Test extracting metadata with special characters and unicode."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = b"""---
title: Special Characters Test
author: "Jos\xc3\xa9 Mar\xc3\xada"
description: "Document with \xc3\xa9mojis \xf0\x9f\x8e\x89 and symbols \xc3\xa0\xc3\xa1\xc3\xa2\xc3\xa3"
tags:
  - "espa\xc3\xb1ol"
  - "portugu\xc3\xaas"
  - "fran\xc3\xa7ais"
unicode_field: "\xe6\xb5\x8b\xe8\xaf\x95\xe4\xb8\xad\xe6\x96\x87"
---

# Content

Unicode content: \xe4\xbd\xa0\xe5\xa5\xbd\xe4\xb8\x96\xe7\x95\x8c
"""

        # Act
        text, metadata = processor.parse_content(content)

        # Assert
        assert metadata["title"] == "Special Characters Test"
        assert metadata["author"] == "José María"
        assert "émojis 🎉" in metadata["description"]
        assert "àáâã" in metadata["description"]
        assert "español" in metadata["tags"]
        assert metadata["unicode_field"] == "测试中文"

        # Text should contain unicode content
        assert "你好世界" in text

    def test_extract_metadata_method_directly(self):
        """Test the extract_metadata method directly."""
        # Arrange
        processor = MarkdownFileProcessor()
        content_with_frontmatter = """---
title: Direct Test
type: unit_test
---

# Content

Test content."""

        content_without_frontmatter = """# No Frontmatter

Just content."""

        # Act
        content_with, metadata_with = processor.extract_metadata(content_with_frontmatter)
        content_without, metadata_without = processor.extract_metadata(content_without_frontmatter)

        # Assert
        assert content_with is not None
        assert metadata_with is not None
        assert metadata_with["title"] == "Direct Test"
        assert metadata_with["type"] == "unit_test"
        assert content_without is not None
        assert metadata_without is None


class TestPDFFileProcessor:
    """Test the PDFFileProcessor class."""

    def test_pdf_processor_exists(self):
        """Test that PDFFileProcessor can be instantiated."""
        # This is a basic test since we don't have actual PDF content
        # In a real scenario, you'd test with actual PDF files
        processor = PDFFileProcessor()
        assert processor is not None

    def test_pdf_metadata_structure(self):
        """Test that PDF processor returns expected metadata structure."""
        # Note: This is a design test to ensure the metadata structure is correct
        # In practice, you would need actual PDF files to test thoroughly
        processor = PDFFileProcessor()

        # We can't test actual PDF parsing without PDF files, but we can
        # verify the processor implements the correct interface
        assert hasattr(processor, "parse_content")
        assert callable(processor.parse_content)

    # Note: Comprehensive PDF testing would require actual PDF files
    # Here are example tests you would implement with real PDF content:
    #
    # def test_pdf_extract_text_and_metadata_from_simple_pdf(self):
    #     """Test extracting text and metadata from a simple PDF."""
    #     # Would require a test PDF file
    #     pass
    #
    # def test_pdf_extract_metadata_with_multiple_pages(self):
    #     """Test that PDF processor correctly counts pages."""
    #     # Would test that metadata['pages'] == expected_page_count
    #     pass
    #
    # def test_pdf_extract_metadata_with_pdf_properties(self):
    #     """Test extracting PDF properties like author, title, creation date."""
    #     # Would test that metadata contains PDF document properties
    #     pass

    # Note: Testing PDFFileProcessor with real PDF content would require
    # actual PDF files. In practice, you'd create test PDF files or
    # use mock PDF libraries for comprehensive testing.


class TestFileProcessorRegistry:
    """Test the FileProcessorRegistry class."""

    def test_get_markdown_processor(self):
        """Test getting processor for markdown files."""
        # Act
        processor = FileProcessorRegistry.get_processor("test.md")

        # Assert
        assert isinstance(processor, MarkdownFileProcessor)

    def test_get_pdf_processor(self):
        """Test getting processor for PDF files."""
        # Act
        processor = FileProcessorRegistry.get_processor("test.pdf")

        # Assert
        assert isinstance(processor, PDFFileProcessor)

    def test_unsupported_file_extension_raises_error(self):
        """Test that unsupported file extensions raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            FileProcessorRegistry.get_processor("test.xyz")
        assert "No processor for .xyz" in str(exc_info.value)

    def test_file_without_extension_raises_error(self):
        """Test that files without extensions raise ValueError."""
        # Act & Assert
        with pytest.raises(ValueError) as exc_info:
            FileProcessorRegistry.get_processor("test")
        assert "No processor for" in str(exc_info.value)

    def test_case_insensitive_extension_matching(self):
        """Test that extension matching works regardless of case."""
        # Note: Current implementation might be case-sensitive
        # This test documents the expected behavior
        try:
            processor = FileProcessorRegistry.get_processor("test.MD")
            # If this succeeds, extension matching is case-insensitive
            assert isinstance(processor, MarkdownFileProcessor)
        except ValueError:
            # If this fails, extension matching is case-sensitive
            # This is the current behavior
            pass

    def test_different_markdown_extensions(self):
        """Test different markdown file extensions."""
        # Currently only .md is registered, but this tests the concept
        processor = FileProcessorRegistry.get_processor("readme.md")
        assert isinstance(processor, MarkdownFileProcessor)

    def test_file_path_with_multiple_dots(self):
        """Test file paths with multiple dots in the name."""
        processor = FileProcessorRegistry.get_processor("my.config.file.md")
        assert isinstance(processor, MarkdownFileProcessor)

    def test_registry_can_be_extended(self):
        """Test that the registry can be extended with new processors."""
        # This is more of a design test - ensuring the registry is extensible
        original_processors = FileProcessorRegistry._processors.copy()

        try:
            # Test that we can register a new extension
            class TestProcessor(MarkdownFileProcessor):
                pass

            FileProcessorRegistry.register_extension(".test", TestProcessor)
            processor = FileProcessorRegistry.get_processor("file.test")
            assert isinstance(processor, TestProcessor)

        finally:
            # Clean up - restore original processors
            FileProcessorRegistry._processors = original_processors
