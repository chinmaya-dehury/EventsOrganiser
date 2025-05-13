import asyncio

from fastapi import FastAPI, APIRouter, Request, HTTPException, Depends, Body, Query
from fastapi.responses import PlainTextResponse
from datetime import datetime, timezone
import itertools

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload
from contextlib import asynccontextmanager
from zoneinfo import ZoneInfo
from collections import defaultdict
from typing import Annotated

import logging
logging.basicConfig(level=logging.INFO)

from typing import cast

from common import models, tables
import os, db
import server_config
from helpers import query_helpers, graph_api, mail_fetcher
from .sub_handler import SubscriptionHandler
from mq.mail_sender import MailSenderMQ, ParseMailsRequest

__logger = logging.getLogger(__name__)

@asynccontextmanager
async def app_lifecycle(api: FastAPI):
    mail_sender_mq = MailSenderMQ(
        host=server_config.RABBITMQ_HOST,
        virtual_host=server_config.RABBITMQ_VIRTUALHOST,
        username=server_config.RABBITMQ_USERNAME,
        password=server_config.RABBITMQ_PASSWORD,
        queue_name=server_config.RABBITMQ_EMAILS_QUEUE,
        enc_key=server_config.EMAIL_ENCRYPTION_SECRET
    )
    subscription_handler = SubscriptionHandler(
        domain_url=server_config.DOMAIN_URL,
        notification_path="/api/microsoft/subscriptions/new_email",
        notification_lifecycle_path="/api/microsoft/subscriptions/email_sub_lifecycle",
        secret=server_config.MICROSOFT_CALLBACK_SECRET,
        mail_sender_mq=mail_sender_mq
    )

    t1 = asyncio.create_task(mail_sender_mq.try_open_conn_indefinite())

    yield {
        "subscription_handler": subscription_handler,
        "mail_sender_mq": mail_sender_mq
    }

    await mail_sender_mq.close_conn()

subscriptions_router = APIRouter(
    prefix="/api/microsoft",
    lifespan=app_lifecycle
)

@subscriptions_router.post("/subscriptions/new_email/", status_code=200, include_in_schema=False) # avoid stupid redirects
@subscriptions_router.post("/subscriptions/new_email", status_code=200)
async def new_email(
    request: Request,
    validationToken: Annotated[str, Query()] = None,
    new_emails: Annotated[models.SubscriptionPayload, Body()] = None,
    db_session: AsyncSession = Depends(db.start_session)
) -> str | None:
    # new subscription validation
    if(validationToken != None):
        return PlainTextResponse(
            content=request.query_params.get("validationToken")
        )

    if(new_emails == None):
        raise HTTPException(status_code=400)

    # check if each email in notification is supposed to be parsed (or can be)
    emails_to_fetch: list[tuple[str, str]] = []
    user_data_per_email: list[tuple[tables.UserInfoTable, ZoneInfo]] = []
    emails_for_user: defaultdict[str, list[dict]] = defaultdict(list)
    for data in new_emails.value:
        if(data.client_state != server_config.MICROSOFT_CALLBACK_SECRET):
            __logger.warning("Client state given by notification does not match the server's callback secret")
            continue
        subscription_row = await query_helpers.get_email_notification_subscription(db_session, sub_id=data.subscription_id)
        if(subscription_row == None):
            continue

        user_settings = await query_helpers.get_settings(db_session, subscription_row.user_id)
        user_info = await query_helpers.update_token_db(db_session, subscription_row.user_id)
        if(user_info.access_token == None):
            __logger.warning(f"User {user_info.user_id} does not have a valid access token")
            continue
        if(user_settings.auto_fetch_emails == False):
            __logger.warning(f"User {user_info.user_id} has disabled automatic email fetching, but a notification was still sent by the Graph API")
            continue

        emails_to_fetch.append((data.resource_data.id, user_info.access_token))
        user_data_per_email.append((user_info, user_settings.timezone.timezone))

    emails = await mail_fetcher.fetch_emails_batched(
        emails_to_fetch,
        filter_func=lambda email: email["isDraft"] == False
    )

    email_parse_requests: list[ParseMailsRequest] = []
    for i, email in enumerate(emails):
        email_parse_requests.append(
            ParseMailsRequest(
                user_id=user_data_per_email[i][0].user_id,
                user_email=user_data_per_email[i][0].user_email,
                user_timezone=user_data_per_email[i][1],
                email=email
            )
        )
        emails_for_user[user_data_per_email[i][0].user_id].append(email)

    for user_id, emails in emails_for_user.items():
        await query_helpers.add_parsed_emails(
            db_session,
            user_id,
            emails,
            expire_in=server_config.MAX_EMAIL_AGE
        )

    await cast(MailSenderMQ, request.state.mail_sender_mq).send_new_emails_to_parse(
        email_parse_requests
    )
    await db_session.commit()

    return

@subscriptions_router.post("/subscriptions/email_sub_lifecycle/", status_code=200, include_in_schema=False) # avoid stupid redirects
@subscriptions_router.post("/subscriptions/email_sub_lifecycle", status_code=200)
async def subscription_lifecycle(
    request: Request,
    validationToken: Annotated[str, Query()] = None,
    lifecycle_notification: Annotated[models.SubscriptionPayload, Body()] = None,
) -> str | None:
    # new subscription validation
    if(validationToken != None):
        return PlainTextResponse(
            content=request.query_params.get("validationToken")
        )
    
    if(lifecycle_notification == None):
        raise HTTPException(status_code=400)

    subscription_handler = cast(SubscriptionHandler, request.state.subscription_handler)
    async with asyncio.TaskGroup() as tg:
        for subscription_data in lifecycle_notification.value:
            tg.create_task(
                subscription_handler.handle_lifecycle_notification(subscription_data, server_config.MAX_EMAIL_AGE)
            )