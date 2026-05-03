import dotenv
import os
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool
from loguru import logger


dotenv.load_dotenv()
DEV_DB_URL = os.getenv("DEV_DB_URL")


engine = create_async_engine(
    url=DEV_DB_URL,
    poolclass=NullPool,
    #echo=True
)
async_session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

@asynccontextmanager
async def get_db():
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            raise
        finally:
            await session.close()

