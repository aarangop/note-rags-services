from pathlib import Path

import click
import psycopg2
from alembic import command
from alembic.config import Config
from psycopg2 import OperationalError
from sqlalchemy.exc import ArgumentError


def get_alembic_config(database_url: str) -> Config:
    """Get Alembic configuration with the correct database URL."""
    # Get the path to the alembic.ini file
    current_dir = Path(__file__).parent
    alembic_ini_path = current_dir.parent.parent / "alembic.ini"

    # Create Alembic config
    alembic_cfg = Config(str(alembic_ini_path))

    # Set the database URL
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)

    return alembic_cfg


def run_sql(database_url: str, sql_string: str, autocommit: bool = True):
    conn = psycopg2.connect(database_url)
    conn.autocommit = autocommit
    try:
        with conn.cursor() as cursor:
            cursor.execute(sql_string)
        print(
            f"Successfully executed sql: {sql_string[:100]}{'...' if len(sql_string) > 100 else ''}"
        )
    except Exception as e:
        raise e from e
    finally:
        conn.close()


def run_init_sql(
    database_url: str,
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

    try:
        # Connect directly with psycopg2 to run the extension creation
        run_sql(database_url, sql_script, autocommit=True)
        print("Successfully executed init.sql:\n")
        print(sql_script)
    except Exception as e:
        raise e from e


def init(database_url: str):
    """Initialize the database by creating all SQLAlchemy tables."""
    try:
        # First, run the init.sql script to set up pgvector extension
        print("Setting up database extensions...")
        run_init_sql(database_url)
    except ArgumentError as e:
        print(e._message)
    except Exception as e:
        print(f"Exception initiating database: {e}")
        raise e


@click.command()
@click.option("--database-url", required=True, help="Database URL (e.g., localhost:5432/mydb)")
def init_command(database_url: str):
    """Initialize the database for first-time setup."""
    try:
        init(database_url)
        click.echo("Database initialized successfully!")
    except OperationalError as e:
        print(f"Database operational error: {e}")
    except Exception as e:
        click.echo(f"Failed to initialize database: {e}")


@click.command()
@click.option("--database-url", required=True, help="Database URL (e.g., localhost:5432/mydb)")
def upgrade_command(database_url: str):
    """Upgrade database to latest schema using migrations."""
    try:
        # First, run the init.sql script to ensure pgvector extension exists
        print("Setting up database extensions...")
        run_init_sql(database_url)

        # Then run migrations
        print("Running database migrations...")
        alembic_cfg = get_alembic_config(database_url)
        command.upgrade(alembic_cfg, "head")
        click.echo("Database upgraded successfully!")
    except Exception as e:
        click.echo(f"Failed to upgrade database: {e}")


@click.command()
@click.option("--database-url", required=True, help="Database URL (e.g., localhost:5432/mydb)")
def reset(database_url: str):
    """Reset database, reverting all migrations and dropping the alembic_version table"""
    try:
        alembic_cfg = get_alembic_config(database_url)
        command.downgrade(alembic_cfg, "base")
        # Drop database migration table, to make it seem as if it was never migrated
        run_sql(database_url, "DROP TABLE IF EXISTS alembic_version")
    except Exception as e:
        raise e from e


@click.group()
def cli():
    """Note RAGs Database CLI."""


# Add commands to the CLI group
cli.add_command(init_command, name="init")
cli.add_command(upgrade_command, name="upgrade")
cli.add_command(reset, name="reset")


if __name__ == "__main__":
    cli()
