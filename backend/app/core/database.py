"""One SQLAlchemy transaction boundary for canonical business facts."""
from collections.abc import Generator
from pathlib import Path
from sqlalchemy import create_engine, event
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker
from sqlalchemy.pool import StaticPool
from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def create_db_engine(database_url: str | None = None):
    url = make_url(database_url or get_settings().database_url)
    options = {}
    if url.get_backend_name() == 'sqlite':
        if url.database and url.database != ':memory:':
            path = Path(url.database)
            if not path.is_absolute():
                path = get_settings().root_dir / path
            path.parent.mkdir(parents=True, exist_ok=True)
            url = url.set(database=str(path))
        else:
            options['poolclass'] = StaticPool
        options['connect_args'] = {'check_same_thread': False, 'timeout': 30}
    bind = create_engine(url, **options)
    if url.get_backend_name() == 'sqlite':
        @event.listens_for(bind, 'connect')
        def sqlite_settings(connection, _):
            cursor = connection.cursor()
            cursor.execute('PRAGMA foreign_keys=ON')
            cursor.execute('PRAGMA journal_mode=WAL')
            cursor.execute('PRAGMA busy_timeout=30000')
            cursor.close()
    return bind


engine = create_db_engine()
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, autoflush=False)


def get_db() -> Generator[Session, None, None]:
    with SessionLocal() as db:
        yield db


def init_db(bind=None) -> None:
    from app import models  # registers only released slice models
    from app.migrations import initialize_schema
    initialize_schema(bind if bind is not None else engine)
