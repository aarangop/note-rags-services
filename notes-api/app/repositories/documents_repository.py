from abc import ABC, abstractmethod

from app.models.document import BaseDocument


class DocumentsRepository(ABC):
    @abstractmethod
    def save(self, document: BaseDocument) -> BaseDocument:
        pass

    @abstractmethod
    def find_by_id(self, doc_id: int) -> BaseDocument | None:
        pass

    @abstractmethod
    def find_by_title(self, title: int) -> BaseDocument | None:
        pass
