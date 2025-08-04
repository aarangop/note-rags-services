from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings


def build_database_url(
    database_url: str,
    dialect: str,
    username: str | None = None,
    password: str | None = None,
) -> str:
    """Build a database connection URL from CLI arguments."""
    if username and password:
        return f"{dialect}://{username}:{password}@{database_url}"
    return f"{dialect}://{database_url}"


class DBConfig(BaseSettings):
    db_url: str = Field(description="Database url")
    db_user: str = Field(description="Database username")
    db_password: SecretStr = Field(description="Database password")
    db_name: str = Field(description="Database name")
    db_dialect: str = Field(description="Database dialect")
    db_driver: str = Field(description="Database driver")

    def get_db_url(self):
        return f"{self.db_dialect}{'+' if self.db_driver else ''}://{self.db_user}:{self.db_password}@{self.db_url}/{self.db_name}"
