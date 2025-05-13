from fastapi import APIRouter, Request, Response, HTTPException, Depends, FastAPI
from fastapi.responses import RedirectResponse
from fastapi_server_session import Session, SessionManager, AsyncMysqlSessionInterface
from pydantic import BaseModel
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from contextlib import asynccontextmanager
from typing import cast
import msal
import urllib.parse
import logging
logging.basicConfig(level=logging.INFO)
import aiomysql

import os
import server_config
from helpers import auth
from mq.notification_sender import NotificationMQ

__logger = logging.getLogger(__name__)

session_manager = SessionManager(
    default_sess_duration=timedelta(minutes=10),
    interface=AsyncMysqlSessionInterface(
        pool_ctx=aiomysql.create_pool(
            host=server_config.MYSQL_HOST, 
            port=3306, 
            user=server_config.MYSQL_DB_USER, 
            password=server_config.MYSQL_DB_PASSWORD, 
            db=server_config.MYSQL_DB_NAME
        )
    )
)
ms_app = msal.ConfidentialClientApplication(
    client_id=server_config.MICROSOFT_APP_CLIENT_ID,
    client_credential=server_config.MICROSOFT_APP_SECRET
)

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

microsoft_router = APIRouter(
    prefix="/api/auth/microsoft",
    lifespan=router_lifespan
)

def get_redirect_uri(request: Request):
    host = str(request.url).replace(str(request.url.path), "")
    if(os.getenv("DEV_MODE") != "1"):
        host = host.replace("http://", "https://")
    
    return host + "/api/auth/microsoft/login_callback"
        
class LoginLinkPostRequest(BaseModel):
    timezone: ZoneInfo

@microsoft_router.post("/", include_in_schema=False) # avoid stupid redirects
@microsoft_router.post("")
async def get_login_link(
    data: LoginLinkPostRequest,
    request: Request,
    session: Session = Depends(session_manager.get_or_start_session)
) -> str:
    """
    API endpoint that initiates the Microsoft login flow
    """
    flow = ms_app.initiate_auth_code_flow(
        scopes=server_config.MICROSOFT_SCOPES,
        redirect_uri=get_redirect_uri(request),
    )
    session["ms_flow"] = flow
    session["user_timezone"] = str(data.timezone) # used for first login to properly create settings...

    return flow["auth_uri"]

@microsoft_router.get("/login_callback/", include_in_schema=False) # avoid stupid redirects
@microsoft_router.get("/login_callback", status_code=303)
async def finish_login(
    request: Request,
    session: Session = Depends(session_manager.get_session)
):
    """
    API endpoint that finalizes the login process by giving the user a JWT token and redirecting him to the home page.

    A notification gets sent in the RabbitMQ 'notifications' exchange with routing key 'notification.outlook.user_login'
    """
    response = RedirectResponse("/", status_code=303)

    auth_flow = ms_app.acquire_token_by_auth_code_flow(auth_code_flow=session["ms_flow"], auth_response=dict(request.query_params))
    if "error" in auth_flow:
        error_str = auth_flow["error_description"] if "error_description" in auth_flow else auth_flow["error"]
        raise RedirectResponse(
            url=f"/login?error={urllib.parse.quote_plus('Problem authenticating with Microsoft account: {}'.format(error_str))}",
            status_code=302, 
        )

    decoded_token, err_msg = await auth.decode_jwt_token(auth_flow["id_token"], server_config.MICROSOFT_APP_CLIENT_ID)
    if(decoded_token == None):
        __logger.warning(f"Problem decoding JWT token after Microsoft login callback: {err_msg}")
        raise RedirectResponse(
            url=f"/login?error={urllib.parse.quote_plus('Unable to verify that the response token is issued by Microsoft')}",
            status_code=302
        )

    token_data = auth.create_jwt_from_microsoft(decoded_token, server_config.JWT_SECRET)
    auth.set_jwt_cookie(server_config.JWT_SESSION_COOKIE_NAME, token_data, response)

    await cast(NotificationMQ, request.state.notifications_mq).notify_of_ms_login(
        decoded_token["oid"],
        datetime.now(timezone.utc) + timedelta(seconds=auth_flow["expires_in"]),
        decoded_token["email"],
        ZoneInfo(session["user_timezone"]),
        auth_flow["access_token"],
        auth_flow["refresh_token"]
    )

    return response