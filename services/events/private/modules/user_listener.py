import sys
sys.path.append('..')
from common import models, tables

import logging
logging.basicConfig(level=logging.INFO)

import sqlalchemy.exc
import json

from sqlalchemy import select, delete, update
from sqlalchemy import func
from sqlalchemy.orm import Session
import threading
import pika, pika.spec, pika.channel

import db, server_config

from common import models

class UserListener(threading.Thread):
    """
    Listens to user authentication notifications & user deletion notifications
    """
    def __init__(self):
        super(UserListener, self).__init__()

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

    def _create_queues(self):
        """
        Create queues where the notifications exchange shall send user login notifications
        """
        self.mq_channel.queue_declare(queue='user_logins_events_listener', durable=True)
        self.mq_channel.queue_bind(queue='user_logins_events_listener', exchange='notifications', routing_key='notification.*.user_login')

        self.mq_channel.queue_declare(queue='user_deletions_events_listener', durable=True)
        self.mq_channel.queue_bind(queue='user_deletions_events_listener', exchange='notifications', routing_key='notification.*.delete_account')

    def _process_login_message(self, user_data: dict) -> bool:
        with db.start_session() as db_session:
            query = select(tables.EventSettingsTable) \
                    .where(
                        tables.EventSettingsTable.user_id == user_data["account_id"],
                        tables.EventSettingsTable.user_acc_type == models.AccountType(user_data["account_type"])
                    )
            query_result = db_session.execute(query)
            settings_row = query_result.unique().scalar_one_or_none()
            if(settings_row != None):
                return True
            
            settings_row = tables.EventSettingsTable()
            settings_row.user_id = user_data["account_id"]
            settings_row.user_acc_type = models.AccountType(user_data["account_type"])
            # tags/categories, default to having everything
            categories_query = db_session.execute(select(tables.TagsTable))
            for (category_tag, ) in categories_query.all():
                settings_row.categories.append(category_tag)

            db_session.add(settings_row)

            try:
                db_session.commit()
            except sqlalchemy.exc.IntegrityError as e:
                db_session.rollback()
                if("duplicate" in e._message().lower()):
                    self.__logger.warning(f"Event Settings for user {user_data['account_id']} already exist somehow (not overwritten by this notification)")
                else:
                    self.__logger.warning("Unknown IntegrityError when trying to create new settings for user", exc_info=True)
                    return False
                
        return True
    
    def _process_deletion_request(self, user_data: dict) -> bool:
        user_id, account_type = user_data["user_id"], models.AccountType(user_data["account_type"])
        with db.start_session() as db_session:
            db_session.execute(
                delete(tables.EventsTable).where(
                    tables.EventsTable.user_id == user_id, tables.EventsTable.user_acc_type == account_type
                )
            )

            db_session.execute(
                delete(tables.CalendarLinksTable).where(
                    tables.CalendarLinksTable.user_id == user_id, tables.CalendarLinksTable.user_acc_type == account_type
                )
            )

            db_session.execute(
                delete(tables.EventSettingsTable).where(
                    tables.EventSettingsTable.user_id == user_id, tables.EventSettingsTable.user_acc_type == account_type
                )
            )

            db_session.commit()

        return True

    def _on_deletion_request(self, channel: pika.channel.Channel, 
                    method: pika.spec.Basic.Deliver, 
                    properties: pika.spec.BasicProperties, 
                    body: bytes):
        try:
            user_data = json.loads(body)
        except json.JSONDecodeError:
            self.__logger.warning(f"_on_deletion_request: Could not get user data for {method.delivery_tag}, deleting that message", exc_info=True)
            channel.basic_reject(method.delivery_tag, requeue=False)
            return
        
        try:
            if(self._process_deletion_request(user_data)):
                channel.basic_ack(method.delivery_tag)
            else:
                channel.basic_nack(method.delivery_tag)
        except:
            self.__logger.warning("_process_deletion_request() raised an exception", exc_info=True)
            channel.basic_nack(method.delivery_tag)
            return

    def _on_user_login(self, channel: pika.channel.Channel, 
                    method: pika.spec.Basic.Deliver, 
                    properties: pika.spec.BasicProperties, 
                    body: bytes):
        try:
            user_data = json.loads(body)
        except json.JSONDecodeError:
            self.__logger.warning(f"_on_user_login: Could not get user data for {method.delivery_tag}, deleting that message", exc_info=True)
            channel.basic_reject(method.delivery_tag, requeue=False)
            return
        
        try:
            if(self._process_login_message(user_data)):
                channel.basic_ack(method.delivery_tag)
            else:
                channel.basic_nack(method.delivery_tag)
        except:
            self.__logger.warning("_process_login_message() raised an exception", exc_info=True)
            channel.basic_nack(method.delivery_tag)
            return

    def run(self):
        self._create_queues()

        self.mq_channel.basic_consume('user_logins_events_listener', self._on_user_login)
        self.mq_channel.basic_consume('user_deletions_events_listener', self._on_deletion_request)

        try:
            self.mq_channel.start_consuming()
        finally:
            self.mq_channel.stop_consuming()
            self.mq_connection.close()

