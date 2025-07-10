from typing import Optional


def build_database_url(
    database_url: str,
    dialect: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
) -> str:
    """Build a database connection URL from CLI arguments."""
    if username and password:
        return f"{dialect}://{username}:{password}@{database_url}"
    return f"{dialect}://{database_url}"
