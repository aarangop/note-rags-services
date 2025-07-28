import os
import re
import tempfile
from abc import ABC, abstractmethod
from typing import Any

import yaml
from langchain_community.document_loaders import PyPDFLoader


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
                metadata = yaml.safe_load(frontmatter_content) or {}
                # Remove frontmatter from content
                content = content[frontmatter_match.end() :]
                return content, metadata
            except yaml.YAMLError as e:
                # If YAML parsing fails, just continue with empty metadata
                raise FileProcessingError("Failed to extract metadata") from e
        return content, None

    def parse_content(self, content: bytes) -> tuple[str, dict[str, Any]]:
        content_str = content.decode("utf-8")
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
