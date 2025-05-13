import sys
sys.path.append('..')
from common import models, tables

import logging
logging.basicConfig(level=logging.INFO)

from pydantic import BaseModel, field_validator, model_validator
from datetime import datetime, tzinfo
from zoneinfo import ZoneInfo
from queue import Queue
import sqlalchemy.exc
import pydantic

from sqlalchemy import select, delete, update
from sqlalchemy import func
from sqlalchemy.orm import Session
import threading
import pika, pika.spec, pika.channel

import db, server_config

class NewEvents(BaseModel):
    user_id: str
    account_type: str
    mail_link: str
    user_timezone: ZoneInfo
    events: list[models.ParsedEvent]


class EventValidatorThread(threading.Thread):
    """
    Validates incoming events from the parser, fixes issues and adds them to the database.
    """
    def __init__(self):
        super(EventValidatorThread, self).__init__()

        self.__logger = logging.getLogger(__name__ + "." + type(self).__name__)

        self.mq_connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=server_config.RABBITMQ_HOST, 
                port=5672, 
                virtual_host=server_config.RABBITMQ_VIRTUALHOST, 
                credentials=pika.PlainCredentials(server_config.RABBITMQ_USERNAME, server_config.RABBITMQ_PASSWORD))
        )
        self.mq_channel = self.mq_connection.channel()
        self.mq_channel.basic_qos(prefetch_count=1)

    def fix_and_combine_location(self, parsed_event: models.ParsedEvent) -> str:
        locations = []
        if(parsed_event.country != None and len(parsed_event.country)):
            locations.append(parsed_event.country.title())

        if(parsed_event.city != None and len(parsed_event.city)):
            locations.append(parsed_event.city.title())

        if(parsed_event.address != None and len(parsed_event.address)):
            locations.append(parsed_event.address)

        if(parsed_event.room != None and len(parsed_event.room)):
            locations.append(parsed_event.room)

        if(len(locations) == 0):
            return "N/A"
        else:
            return ", ".join(locations)

    def get_or_create_tag(self, db_session: Session, tag_name: str) -> tables.TagsTable:
        query = select(tables.TagsTable) \
                .where(func.lower(tables.TagsTable.name) == tag_name.lower())
        tag_row = db_session.execute(query).scalar_one_or_none()

        if(tag_row == None):
            self.__logger.info(f"Creating new tag {tag_name} without committing, since it was missing")
            tag_row = tables.TagsTable()
            tag_row.name = tag_name

        return tag_row

    def fix_datetimes(self, start_date: datetime | None, end_date: datetime, user_timezone: ZoneInfo) -> tuple[datetime | None, datetime]:
        """Returns fixed & localized UTC datetimes"""

        if(start_date == None):
            if(not models.tz_aware(end_date)):
                end_date = end_date.replace(tzinfo=user_timezone)
            return None, end_date

        # only one date has timezone defined, which is probably a weird AI issue so we extend the found timezone to the other datetime
        if(models.tz_aware(start_date) != models.tz_aware(end_date)):
            self.__logger.info("Found instance of only one (start_date, end_date) having timezone information provided by AI")
            self.__logger.info(f"{start_date=}, {end_date=}")

            defined_timezone: tzinfo = (start_date.tzinfo or end_date.tzinfo)
            if(not models.tz_aware(start_date)):
                start_date = start_date.replace(tzinfo=defined_timezone)
            else:
                end_date = end_date.replace(tzinfo=defined_timezone)
        elif(not models.tz_aware(start_date) and not models.tz_aware(end_date)):
            start_date = start_date.replace(tzinfo=user_timezone)
            end_date = end_date.replace(tzinfo=user_timezone)

        return start_date.astimezone(tz=ZoneInfo("UTC")), end_date.astimezone(tz=ZoneInfo("UTC"))

    def validate_and_create_event_row(self, db_session: Session, parsed_event: models.ParsedEvent, user_timezone: ZoneInfo) -> tables.EventsTable:
        """Fixes a few AI related issues & returns a new events row object"""
        event_row = tables.EventsTable()
        event_row.event_name = parsed_event.event_name

        fixed_start_date_utc, fixed_end_date_utc = self.fix_datetimes(parsed_event.start_date, parsed_event.end_date, user_timezone)
        event_row.start_date_utc = fixed_start_date_utc
        event_row.end_date_utc = fixed_end_date_utc
        event_row.address = self.fix_and_combine_location(parsed_event)

        for tag_name in parsed_event.tags:
            event_row.tags.append(self.get_or_create_tag(db_session, tag_name))

        return event_row

    def should_ignore_event(self, parsed_event: models.ParsedEvent) -> bool:
        """Checks whether this event should be added to the DB for a user"""
        if(len(parsed_event.tags) == 0):
            return True
        
        return False

    def add_events_to_db(self, new_events: NewEvents) -> None:
        with db.start_session() as db_session:
            for parsed_event in new_events.events:
                if(self.should_ignore_event(parsed_event)):
                    continue

                try:
                    event_row = self.validate_and_create_event_row(db_session, parsed_event, new_events.user_timezone)
                except ValueError:
                    self.__logger.warning("Unexpected ValueError when validating event data, event dropped", exc_info=True)
                    continue

                event_row.user_id = new_events.user_id
                event_row.user_acc_type = new_events.account_type
                event_row.email_link = new_events.mail_link
                db_session.add(event_row)

            db_session.commit()

    def _on_new_events(self, channel: pika.channel.Channel, 
                    method: pika.spec.Basic.Deliver, 
                    properties: pika.spec.BasicProperties, 
                    body: bytes):
        try:
            data: NewEvents = NewEvents.model_validate_json(body)
        except pydantic.ValidationError:
            self.__logger.warning(f"Events from an email rejected due to data validation errors", exc_info=True)
            channel.basic_reject(method.delivery_tag, requeue=False)
            return
        
        try:
            self.add_events_to_db(data)
            channel.basic_ack(method.delivery_tag)
        except ValueError:
            self.__logger.warning("Unexpected ValueError when adding events to the database", exc_info=True)
            channel.basic_reject(method.delivery_tag, requeue=False)
        except sqlalchemy.exc.OperationalError:
            self.__logger.error("Unable to execute queries on the events MySQL database", exc_info=True)
            channel.basic_reject(method.delivery_tag, requeue=True)
        except Exception:
            self.__logger.error("Unknown exception occurred", exc_info=True)
            channel.basic_reject(method.delivery_tag, requeue=False)
            pass

    def _create_queues(self):
        self.mq_channel.exchange_declare(exchange='dlx', exchange_type='direct')
        self.mq_channel.queue_declare(queue='dead_events', durable=True)
        self.mq_channel.queue_bind(queue='dead_events', exchange='dlx', routing_key='dead_events')

        self.mq_channel.queue_declare(
            server_config.RABBITMQ_EVENTS_OUTPUT_QUEUE, 
            durable=True,
            arguments={
                'x-dead-letter-exchange': 'dlx', # Specify the DLQ exchange
                'x-dead-letter-routing-key': 'dead_events'      # Routing key for dead messages
            }
        )

    def run(self):
        self._create_queues()

        self.mq_channel.basic_consume(server_config.RABBITMQ_EVENTS_OUTPUT_QUEUE, self._on_new_events)

        try:
            self.mq_channel.start_consuming()
        finally:
            self.mq_channel.stop_consuming()
            self.mq_connection.close()

