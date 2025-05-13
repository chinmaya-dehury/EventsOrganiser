


import logging
logging.basicConfig(level=logging.INFO, 
                format='%(levelname)s %(asctime)s %(message)s', 
                datefmt='%m/%d/%Y %I:%M:%S %p %Z')
import time
import threading
from sqlalchemy import select, func
from typing import Callable
from dataclasses import dataclass

import server_config, db
from common import tables
from modules import parser, validator, user_listener

@dataclass
class ThreadModule:
    thread_instance: threading.Thread
    thread_constructor: Callable[[], threading.Thread]


THREADS: list[ThreadModule] = [
    ThreadModule(None, parser.ParserThread),
    ThreadModule(None, validator.EventValidatorThread),
    ThreadModule(None, user_listener.UserListener),
]

def create_default_categories():
    with db.start_session() as db_session:
        for category_name in server_config.DEFAULT_EVENT_CATEGORIES:
            q = select(tables.TagsTable) \
                .where(func.lower(tables.TagsTable.name) == func.lower(category_name))
            query_result = db_session.execute(q).scalar_one_or_none()
            if(query_result == None):
                new_category = tables.TagsTable()
                new_category.name = category_name
                db_session.add(new_category)

        db_session.commit()

class PrivateEventsServer():
    def __init__(self):
        self.__logger = logging.getLogger(__name__ + "." + type(self).__name__)

    def run(self):
        self.__logger.info("Creating default categories in database")
        create_default_categories()

        for i in range(len(THREADS)):
            THREADS[i].thread_instance = THREADS[i].thread_constructor()
            THREADS[i].thread_instance.daemon = True
            THREADS[i].thread_instance.start()

        self.__logger.info("Server started")

        while True:
            for i in range(len(THREADS)):
                if(not THREADS[i].thread_instance.is_alive()):
                    self.__logger.warning(f"{THREADS[i].thread_constructor.__name__} unexpectedly crashed, restarted it")

                    THREADS[i].thread_instance = THREADS[i].thread_constructor()
                    THREADS[i].thread_instance.daemon = True
                    THREADS[i].thread_instance.start()

            time.sleep(5)


if __name__ == "__main__":
    server = PrivateEventsServer()
    server.run()