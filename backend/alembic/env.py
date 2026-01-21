import os
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.db.base import Base
from app.db import models

# Alembic Config object, which provides access to values within alembic.ini
config = context.config

# Metadata used by Alembic for autogenerate (diffing models vs DB schema)
target_metadata = Base.metadata

def get_url() -> str:
    """
    Resolve the database URL for migrations.

    Priority:
    1) POSTGRES_DSN environment variable (preferred in Docker / deployments)
    2) sqlalchemy.url value in alembic.ini (fallback for local dev)

    Returns:
        str: SQLAlchemy database URL / DSN string.
    """
    return os.getenv("POSTGRES_DSN", config.get_main_option("sqlalchemy.url"))


def run_migrations_offline() -> None:
    """
    Run migrations in "offline" mode.

    Offline mode does NOT create a DB connection.
    Instead, Alembic generates SQL statements directly.

    literal_binds=True means values are rendered directly into the SQL string,
    rather than being passed as bind parameters.
    """
    url = get_url()

    # Configure Alembic context for offline migration generation.
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
    )

    # Wrap migration operations in a transaction block.
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """
    Run migrations in "online" mode.
    Online mode DOES create a DB connection and applies migrations directly.
    """
    # Pull config section from alembic.ini
    cfg = config.get_section(config.config_ini_section) or {}

    # Ensure the DB URL is set dynamically.
    cfg["sqlalchemy.url"] = get_url()

    # Create an Engine using Alembic's configuration helper.
    # NullPool avoids connection pooling during migrations.
    connectable = engine_from_config(
        cfg,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    # Open a connection and run migrations.
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


# Decide whether we are running offline or online migrations.
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
