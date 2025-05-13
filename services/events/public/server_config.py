import os, dotenv
dotenv.load_dotenv() # only for local testing, the docker container will already have environment variables set for it

MICROSOFT_APP_CLIENT_ID = os.getenv("MICROSOFT_APP_CLIENT_ID")
MICROSOFT_APP_SECRET = os.getenv("MICROSOFT_APP_SECRET")

MYSQL_EVENTS_USER = os.getenv("MYSQL_EVENTS_USER")
MYSQL_EVENTS_PASSWORD = os.getenv("MYSQL_EVENTS_PASSWORD")
MYSQL_HOST = os.getenv("MYSQL_HOST")

JWT_SECRET=os.getenv("JWT_SECRET")
JWT_SESSION_COOKIE_NAME=os.getenv("JWT_SESSION_COOKIE_NAME")

LIMIT_RESULTS = 100
YIELD_EVENTS_PER_TIME = 20