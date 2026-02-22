import logging
from os import environ, makedirs
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from database.db_classes import *

logger = logging.getLogger('Database')

_database_path = environ.get("DATABASE_PATH", "muppets.sqlite")
if _database_path != ":memory:" and not Path(_database_path).is_absolute():
    _database_path = str(Path.cwd() / _database_path)
engine = create_async_engine(
    f"sqlite+aiosqlite:///{_database_path}",
    echo=False,
    connect_args={"check_same_thread": False},
)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)


async def init_database():
    logger.info("Initializing database...")
    db_path = Path(_database_path)
    if db_path != Path("-") and not str(_database_path).startswith(":memory:"):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
