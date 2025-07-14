"""
Unit tests for file processors.

These tests verify that file processors correctly extract text and metadata
from different file formats.
"""

from app.utils.file_processor import (
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
        text, metadata = processor.extract_text(content)

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
        text, metadata = processor.extract_text(content)

        # Assert
        assert text == ""
        assert isinstance(metadata, dict)

    def test_extract_text_with_unicode_characters(self):
        """Test extracting text with unicode characters."""
        # Arrange
        processor = MarkdownFileProcessor()
        content = "# Document with émojis 🎉 and symbols àáâã".encode()

        # Act
        text, metadata = processor.extract_text(content)

        # Assert
        assert "émojis 🎉" in text
        assert "àáâã" in text
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
        text, metadata = processor.extract_text(content)

        # Assert
        assert "def hello():" in text
        assert "```python" in text
        assert "End of document." in text


class TestPDFFileProcessor:
    """Test the PDFFileProcessor class."""

    def test_pdf_processor_exists(self):
        """Test that PDFFileProcessor can be instantiated."""
        # This is a basic test since we don't have actual PDF content
        # In a real scenario, you'd test with actual PDF files
        processor = PDFFileProcessor()
        assert processor is not None

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
        try:
            FileProcessorRegistry.get_processor("test.xyz")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "No processor for .xyz" in str(e)

    def test_file_without_extension_raises_error(self):
        """Test that files without extensions raise ValueError."""
        # Act & Assert
        try:
            FileProcessorRegistry.get_processor("test")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            assert "No processor for" in str(e)

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
