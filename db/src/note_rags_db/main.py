from pathlib import Path

import click
import psycopg2
from alembic import command
from alembic.config import Config
from psycopg2 import OperationalError
from sqlalchemy.exc import ArgumentError

from note_rags_db.config import build_database_url
from note_rags_db.db import Base, create_db_engine

# Import models so they get registered with Base
from note_rags_db.schemas import Document, DocumentChunk  # noqa: F401


def get_alembic_config(
    database_url: str, dialect: str, username: str | None = None, password: str | None = None
) -> Config:
    """Get Alembic configuration with the correct database URL."""
    # Get the path to the alembic.ini file
    current_dir = Path(__file__).parent
    alembic_ini_path = current_dir.parent.parent / "alembic.ini"

    # Create Alembic config
    alembic_cfg = Config(str(alembic_ini_path))

    # Set the database URL
    db_url = build_database_url(database_url, dialect, username, password)
    alembic_cfg.set_main_option("sqlalchemy.url", db_url)

    return alembic_cfg


def run_init_sql(
    database_url: str,
    dialect: str,
    username: str | None = None,
    password: str | None = None,
):
    """Run the init.sql script to set up pgvector extension."""
    # Get the path to the init.sql file
    current_dir = Path(__file__).parent
    init_sql_path = current_dir.parent.parent / "scripts" / "init.sql"

    if not init_sql_path.exists():
        print(f"Warning: init.sql not found at {init_sql_path}")
        return

    # Read the SQL script
    with open(init_sql_path) as f:
        sql_script = f.read()

    # Parse the database URL to get connection parameters
    if dialect.startswith("postgresql"):
        # Extract host, port, and database from database_url (format: host:port/database)
        if "/" in database_url:
            host_port, database = database_url.split("/", 1)
        else:
            host_port = database_url
            database = "postgres"  # default database

        if ":" in host_port:
            host, port = host_port.split(":", 1)
        else:
            host = host_port
            port = "5432"  # default port

        try:
            # Connect directly with psycopg2 to run the extension creation
            conn = psycopg2.connect(
                host=host, port=port, database=database, user=username, password=password
            )
            conn.autocommit = True

            with conn.cursor() as cursor:
                cursor.execute(sql_script)
                print("Successfully executed init.sql (pgvector extension created)")

            conn.close()

        except Exception as e:
            print(f"Warning: Could not run init.sql script: {e}")
            print("You may need to manually create the pgvector extension")


def init(
    database_url: str,
    dialect: str,
    username: str | None = None,
    password: str | None = None,
):
    """Initialize the database by creating all SQLAlchemy tables."""
    try:
        # First, run the init.sql script to set up pgvector extension
        print("Setting up database extensions...")
        run_init_sql(database_url, dialect, username, password)

        # Then create the SQLAlchemy tables
        print("Creating database tables...")
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
@click.option("--database-url", required=True, help="Database URL (e.g., localhost:5432/mydb)")
@click.option("--dialect", default="postgresql+psycopg2", help="Database dialect")
@click.option("--username", help="Database username")
@click.option("--password", help="Database password")
def init_command(database_url: str, dialect: str, username: str | None, password: str | None):
    """Initialize the database for first-time setup."""
    try:
        init(database_url, dialect, username, password)
        click.echo("Database initialized successfully!")
    except OperationalError as e:
        print(f"Database operational error: {e}")
    except Exception as e:
        click.echo(f"Failed to initialize database: {e}")


@click.command()
@click.option("--database-url", required=True, help="Database URL (e.g., localhost:5432/mydb)")
@click.option("--dialect", default="postgresql+psycopg2", help="Database dialect")
@click.option("--username", help="Database username")
@click.option("--password", help="Database password")
def upgrade_command(database_url: str, dialect: str, username: str | None, password: str | None):
    """Upgrade database to latest schema using migrations."""
    try:
        # First, run the init.sql script to ensure pgvector extension exists
        print("Setting up database extensions...")
        run_init_sql(database_url, dialect, username, password)

        # Then run migrations
        print("Running database migrations...")
        alembic_cfg = get_alembic_config(database_url, dialect, username, password)
        command.upgrade(alembic_cfg, "head")
        click.echo("Database upgraded successfully!")
    except Exception as e:
        click.echo(f"Failed to upgrade database: {e}")


@click.group()
def cli():
    """Note RAGs Database CLI."""


# Add commands to the CLI group
cli.add_command(init_command, name="init")
cli.add_command(upgrade_command, name="upgrade")


if __name__ == "__main__":
    cli()
