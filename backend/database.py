import os
from threading import Lock

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+psycopg2://postgres:postgres@localhost:5432/langchain_app",
)

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)
Base = declarative_base()

_PARENT_CHUNK_SCHEMA_LOCK = Lock()
_PARENT_CHUNK_SCHEMA_READY = False
_PARENT_CHUNK_SCOPE_COLUMNS = {
    "visibility": "ALTER TABLE parent_chunks ADD COLUMN visibility VARCHAR(20) NOT NULL DEFAULT 'public'",
    "owner_id": "ALTER TABLE parent_chunks ADD COLUMN owner_id VARCHAR(100) NOT NULL DEFAULT ''",
    "document_domain": (
        "ALTER TABLE parent_chunks ADD COLUMN document_domain VARCHAR(50) "
        "NOT NULL DEFAULT 'knowledge_base'"
    ),
}
_PARENT_CHUNK_SCOPE_INDEXES = {
    "ix_parent_chunks_visibility": "CREATE INDEX IF NOT EXISTS ix_parent_chunks_visibility ON parent_chunks (visibility)",
    "ix_parent_chunks_owner_id": "CREATE INDEX IF NOT EXISTS ix_parent_chunks_owner_id ON parent_chunks (owner_id)",
    "ix_parent_chunks_document_domain": (
        "CREATE INDEX IF NOT EXISTS ix_parent_chunks_document_domain ON parent_chunks (document_domain)"
    ),
}


def ensure_parent_chunk_schema(bind=None, force: bool = False) -> None:
    global _PARENT_CHUNK_SCHEMA_READY

    current_engine = bind or engine
    if _PARENT_CHUNK_SCHEMA_READY and not force:
        return

    with _PARENT_CHUNK_SCHEMA_LOCK:
        if _PARENT_CHUNK_SCHEMA_READY and not force:
            return

        inspector = inspect(current_engine)
        if not inspector.has_table("parent_chunks"):
            return

        existing_columns = {column["name"] for column in inspector.get_columns("parent_chunks")}
        existing_indexes = {index["name"] for index in inspector.get_indexes("parent_chunks")}

        statements: list[str] = []
        for column_name, statement in _PARENT_CHUNK_SCOPE_COLUMNS.items():
            if column_name not in existing_columns:
                statements.append(statement)
        for index_name, statement in _PARENT_CHUNK_SCOPE_INDEXES.items():
            if index_name not in existing_indexes:
                statements.append(statement)

        if statements:
            with current_engine.begin() as connection:
                for statement in statements:
                    connection.execute(text(statement))

        _PARENT_CHUNK_SCHEMA_READY = True


def init_db() -> None:
    # Delayed import to avoid circular dependency.
    import models  # noqa: F401

    Base.metadata.create_all(bind=engine)
    ensure_parent_chunk_schema(engine)
