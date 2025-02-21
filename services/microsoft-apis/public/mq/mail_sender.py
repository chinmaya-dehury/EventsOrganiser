import asyncio, json
import sqlalchemy.exc
from sqlalchemy import select
from zoneinfo import ZoneInfo
from dataclasses import dataclass

import aio_pika

from common import tables

import db
import logging

@dataclass
class ParseMailsRequest:
    user_id: str
    user_email: str
    user_timezone: ZoneInfo
    email: dict[str]

class MailSenderMQ:
    def __init__(self, host: str, virtual_host: str, username: str, password: str, queue_name: str):
        self.__logger = logging.getLogger(__name__)
        self.__retry_conn_task = None

        self._ioloop = asyncio.get_running_loop()
        self._mq_conn_coroutine = aio_pika.connect_robust(
            host=host,
            virtualhost=virtual_host,
            login=username,
            password=password
        )

        self.mq_connection = None
        self.mq_channel = None
        self.email_parsing_queue = queue_name

    async def try_open_conn_indefinite(self):
        """
        Tries to open an initial connection with RabbitMQ. If it fails, a task will be created to retry opening connection indefinitely.
        """
        try:
            await self.open_conn()
        except:
            self.__logger.warning("Failed to open NotificationMQ connection, trying again later", exc_info=True)
            self.__retry_conn_task = asyncio.create_task(self.try_open_conn_indefinite())

    async def open_conn(self):
        self.mq_connection = await self._mq_conn_coroutine
        self.mq_channel = await self.mq_connection.channel(publisher_confirms=False)

        await self.mq_channel.declare_queue(
            name=self.email_parsing_queue,
            durable=True
        )

    async def close_conn(self):
        if(not self.mq_connection.is_closed):
            await self.mq_connection.close()  

    async def send_new_emails_to_parse(
        self,
        requests: list[ParseMailsRequest]
    ):
        async with self.mq_channel.transaction():
            for data in requests:
                await self.mq_channel.default_exchange.publish(
                    message=aio_pika.Message(
                        body=json.dumps({
                            "user_id": data.user_id,
                            "account_type": "outlook",
                            "user_timezone": str(data.user_timezone),
                            "email_data": data.email,
                            "reader_email": data.user_email
                        }).encode(),
                        delivery_mode=aio_pika.DeliveryMode.PERSISTENT
                    ),
                    routing_key=self.email_parsing_queue
                )
