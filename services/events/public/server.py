from fastapi import FastAPI
from fastapi_pagination import add_pagination
from routes import events_router, settings_router, calendar_router

import os

import sys
sys.path.append('..')

api = FastAPI(
    debug=(os.getenv("DEV_MODE") == "1"),
)
add_pagination(api)

if(os.getenv("DEV_MODE") == "1"):
    from fastapi.middleware.cors import CORSMiddleware
    api.add_middleware(
        CORSMiddleware,
        allow_origins=['*']
    )

api.include_router(settings_router)
api.include_router(events_router)
api.include_router(calendar_router)