import click
from sqlalchemy.exc import ArgumentError

from note_rags_db.db import Base, engine

# Import models so they get registered with Base
from note_rags_db.schemas import document  # noqa: F401


def init():
    """Initialize the database by creating all SQLAlchemy tables."""
    try:
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


@click.command()
def init_command():
    """Initialize the database."""
    init()
    click.echo("Database initialized successfully!")


@click.group()
def cli():
    """Note RAGs Database CLI."""
    pass


# Add commands to the CLI group
cli.add_command(init_command, name="init")


if __name__ == "__main__":
    cli()
