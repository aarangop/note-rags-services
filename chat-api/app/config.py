from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

class Config(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env"
    )

    db_url: str = Field(default=..., alias="DATABASE_URL")
    db_user: str = Field(default=..., alias="DATABASE_USER")
    db_password: SecretStr=Field(default=..., alias="DATABASE_PASSWORD")

    openai_api_key: SecretStr = Field(default=..., alias="OPENAI_API_KEY")

    def get_db_url(self):
        return f"postgresql+asyncpg://{self.db_user}:{self.db_password.get_secret_value()}@{self.db_url}"

config = Config()