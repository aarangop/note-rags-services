from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    db_url: str = Field(default=..., alias="DB_URL")

    db_username: str = Field(default=..., alias="DB_USERNAME")

    db_password: str = Field(default=..., alias="DB_PASSWORD")

    db_driver: str = "asyncpg"

    openai_api_key: SecretStr = Field(default=..., alias="OPENAI_API_KEY")

    chunk_size: int = Field(
        default=500,
        alias="CHUNK_SIZE",
    )

    chunk_overlap: int = Field(default=50, alias="CHUNK_OVERLAP")

    def get_db_connection_string(self):
        return f"postgresql+{self.db_driver}://{self.db_username}:{self.db_password}@{self.db_url}"


config = Config()
