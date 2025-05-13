import asyncio
from fastapi import APIRouter, FastAPI, Request, HTTPException, Depends
from datetime import datetime, timezone
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from sqlalchemy.orm import selectinload

from typing import cast

import logging
logging.basicConfig(level=logging.INFO)

from common import models, tables

import server_config, db
from helpers import auth
from helpers.auth import UserData
from mq.mail_sender import MailSenderMQ, ParseMailsRequest
from helpers import query_helpers, graph_api, mail_fetcher

__logger = logging.getLogger(__name__)

@asynccontextmanager
async def router_lifespan(app: FastAPI):
    mail_sender_mq = MailSenderMQ(
        host=server_config.RABBITMQ_HOST,
        virtual_host=server_config.RABBITMQ_VIRTUALHOST,
        username=server_config.RABBITMQ_USERNAME,
        password=server_config.RABBITMQ_PASSWORD,
        queue_name=server_config.RABBITMQ_EMAILS_QUEUE,
        enc_key=server_config.EMAIL_ENCRYPTION_SECRET
    )
    t1 = asyncio.create_task(mail_sender_mq.try_open_conn_indefinite())

    yield {"mail_sender_mq": mail_sender_mq}

    await mail_sender_mq.close_conn()

emails_router = APIRouter(
    prefix="/api/microsoft",
    lifespan=router_lifespan
)

@emails_router.post("/emails/fetch_new/", status_code=200, include_in_schema=False) # avoid stupid redirects
@emails_router.post("/emails/fetch_new", status_code=200)
async def new_email(
    request: Request,
    user: UserData = Depends(auth.authenticate_user),
    db_session: AsyncSession = Depends(db.start_session)
) -> models.FetchNewEmailsGetResponse:
    user_data = await query_helpers.update_token_db(db_session, user.account_id)
    user_settings = await query_helpers.get_settings(db_session, user_data.user_id)

    parsed_email_ids = await query_helpers.get_parsed_emails(db_session, user_data.user_id)
    unparsed_email_ids = await mail_fetcher.get_unparsed_emails_after_date(
        user_data.access_token,
        parsed_email_ids,
        datetime.now(timezone.utc) - server_config.MAX_EMAIL_AGE,
        "isDraft eq false"
    )
    ids_and_tokens = [(_id, user_data.access_token) for _id in unparsed_email_ids]
    emails = await mail_fetcher.fetch_emails_batched(
        ids_and_tokens,
        batch_size=25,
    )

    email_parse_requests = []
    for email in emails:
        email_parse_requests.append(                
            ParseMailsRequest(
                user_id=user_data.user_id,
                user_email=user_data.user_email,
                user_timezone=user_settings.timezone.timezone,
                email=email
            )
        )

    await query_helpers.add_parsed_emails(
        db_session,
        user_data.user_id,
        emails,
        expire_in=server_config.MAX_EMAIL_AGE
    )
    await cast(MailSenderMQ, request.state.mail_sender_mq).send_new_emails_to_parse(email_parse_requests)
    await db_session.commit()

    resp = models.FetchNewEmailsGetResponse(
        count=len(emails)
    )
    return resp
