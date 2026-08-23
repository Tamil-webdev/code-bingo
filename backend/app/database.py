"""
Async database engine and session management for SQLAlchemy.
"""

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect, text
from sqlalchemy.engine import make_url
from app.config import settings

# Create async engine
engine_options = {"echo": False, "pool_pre_ping": True}
if make_url(settings.DATABASE_URL).get_backend_name() != "sqlite":
    engine_options.update(pool_size=20, max_overflow=10)

engine = create_async_engine(settings.DATABASE_URL, **engine_options)

# Session factory
async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""
    pass


async def get_db() -> AsyncSession:
    """Dependency that provides an async database session."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Lightweight compatibility migration for existing local databases.
        tournament_columns = await conn.run_sync(
            lambda sync_conn: {column["name"] for column in inspect(sync_conn).get_columns("tournaments")}
        )
        if "room_code" not in tournament_columns:
            await conn.execute(text("ALTER TABLE tournaments ADD COLUMN room_code VARCHAR(12)"))
        team_columns = await conn.run_sync(
            lambda sync_conn: {column["name"] for column in inspect(sync_conn).get_columns("teams")}
        )
        if "tournament_id" not in team_columns:
            await conn.execute(text("ALTER TABLE teams ADD COLUMN tournament_id UUID"))
        await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_tournaments_room_code ON tournaments (room_code)"))
        # SQLite creates the current schema directly. The PostgreSQL migration
        # keeps existing Docker deployments compatible with the Firebase column.
        if conn.dialect.name != "sqlite":
            await conn.execute(
                text("ALTER TABLE users ADD COLUMN IF NOT EXISTS firebase_uid VARCHAR(128)")
            )
            await conn.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS ix_users_firebase_uid ON users (firebase_uid)"
                )
            )
