from fastapi import Depends, FastAPI, Request, Response, HTTPException

import logging
logging.basicConfig(level=logging.INFO)
__logger = logging.getLogger(__name__)

import server_config
import os

from routes import microsoft_router, general_auth_router

api = FastAPI(
    debug=(os.getenv("DEV_MODE") == "1")
)

if(os.getenv("DEV_MODE") == "1"):
    from fastapi.middleware.cors import CORSMiddleware
    api.add_middleware(
        CORSMiddleware,
        allow_origins=['*']
    )

if(server_config.MICROSOFT_APP_CLIENT_ID == None or server_config.MICROSOFT_APP_SECRET == None):
    __logger.info("Microsoft authentication disabled due to missing app client id/app secret")
else:
    api.include_router(microsoft_router)


api.include_router(general_auth_router)