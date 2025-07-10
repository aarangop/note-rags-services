from typing import Optional

import click
from psycopg2 import OperationalError
from sqlalchemy.exc import ArgumentError

from note_rags_db.config import build_database_url
from note_rags_db.db import Base, create_db_engine

# Import models so they get registered with Base
from note_rags_db.schemas import document  # noqa: F401


def init(
    database_url: str,
    dialect: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
):
    """Initialize the database by creating all SQLAlchemy tables."""
    try:
        db_url = build_database_url(database_url, dialect, username, password)
        engine = create_db_engine(db_url)
        Base.metadata.create_all(engine)
        table_names = list(Base.metadata.tables.keys())
        if table_names:
            print(f"Database tables created successfully: {', '.join(table_names)}")
        else:
            print("No tables were created (no models found)")
    except ArgumentError as e:
        print(e._message)
    except Exception as e:
        print(f"Exception initiating database: {e}")
        raise e


@click.command()
@click.option(
    "--database-url", required=True, help="Database URL (e.g., localhost:5432/mydb)"
)
@click.option("--dialect", default="postgresql+psycopg2", help="Database dialect")
@click.option("--username", help="Database username")
@click.option("--password", help="Database password")
def init_command(
    database_url: str, dialect: str, username: Optional[str], password: Optional[str]
):
    """Initialize the database."""
    try:
        init(database_url, dialect, username, password)
        click.echo("Database initialized successfully!")
    except OperationalError as e:
        print(f"Database operational error: {e}")
    except Exception as e:
        click.echo(f"Failed to initialize database: {e}")


@click.group()
def cli():
    """Note RAGs Database CLI."""
    pass


# Add commands to the CLI group
cli.add_command(init_command, name="init")


if __name__ == "__main__":
    cli()
