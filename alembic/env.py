from __future__ import with_statement
import sys
import os
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy import create_engine
from alembic import context
from database import Base

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config
fileConfig(config.config_file_name)

# Ensure models are imported so metadata is available
import models.user  # noqa: F401
import models.crop  # noqa: F401
import models.daily_log  # noqa: F401
import models.recommendation  # noqa: F401
import models.task  # noqa: F401
import models.verification  # noqa: F401

target_metadata = Base.metadata


def get_url() -> str:
    url = os.getenv("DATABASE_URL", config.get_main_option("sqlalchemy.url"))
    if url.startswith("sqlite:///") and not url.startswith("sqlite:///"):
        # For SQLite, ensure proper path
        pass
    return url

config.set_main_option("sqlalchemy.url", get_url())


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
