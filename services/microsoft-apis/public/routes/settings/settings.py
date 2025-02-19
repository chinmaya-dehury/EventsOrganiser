import os
if(os.getenv("DEV_MODE") == "1"):
    import sys
    sys.path.append('..')

import asyncio 

from fastapi import FastAPI, APIRouter, Request, Response, HTTPException, Depends
from datetime import timedelta

import sqlalchemy.exc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy import select
from zoneinfo import ZoneInfo
from datetime import datetime
from contextlib import asynccontextmanager
import dataclasses
from typing import cast

import logging
logging.basicConfig(level=logging.INFO)

from common import models, tables

import server_config
import db

import server_config
from helpers import auth
from helpers import query_helpers
from helpers.auth import UserData
from mq.notifications import NotifiactionMQ
from routes.subscriptions.sub_handler import SubscriptionHandler

@asynccontextmanager
async def app_lifespan(app: FastAPI):
    # https://github.com/Kludex/fastapi-tips?tab=readme-ov-file#6-use-lifespan-state-instead-of-appstate
    settings_notification_mq = NotifiactionMQ(
        host=server_config.RABBITMQ_HOST,
        virtual_host=server_config.RABBITMQ_VIRTUALHOST,
        username=server_config.RABBITMQ_USERNAME,
        password=server_config.RABBITMQ_PASSWORD,
        queue_name="outlook_user_logins",
        routing_key="notification.outlook.user_login",
        notification_callback=process_login_notification
    ) 
    await settings_notification_mq.open_conn()

    yield {"settings_notification_mq": settings_notification_mq}

    # cleanup
    await settings_notification_mq.close_conn()

__logger = logging.getLogger(__name__)
settings_router = APIRouter(
    prefix="/api/microsoft",
    lifespan=app_lifespan
)

@settings_router.get("/settings")
async def get_settings(
    user: UserData = Depends(auth.authenticate_user),
    db_session: AsyncSession = Depends(db.start_session)
) -> models.SettingsGetResponse:
    settings_row = await query_helpers.get_settings(db_session, user.account_id)

    return models.SettingsGetResponse(
        auto_fetch_emails=settings_row.auto_fetch_emails,
        timezone=settings_row.timezone.timezone
    )

@settings_router.patch("/settings", status_code=204)
async def update_settings(
    new_settings: models.SettingsPostRequest,
    request: Request,
    user: UserData = Depends(auth.authenticate_user),
    db_session: AsyncSession = Depends(db.start_session)
):
    settings_row = await query_helpers.get_settings(db_session, user.account_id)

    settings_row.auto_fetch_emails = new_settings.auto_fetch_emails
    settings_row.timezone = await query_helpers.get_or_create_timezone(db_session, new_settings.timezone)

    res = await cast(SubscriptionHandler, request.state.subscription_handler).settings_changed_notification(settings_row)
    if(res == False):
        raise HTTPException(status_code=500, detail=f"Failed to {"disable" if settings_row.auto_fetch_emails == False else "enable"} automatic email parsing on Microsoft's side")

    await db_session.merge(settings_row)
    await db_session.commit()

    return

async def process_login_notification(message: dict) -> bool:
    results = await asyncio.gather(
        merge_user_info(message),
        create_settings(message),
        return_exceptions=True
    )
    
    return all(results)

async def create_settings(data: dict) -> bool:
    async with db.async_session() as db_session:
        q = select(tables.SettingsTable) \
            .where(tables.SettingsTable.user_id == data["account_id"])
        user_settings = (await db_session.execute(q)).scalar_one_or_none()
        if(user_settings != None): # user already has settings...
            return True

        settings_row = tables.SettingsTable()
        settings_row.user_id = data["account_id"]
        settings_row.timezone = await query_helpers.get_or_create_timezone(db_session, ZoneInfo(data["user_timezone"]))

        db_session.add(settings_row)

        try:
            await db_session.commit()
        except sqlalchemy.exc.IntegrityError as e:
            await db_session.rollback()
            if("duplicate" in e._message().lower()):
                __logger.warning(f"Settings for user {data['account_id']} already exist somehow (not overwritten by this notification)")
            else:
                __logger.warning("Unknown IntegrityError when trying to create new settings for user", exc_info=True)
                return False

    return True

async def merge_user_info(data: dict):
    """
    Creates or updates existing user info
    """

    async with db.async_session() as db_session:
        db_session = cast(AsyncSession, db_session)
        user_info = tables.UserInfoTable()
        user_info.user_id = data["account_id"]
        user_info.user_email = data["email"]
        user_info.access_token = data["access_token"]
        user_info.access_token_expires = datetime.fromisoformat(data["access_token_expiration"]) 
        user_info.refresh_token = data["refresh_token"]

        await db_session.merge(user_info)
        await db_session.commit()

    return True