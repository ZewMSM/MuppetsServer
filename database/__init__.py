import logging
from os import environ, makedirs
from pathlib import Path

from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

# localmodules:start
from database.db_classes import *
# localmodules:end

logger = logging.getLogger("Database")

# Единственное место с __file__: при запуске из Chaquopy (exec(string)) __file__ нет
try:
    _CONTENT_ROOT = Path(__file__).resolve().parent.parent / "content" / "base_game_data"
except NameError:
    _CONTENT_ROOT = Path.cwd() / "content" / "base_game_data"

_database_path = f'{environ.get("HOME", ".")}/{environ.get("DATABASE_PATH", "zewmsm.db")}'
engine = create_async_engine(
    f'sqlite+aiosqlite:///{environ.get("HOME")}/{environ.get("DATABASE_PATH", "zewmsm.db")}',
    echo=False,
    pool_size=5,
    max_overflow=5,
    pool_timeout=10,
)
Session = async_sessionmaker(bind=engine, expire_on_commit=False)
SessionLocal = Session  # алиас для сборки в один файл (base_adapter использует SessionLocal)


async def init_database():
    logger.info("Initializing database...")
    db_path = Path(_database_path)
    if db_path != Path("-") and not str(_database_path).startswith(":memory:"):
        db_path.parent.mkdir(parents=True, exist_ok=True)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
