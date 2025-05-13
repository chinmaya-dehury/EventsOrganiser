import time, json, os, pika, dotenv, uuid, itertools
from cryptography.fernet import Fernet
import logging
from logging.handlers import RotatingFileHandler
dotenv.load_dotenv()

USERS = 250
USER_MAIL_PER_DAY = 20
TEST_MAX_TIME_SECONDS = 28800

microsoft_emails = []
with open("emails.json", "r", encoding="UTF-8") as f:
    json_data = json.loads(f.read())
    for email in json_data["value"]:
        microsoft_emails.append(email)

def modify_email(email: dict):
    """
    Assigns a new ID and web link to Microsoft mail JSON
    
    This makes it unique compared to any previous examples, especially if there aren't many emails in emails.json
    """
    new_email = email.copy()
    new_email["id"] = str(uuid.uuid4())
    new_email["webLink"] = f"https://outlook.office365.com/owa/?ItemID={new_email['id']}&exvsurl=1&viewmodel=ReadMessageItem"
    return new_email

def run_test():
    """Run the performance test for email parsing"""
    f = Fernet(os.getenv("FERNET_ENC_KEY"))
    delay_between_mail_seconds = 86400 / (USERS*USER_MAIL_PER_DAY)

    # https://stackoverflow.com/questions/6386698/how-to-write-to-a-file-using-the-logging-python-module
    handlers = [ 
        RotatingFileHandler(
            filename="./performance_test.log", 
            mode='w', 
            maxBytes=512000, 
            backupCount=4
        )
    ]
    logging.basicConfig(handlers=handlers, 
                        level=logging.INFO, 
                        format='%(levelname)s %(asctime)s %(message)s', 
                        datefmt='%m/%d/%Y %I:%M:%S %p %Z')
        
    logger = logging.getLogger('my_logger')
    mq_connection = pika.BlockingConnection(
        pika.ConnectionParameters(
            heartbeat=int(delay_between_mail_seconds*2),
            host=os.getenv("RABBITMQ_HOST"), 
            port=5672, 
            virtual_host=os.getenv("RABBITMQ_VIRTUALHOST"), 
            credentials=pika.PlainCredentials(os.getenv("RABBITMQ_USERNAME"), os.getenv("RABBITMQ_PASSWORD")))
    )
    mq_channel = mq_connection.channel()

    print("testing started")
    test_start = time.time()
    for email in itertools.cycle(microsoft_emails):
        if(time.time() - test_start > TEST_MAX_TIME_SECONDS):
            break

        new_email = modify_email(email)
        mq_channel.basic_publish(
            exchange="",
            routing_key="email_parsing_queue",
            body=f.encrypt(
                json.dumps({
                    "user_id": "00000000-0000-0000-82a0-946cac1dbac9",
                    "account_type": "outlook",
                    "user_timezone": "Europe/Kyiv",
                    "email_data": new_email,
                    "reader_email": "madisman5@outlook.com"
                }).encode()
            )
        )

        logger.info("%s; %s", new_email["id"], new_email["webLink"])

        time.sleep(delay_between_mail_seconds)

    print("testing finished")

run_test()