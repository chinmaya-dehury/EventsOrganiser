import uuid, os
from fastapi import Request

def format_calendar_link(calendar_identifier: uuid.UUID, request: Request):
    host = str(request.url).replace(str(request.url.path), "")
    if(os.getenv("DEV_MODE") != "1"):
        host = host.replace("http", "https")
    return host + "/api/events/calendar/" + str(calendar_identifier)