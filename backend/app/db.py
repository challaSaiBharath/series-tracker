"""Database engine and session. SQLite by default; PostgreSQL by changing DATABASE_URL (Week 2)."""
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.core.config import settings


def make_engine(url: str):
    kwargs = {}
    if url.startswith("sqlite"):
        # FastAPI runs sync endpoints in a thread pool, so SQLite must allow that.
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


engine = make_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db():
    # Looks up SessionLocal at call time so tests can swap it.
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def ensure_columns(bind) -> list[str]:
    """Stop-gap: add new nullable columns to tables that already exist (so v0.1 databases keep working).
    Week 2 replaces this with Alembic migrations."""
    added: list[str] = []
    inspector = inspect(bind)
    with bind.begin() as conn:
        for table in Base.metadata.sorted_tables:
            if not inspector.has_table(table.name):
                continue
            existing = {c["name"] for c in inspector.get_columns(table.name)}
            for col in table.columns:
                if col.name in existing:
                    continue
                if not col.nullable:
                    raise RuntimeError(f"Cannot auto-add NOT NULL column {table.name}.{col.name}; write a migration")
                ddl = f'ALTER TABLE "{table.name}" ADD COLUMN "{col.name}" {col.type.compile(bind.dialect)}'
                conn.execute(text(ddl))
                added.append(f"{table.name}.{col.name}")
    return added
