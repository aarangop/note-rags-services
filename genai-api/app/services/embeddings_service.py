from langchain_openai import OpenAIEmbeddings

from app.config import Config


async def get_embeddings(text: str, config: Config) -> list[float]:
    embeddings = OpenAIEmbeddings(model=config.embeddings_model)
    return await embeddings.aembed_query(text)


class EmbeddingsService:
    def __init__(self, model: str):
        self.embeddings = OpenAIEmbeddings(model=model)

    async def get_embeddings(self, text: str):
        return await self.embeddings.aembed_query(text)


def get_embeddings_service(model: str):
    return EmbeddingsService(model)
