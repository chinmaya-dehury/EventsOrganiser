import os, dotenv
dotenv.load_dotenv() # only for local testing, the docker container will already have environment variables set for it

MICROSOFT_APP_CLIENT_ID = os.getenv("MICROSOFT_APP_CLIENT_ID")
MICROSOFT_APP_SECRET = os.getenv("MICROSOFT_APP_SECRET")
MICROSOFT_SCOPES=["Mail.Read", "email"]

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_VIRTUALHOST = os.getenv("RABBITMQ_VIRTUALHOST") or "/"
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")

MYSQL_DB_NAME = os.getenv("MYSQL_DB_NAME")
MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DB_USER = os.getenv("MYSQL_DB_USER")
MYSQL_DB_PASSWORD = os.getenv("MYSQL_DB_PASSWORD")

JWT_SECRET = os.getenv("JWT_SECRET")
if(os.getenv("DEV_MODE") == "1"):
    JWT_SESSION_COOKIE_NAME = "session-jwt"
else:
    JWT_SESSION_COOKIE_NAME = "__Host-session-jwt"