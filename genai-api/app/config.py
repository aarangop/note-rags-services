from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file="../.env", extra="ignore")

    db_url: str = Field(default=..., alias="DB_URL")
    db_user: str = Field(default=..., alias="DB_USERNAME")
    db_password: SecretStr = Field(default=..., alias="DB_PASSWORD")

    openai_api_key: SecretStr = Field(default=..., alias="OPENAI_API_KEY")
    embeddings_model: str = Field(default=..., alias="EMBEDDINGS_MODEL")

    def get_db_url(self):
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password.get_secret_value()}@{self.db_url}"


config = Config()


def get_config(reset: bool = False) -> Config:
    global config
    if not config or (config and reset):
        config = Config()

    return config


def reset_config():
    global config
    config = Config()
