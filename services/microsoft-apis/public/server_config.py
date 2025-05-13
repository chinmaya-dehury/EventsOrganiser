import os, dotenv
dotenv.load_dotenv() # only for local testing, the docker container will already have environment variables set for it
from datetime import timedelta

MICROSOFT_APP_CLIENT_ID = os.getenv("MICROSOFT_APP_CLIENT_ID")
MICROSOFT_APP_SECRET = os.getenv("MICROSOFT_APP_SECRET")
MICROSOFT_SCOPES=["Mail.Read", "Mail.ReadBasic"]
MICROSOFT_CALLBACK_SECRET = os.getenv("MICROSOFT_CALLBACK_SECRET")

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_DB_USER = os.getenv("MYSQL_DB_USER")
MYSQL_DB_PASSWORD = os.getenv("MYSQL_DB_PASSWORD")
MYSQL_ENC_KEY = os.getenv("MYSQL_ENC_KEY")

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_VIRTUALHOST = os.getenv("RABBITMQ_VIRTUALHOST")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_EMAILS_QUEUE = os.getenv("RABBITMQ_EMAILS_QUEUE")

JWT_SECRET=os.getenv("JWT_SECRET")
JWT_SESSION_COOKIE_NAME=os.getenv("JWT_SESSION_COOKIE_NAME")
EMAIL_ENCRYPTION_SECRET=os.getenv("EMAIL_ENCRYPTION_SECRET")

MAX_EMAIL_AGE = timedelta(days=31)
DOMAIN_URL = os.getenv("DOMAIN_URL")
