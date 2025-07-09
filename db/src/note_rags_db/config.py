from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Config(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    url: str = Field(default=..., alias="URL")
    user: str = Field(default=..., alias="USER")
    password: SecretStr = Field(default=..., alias="PASSWORD")
    dialect: str = Field(default="postgresql+psycopg2", alias="DIALECT")

    def get_url(self):
        return f"{self.dialect}://{self.user}:{self.password.get_secret_value()}@{self.url}"


config = Config()
