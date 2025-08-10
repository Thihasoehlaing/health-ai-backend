from logging.config import fileConfig
from alembic import context
from sqlalchemy import engine_from_config, pool
import os
import sys
from pathlib import Path

# --- Ensure 'app' is importable no matter where alembic is run from ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]  # points to your project root
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Alembic Config
config = context.config
if config.config_file_name:
    fileConfig(config.config_file_name)

# Build DB URL from app settings
from app.config import settings
db_url = settings.postgres_url
config.set_main_option("sqlalchemy.url", db_url)

# Import models' metadata
from app.db.pg import Base
# Import all models so metadata is populated
from app.models import department, doctor, patient, appointment, faq, admin, kiosk_device, audit_log

target_metadata = Base.metadata

def run_migrations_offline():
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            compare_server_default=True,
        )
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
