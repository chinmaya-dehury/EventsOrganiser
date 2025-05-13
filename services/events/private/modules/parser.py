from sqlalchemy import select, delete, update
import threading, json
import pika, pika.spec, pika.channel
import logging
import functools
from cryptography.fernet import Fernet

from common import tables, models
from helpers.email_data import Email
from llm.model import Llama3Model 
import server_config, db
import os

# This should still work fine with pika andmost LLM libraries, since 
# most of them release the GIL when it comes time to run the LLM with a prompt
class ParserThread(threading.Thread):
    """
    Listens on RabbitMQ new emails queue and parses events from them.

    Uses DB to get the categories of events the user wants to be parsed.
    """
    def __init__(self):
        super(ParserThread, self).__init__()

        self.logger = logging.getLogger(__name__ + "." + type(self).__name__)
        self.mq_connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=server_config.RABBITMQ_HOST, 
                port=5672, 
                virtual_host=server_config.RABBITMQ_VIRTUALHOST, 
                credentials=pika.PlainCredentials(server_config.RABBITMQ_USERNAME, server_config.RABBITMQ_PASSWORD))
        )
        self.mq_channel = self.mq_connection.channel()
        self.mq_channel.basic_qos(prefetch_count=1)

        self.current_work_delivery_tag = None
        self.llm = Llama3Model(server_config.LLM_PATH)

    def to_email_obj(self, msg_with_email: dict[str]) -> Email:
        email_data = msg_with_email["email_data"]
        reader_email = msg_with_email["reader_email"]

        match msg_with_email["account_type"]:
            case "outlook":
                return Email.from_outlook_json(email_data, reader_email)
            case _:
                return None

    def _create_queues(self):
        self.mq_channel.queue_declare(server_config.RABBITMQ_EMAILS_QUEUE, durable=True)

        self.mq_channel.exchange_declare("dlx", exchange_type="direct")
        self.mq_channel.queue_declare(
            server_config.RABBITMQ_EVENTS_OUTPUT_QUEUE, 
            durable=True,
            arguments={
                'x-dead-letter-exchange': 'dlx', # Specify the DLQ exchange
                'x-dead-letter-routing-key': 'dead_events'      # Routing key for dead messages
            }
        )

    def _on_new_email(self, channel: pika.channel.Channel, 
                    method: pika.spec.Basic.Deliver, 
                    properties: pika.spec.BasicProperties, 
                    body: bytes):
        if(os.getenv("DEV_MODE") != "1"):
            f = Fernet(server_config.EMAIL_ENCRYPTION_SECRET)
            body = f.decrypt(body)

        msg_with_email: dict[str] = json.loads(body)

        user_event_categories = []
        with db.start_session() as db_session:
            query = select(tables.EventSettingsTable) \
                    .where(
                        tables.EventSettingsTable.user_id == msg_with_email["user_id"],
                        tables.EventSettingsTable.user_acc_type == models.AccountType(msg_with_email["account_type"])
                    )
            settings_row = db_session.execute(query).unique().scalar_one_or_none()

            if(settings_row == None):
                self.logger.warning(f"Settings do not exist for user {msg_with_email["user_id"]}, dropping this email since the account might be deleted")
                return channel.basic_ack(method.delivery_tag)
            else:
                for category in settings_row.categories:
                    user_event_categories.append(category.name)

        t = threading.Thread(
            target=self._start_parsing, 
            args=(channel, method, properties, msg_with_email, user_event_categories)
        )
        t.daemon = True
        t.start()

    def _start_parsing(self, channel: pika.channel.Channel, 
                       method: pika.spec.Basic.Deliver, 
                       properties: pika.spec.BasicProperties, 
                       msg_with_email: dict[str],
                       user_event_categories: list[str]):
        try:
            email: Email = self.to_email_obj(msg_with_email)
            self.logger.info(f"New e-mail: {email.id}")
            events = self.llm.parse_events_from_email(email, user_event_categories)
        except:
            self.logger.warning("Unknown exception in email parsing function", exc_info=True)
            channel.basic_nack(method.delivery_tag)
            return
        
        cb = functools.partial(self._parsing_complete, channel, method, properties, email, msg_with_email, events)
        channel.connection.add_callback_threadsafe(cb)
        self.logger.info(f"E-mail parsing finished: {email.id}")


    def _parsing_complete(self, channel: pika.channel.Channel, 
                          method: pika.spec.Basic.Deliver, 
                          properties: pika.spec.BasicProperties, 
                          email: Email, 
                          msg_with_email: dict[str],
                          events: list[dict]):
        self.logger.debug("_parsing_complete called")
        
        self.mq_channel.basic_publish(
            exchange="",
            routing_key=server_config.RABBITMQ_EVENTS_OUTPUT_QUEUE,
            properties=pika.BasicProperties(
                delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
            ),
            body=json.dumps({
                "events": events,
                "user_id": msg_with_email["user_id"],
                "account_type": msg_with_email["account_type"],
                "mail_link": email.mail_link,
                "user_timezone": msg_with_email["user_timezone"]
            })
        )

        channel.basic_ack(method.delivery_tag)

    def run(self):
        self._create_queues()

        self.mq_channel.basic_consume(server_config.RABBITMQ_EMAILS_QUEUE, self._on_new_email)

        try:
            self.mq_channel.start_consuming()
        finally:
            self.mq_channel.stop_consuming()
            self.mq_connection.close()