from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", env_file_encoding="utf-8", extra="ignore")
    openai_api_key: SecretStr = Field(default=..., alias="OPENAI_API_KEY")
    embeddings_model: str = Field(default=..., alias="EMBEDDINGS_MODEL")
    chunk_size: int = Field(
        default=500,
        alias="CHUNK_SIZE",
    )
    chunk_overlap: int = Field(default=50, alias="CHUNK_OVERLAP")


config = Config()
