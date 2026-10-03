import asyncio
from typing import AsyncGenerator
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import declarative_base

from app.core.config import settings
from app.core.logging import logger

Base = declarative_base()

_engine = None
_session_factory = None
_db_lock = asyncio.Lock()
_using_sqlite_fallback = False


def _create_engine_for_url(url: str):
    if "sqlite" in url:
        return create_async_engine(
            url,
            echo=settings.DEBUG,
            future=True,
            connect_args={"check_same_thread": False},
        )
    return create_async_engine(
        url,
        echo=settings.DEBUG,
        future=True,
        pool_pre_ping=True,
        connect_args={"timeout": 1.5} if "asyncpg" in url else {},
    )


async def init_db():
    """
    Initialize database connection.
    Attempts configured PostgreSQL first; if unreachable, falls back to local SQLite.
    """
    global _engine, _session_factory, _using_sqlite_fallback

    if _engine is not None:
        return _engine

    async with _db_lock:
        if _engine is not None:
            return _engine

        # Test connecting to configured DATABASE_URL
        primary_url = settings.DATABASE_URL
        test_engine = _create_engine_for_url(primary_url)

        try:
            async with test_engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            _engine = test_engine
            _session_factory = async_sessionmaker(
                bind=_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )
            logger.info("Connected to primary database successfully.")
        except Exception as e:
            logger.warning(
                f"PostgreSQL at '{primary_url}' is not reachable ({e}). "
                "Automatically activating local SQLite fallback (claudinary.db) for zero-downtime development."
            )
            await test_engine.dispose()
            _using_sqlite_fallback = True
            sqlite_url = "sqlite+aiosqlite:///./claudinary.db"
            _engine = _create_engine_for_url(sqlite_url)
            _session_factory = async_sessionmaker(
                bind=_engine,
                class_=AsyncSession,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
            )

            # Auto-create all tables in fallback SQLite
            from app.db.models import Base
            async with _engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Local SQLite database initialized with all tables.")

        return _engine


async def get_session_factory():
    if _session_factory is None:
        await init_db()
    return _session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency yielding an async database session per request.
    """
    factory = await get_session_factory()
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()
