from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    openai_api_key: SecretStr = Field(default=..., alias="OPENAI_API_KEY")
    embeddings_model: str = Field(default=..., alias="EMBEDDINGS_MODEL")


config = Config()


def get_config(reset: bool = False) -> Config:
    global config
    if not config or (config and reset):
        config = Config()

    return config


def reset_config():
    global config
    config = Config()
