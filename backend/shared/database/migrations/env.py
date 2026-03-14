"""
KOROBOS — Second Brain Operating System

Copyright (c) 2026 Saravana Perumal K

Licensed under the GNU Affero General Public License v3.

Alembic environment configuration for async PostgreSQL migrations.
"""

import asyncio
import importlib
import importlib.util
import os
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# -- Ensure the project root is on sys.path --
# This allows importing from backend.shared and the service model modules.
PROJECT_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "..")
)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from backend.shared.database.base_model import Base  # noqa: E402

# -- Import ALL service models so Base.metadata picks them up --
# Every model that inherits from Base must be imported here for autogenerate.
# The try/except blocks allow running even if some services aren't installed.

_model_imports = [
    "backend.services.auth-service.app.models.model",
    "backend.services.notes-service.app.models.model",
    "backend.services.habit-service.app.models.model",
    "backend.services.learning-service.app.models.model",
    "backend.services.health-service.app.models.model",
    "backend.services.analytics-service.app.models.model",
    "backend.services.notification-service.app.models.model",
    "backend.services.ai-service.app.models.model",
]

for _mod_path in _model_imports:
    # Convert hyphenated paths to filesystem-style imports
    # Since Python doesn't allow hyphens, we use importlib to load by path
    _parts = _mod_path.split(".")
    _service_dir = _parts[2]  # e.g. "auth-service"
    _fs_path = os.path.join(
        PROJECT_ROOT, "backend", "services", _service_dir, "app", "models", "model.py"
    )
    if os.path.exists(_fs_path):
        spec = importlib.util.spec_from_file_location(
            f"{_service_dir}.models", _fs_path
        )
        if spec and spec.loader is not None:
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)

# Alembic Config object
config = context.config

# Set up loggers from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# MetaData target for autogenerate support — all models must inherit from Base
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """
    Run migrations in 'offline' mode.

    Generates SQL scripts without connecting to the database.
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Run migrations against a live connection."""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Run migrations in 'online' mode using an async engine.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migrations — delegates to async runner."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
