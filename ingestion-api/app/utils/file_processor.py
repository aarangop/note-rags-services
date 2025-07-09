import os
import tempfile
from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple, Type

from langchain_community.document_loaders import PyPDFLoader


class FileProcessor(ABC):
    @abstractmethod
    def extract_text(self, content: bytes) -> Tuple[str, Dict[str, Any]]:
        raise NotImplementedError()


class MarkdownFileProcessor(FileProcessor):
    def extract_text(self, content: bytes) -> Tuple[str, Dict[str, Any]]:
        # TODO: Extract metadata from frontmatter
        metadata: Dict[str, Any] = {}
        return content.decode("utf-8"), metadata


class PDFFileProcessor(FileProcessor):
    def process(self, content: bytes) -> Tuple[str, Dict[str, Any]]:
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
    _processors: dict[str, Type[FileProcessor]] = {}

    @classmethod
    def register_extensions(
        cls, extensions: list[str], processor_class: Type[FileProcessor]
    ):
        for ext in extensions:
            cls._processors[ext] = processor_class

    @classmethod
    def register_extension(cls, extension: str, processor_class: Type[FileProcessor]):
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
