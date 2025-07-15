from langchain_openai import OpenAIEmbeddings

from app.config import config


def get_embeddings_model() -> OpenAIEmbeddings:
    return OpenAIEmbeddings(model=config.embeddings_model, api_key=config.openai_api_key)


async def get_embeddings(chunks: list[str]) -> list[list[float]]:
    embeddings_model = get_embeddings_model()
    return await embeddings_model.aembed_documents(chunks)
