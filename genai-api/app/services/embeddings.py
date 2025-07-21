from langchain_openai import OpenAIEmbeddings

from app.config import Config


async def get_embeddings(text: str, config: Config) -> list[float]:
    embeddings = OpenAIEmbeddings(model=config.embeddings_model)
    return await embeddings.aembed_query(text)
