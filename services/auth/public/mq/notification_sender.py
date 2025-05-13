import asyncio, json
import aio_pika
from dataclasses import dataclass
import functools
import logging
from typing import Callable, Awaitable
from datetime import datetime
from zoneinfo import ZoneInfo

@dataclass
class NotificationListener:
     queue_name: str
     routing_key: str
     notification_callback: Callable[[dict], Awaitable[bool]]

class NotificationMQ:
    def __init__(self, host: str, virtual_host: str, username: str, password: str, listeners: list[NotificationListener]):
        """
        Creates an instance of a MQ client listening for notifications on 'queue_name' that are routed there with 'routing_key'

        :param host: IP of the broker
        :param virtual_host: Virtual host name
        :param username: Broker login username
        :param password: Broker login password
        :param listeners: A list of the endpoints that determines where notifications should be sent.
            Each item makes RabbitMQ create a new queue "queue_name" and binds the notification exchange to the queue with "routing_key"
            On a new message, notification_callback gets called with message data
        :param routing_key: Defines which type of notifications in RabbitMQ to send to a queue defined by 'queue_name'
        :queue_name: Queue to receive certain notifications on
        :param notification_callback: An async function that gets called on a new notification. 
            The callback must take a dictionary and return a bool value (True indicating that the notification was successfully processed)
        """
        self.__logger = logging.getLogger(__name__)
        self.__retry_conn_task = None

        self.host = host
        self.virtual_host = virtual_host
        self.username = username
        self.password = password

        self.mq_connection = None
        self.mq_channel = None
        self.notification_exchange = None

        self.listeners = listeners

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
        self.mq_connection = await aio_pika.connect_robust(
            host=self.host,
            virtualhost=self.virtual_host,
            login=self.username,
            password=self.password
        )
        self.mq_channel = await self.mq_connection.channel()
        await self.mq_channel.set_qos(prefetch_count=10)

        self.notification_exchange = await self.mq_channel.declare_exchange(name="notifications", type=aio_pika.ExchangeType.TOPIC, durable=True)
        for listener in self.listeners:
            queue = await self.mq_channel.declare_queue(
                name=listener.queue_name,
                durable=True
            )
            await queue.bind(exchange="notifications", routing_key=listener.routing_key)

            _on_notification_with_bound_callback = functools.partial(self._on_notification, process_message_callback=listener.notification_callback)
            await queue.consume(_on_notification_with_bound_callback)

    async def close_conn(self):
        if(self.mq_connection is not None and not self.mq_connection.is_closed):
            await self.mq_connection.close()    

    async def send_notification(self, data: dict, routing_key: str, **kwargs):
        """
        Send a notification through 'notifications' exchange with a routing key

        :param data: Message content to send
        :param routing_key: AMQP routing key for the message
        :param kwargs: Extra arguments for aio_pika.Message
        """
        await self.notification_exchange.publish(
            aio_pika.Message(
                body=json.dumps(data).encode(),
                **kwargs
            ),
            routing_key=routing_key,
        )

    async def _on_notification(self, msg: aio_pika.message.AbstractIncomingMessage,
                               process_message_callback: Callable[[dict], Awaitable[bool]]):
        try:
            data = json.loads(msg.body.decode())
        except json.JSONDecodeError:
            self.__logger.error("Unable to decode new user notification due to a programmer JSON formatting error", exc_info=True, stack_info=True)
            await msg.reject()

        try:
            proc_success = await process_message_callback(data)
            if(proc_success):
                await msg.ack()
            else:
                self.__logger.warning(f"Notification was not processed fully by callback '{getattr(process_message_callback, "__name__", repr(process_message_callback))}'", exc_info=True)
                await msg.nack(requeue=True)
        except Exception:
            self.__logger.warning("Error passing on notification to 'notification_callback'", exc_info=True)
            await msg.nack(requeue=True)

    async def notify_of_ms_login(self, account_id: str, access_token_expiration: datetime, email: str,
                                 user_timezone: ZoneInfo, access_token: str, refresh_token: str):        
        await self.send_notification({
                "account_id": account_id,
                "account_type": "outlook",
                "email": email,
                "user_timezone": str(user_timezone),
                "access_token": access_token,
                "access_token_expiration": access_token_expiration.isoformat(),
                "refresh_token": refresh_token
            },
            "notification.outlook.user_login"
        )
        