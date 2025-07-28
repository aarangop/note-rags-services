import datetime
import os
import re
import tempfile
from abc import ABC, abstractmethod
from typing import Any

import yaml
from langchain_community.document_loaders import PyPDFLoader


def date_constructor(loader, node):
    """Custom YAML constructor to convert dates to ISO format strings."""
    value = loader.construct_yaml_timestamp(node)
    if isinstance(value, datetime.date | datetime.datetime):
        return value.isoformat()
    return value


def setup_yaml_loader():
    """Set up YAML loader with custom date handling."""

    # Create a custom SafeLoader class
    class JSONSerializableLoader(yaml.SafeLoader):
        pass

    # Add constructor for timestamp tags to convert dates to ISO strings
    JSONSerializableLoader.add_constructor("tag:yaml.org,2002:timestamp", date_constructor)

    return JSONSerializableLoader


class FileProcessingError(Exception):
    pass


class MetadataProcessingError(FileProcessingError):
    pass


class FileProcessor(ABC):
    @abstractmethod
    def parse_content(self, content: bytes) -> tuple[str, dict[str, Any]]:
        raise NotImplementedError()


class MarkdownFileProcessor(FileProcessor):
    def extract_metadata(self, content: str) -> tuple[str, dict | None]:
        # Extract frontmatter between --- delimiters
        frontmatter_match = re.match(r"^---\s*\n(.*?)\n---\s*\n", content, re.DOTALL)
        if frontmatter_match:
            frontmatter_content = frontmatter_match.group(1)
            try:
                # Use custom loader to handle dates as ISO strings
                loader_class = setup_yaml_loader()
                metadata = yaml.load(frontmatter_content, Loader=loader_class) or {}
                # Remove frontmatter from content
                content = content[frontmatter_match.end() :]
                return content, metadata
            except yaml.YAMLError as e:
                # If YAML parsing fails, just continue with empty metadata
                raise FileProcessingError("Failed to extract metadata") from e
        return content, None

    def parse_content(self, content: bytes) -> tuple[str, dict[str, Any]]:
        # Try multiple encodings to handle different file encodings gracefully
        encodings_to_try = ["utf-8", "utf-8-sig", "latin-1", "windows-1252", "iso-8859-1"]

        content_str = None
        for encoding in encodings_to_try:
            try:
                content_str = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue

        if content_str is None:
            # If all encodings fail, use 'utf-8' with error handling
            content_str = content.decode("utf-8", errors="replace")

        content_str, metadata = self.extract_metadata(content_str)

        return content_str, metadata if metadata else {}


class PDFFileProcessor(FileProcessor):
    def parse_content(self, content: bytes) -> tuple[str, dict[str, Any]]:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
            temp_file.write(content)
            temp_path = temp_file.name
        try:
            loader = PyPDFLoader(temp_path)
            pages = loader.load()
            text = "\n".join([page.page_content for page in pages])
            metadata = {"pages": len(pages), "source": temp_path}
            if pages:
                metadata.update(pages[0].metadata)
            return text, metadata
        finally:
            os.unlink(temp_path)


class FileProcessorRegistry:
    _processors: dict[str, type[FileProcessor]] = {}

    @classmethod
    def register_extensions(cls, extensions: list[str], processor_class: type[FileProcessor]):
        for ext in extensions:
            cls._processors[ext] = processor_class

    @classmethod
    def register_extension(cls, extension: str, processor_class: type[FileProcessor]):
        cls._processors[extension] = processor_class

    @classmethod
    def get_processor(cls, filename: str) -> FileProcessor:
        ext = os.path.splitext(filename)[1]
        if ext not in cls._processors:
            raise ValueError(f"No processor for {ext}")
        processor_class = cls._processors[ext]
        return processor_class()


FileProcessorRegistry.register_extension(".md", MarkdownFileProcessor)
FileProcessorRegistry.register_extension(".pdf", PDFFileProcessor)
