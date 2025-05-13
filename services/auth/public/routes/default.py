from fastapi import APIRouter, Request, Response, HTTPException, Depends, FastAPI
from fastapi.responses import RedirectResponse
from fastapi_server_session import Session, SessionManager, AsyncMysqlSessionInterface
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from contextlib import asynccontextmanager
from typing import cast
import msal
import aiohttp
import logging
logging.basicConfig(level=logging.INFO)
import aiomysql

import os
import server_config
from helpers import auth
from mq.notification_sender import NotificationMQ

__logger = logging.getLogger(__name__)

@asynccontextmanager
async def router_lifespan(app: FastAPI):
    notifications_mq = NotificationMQ(
        host=server_config.RABBITMQ_HOST,
        virtual_host=server_config.RABBITMQ_VIRTUALHOST,
        username=server_config.RABBITMQ_USERNAME,
        password=server_config.RABBITMQ_PASSWORD,
        listeners=[]
    )

    await notifications_mq.try_open_conn_indefinite()

    yield {
        "notifications_mq": notifications_mq
    }

    await notifications_mq.close_conn()

general_auth_router = APIRouter(
    prefix="/api/auth",
    lifespan=router_lifespan
)

@general_auth_router.post("/delete_account/", include_in_schema=False)
@general_auth_router.post("/delete_account")
async def delete_account(
    request: Request,
    user: auth.UserData = Depends(auth.authenticate_user)
):
    cast(NotificationMQ, request.state.notifications_mq).send_notification(
        {
            "user_id": user.account_id,
            "account_type": user.account_type
        },
        routing_key=f"notification.{user.account_type}.delete_account"
    )

    return