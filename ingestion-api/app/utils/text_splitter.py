from app.config import config
from langchain_text_splitters import RecursiveCharacterTextSplitter


def get_text_splitter():
    return RecursiveCharacterTextSplitter(
        chunk_size=config.chunk_size, chunk_overlap=config.chunk_overlap
    )


def split_text(text: str) -> list[str]:
    text_splitter = get_text_splitter()
    return text_splitter.split_text(text)
