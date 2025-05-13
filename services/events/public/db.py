import asyncio

from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from asyncio import current_task
import os

import server_config

import sys
sys.path.append('..')
from common.tables import Base

url = URL.create(
    drivername="mysql+aiomysql",
    username=server_config.MYSQL_EVENTS_USER,
    password=server_config.MYSQL_EVENTS_PASSWORD,
    host=server_config.MYSQL_HOST,
    database="events",
    port=3306
)
engine = create_async_engine(url)
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

async def create_tables() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# sometimes an event loop already exists, depending on how you run the program
try:
    loop = asyncio.get_running_loop()
    loop.create_task(create_tables())
except RuntimeError:
    asyncio.run(create_tables())

async def start_session():
    async with async_session() as session:
        yield session