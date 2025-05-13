import os, dotenv
dotenv.load_dotenv() # only for local testing, the docker container will already have environment variables set for it

RABBITMQ_HOST = os.getenv("RABBITMQ_HOST")
RABBITMQ_VIRTUALHOST = os.getenv("RABBITMQ_VIRTUALHOST")
RABBITMQ_USERNAME = os.getenv("RABBITMQ_USERNAME")
RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD")
RABBITMQ_EVENTS_OUTPUT_QUEUE = os.getenv("RABBITMQ_EVENTS_OUTPUT_QUEUE")
RABBITMQ_EMAILS_QUEUE = os.getenv("RABBITMQ_EMAILS_QUEUE")

MYSQL_HOST = os.getenv("MYSQL_HOST")
MYSQL_EVENTS_USER = os.getenv("MYSQL_EVENTS_USER")
MYSQL_EVENTS_PASSWORD = os.getenv("MYSQL_EVENTS_PASSWORD")
MYSQL_EVENTS_DB = os.getenv("MYSQL_EVENTS_DB")

EMAIL_ENCRYPTION_SECRET=os.getenv("EMAIL_ENCRYPTION_SECRET")
LLM_PATH = os.getenv("LLM_PATH")

DEFAULT_EVENT_CATEGORIES = [
    "Deadline", "Moodle", "Personal", "Computer Science", "University of Tartu", "General",
    "Hackathon", "Internship", "Feedback"
]