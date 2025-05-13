import os, server_config # necessary import
if(os.getenv("DEV_MODE") == "1"):
    import sys
    sys.path.append('..')

from fastapi import FastAPI

import os
from routes import settings_router, emails_router, subscriptions_router

api = FastAPI(
    debug=(os.getenv("DEV_MODE") == "1"),
)

api.include_router(settings_router)
api.include_router(emails_router)
api.include_router(subscriptions_router)