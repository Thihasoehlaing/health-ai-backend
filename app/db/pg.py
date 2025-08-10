from collections.abc import Generator
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session
from sqlalchemy import create_engine
from app.config import settings

class Base(DeclarativeBase):
    pass

engine = create_engine(
    settings.postgres_url,
    pool_pre_ping=True,
    echo=(settings.APP_ENV == "dev"),
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False,
    expire_on_commit=False,
    class_=Session,
)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def dispose_engine() -> None:
    """Optional: call on shutdown in tests to fully close the pool."""
    engine.dispose()
