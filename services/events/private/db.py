from contextlib import contextmanager

from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy import create_engine

import sys
sys.path.append('..')
from common import models, tables

import server_config

url = URL.create(
    drivername="mysql+pymysql",
    username=server_config.MYSQL_EVENTS_USER,
    password=server_config.MYSQL_EVENTS_PASSWORD,
    host=server_config.MYSQL_HOST,
    database="events",
    port=3306
)
engine = create_engine(url)
session = sessionmaker(
    engine, expire_on_commit=False
)

tables.Base.metadata.create_all(engine)

@contextmanager
def start_session():
    with session() as sess:
        yield sess