# Internal events microservice

Subportion of the project responsible for parsing events from mail, fixing issues in parsed events and deleting user accounts.

# Getting started
## Prerequisites

### Python
You will need to have at least Python version 3.12 installed.
Required modules also need to be installed with `pip install -r requirements.txt`

### MySQL
You will need to have a MySQL server set up which supports the `UUID_TO_BIN` function. The MySQL host, password etc can be configured through environment variables listed in the Technical Details section.

### RabbitMQ
A RabbitMQ broker needs to be set up, the details can be configured through environment variables listed in the Technical Details section

### (Optional) Docker
Docker is needed to containerize the application, any version is fine.

## Running the microservice
Run the service with `py server.py` (`python3 server.py` on linux)

## Containerizing the app
Build a container with the command `docker build -t {username}/{imagename}`. If you don't plan on pushing the image to a registry then leave out the `{username}/` part.

Add the image to Docker Hub by running `docker push {username}/{imagename}`.

# Technical details

This section brings out some details that you will need to get the app running properly. It also includes details needed if you want to integrate another microservice with this app.

## Environment variables
| Variable name | Required | Description |
| - | - | - |
| RABBITMQ_HOST | yes | IP of RabbitMQ broker |
| RABBITMQ_VIRTUALHOST | no | RabbitMQ virtual host |
| RABBITMQ_USERNAME | yes | RabbitMQ management user name |
| RABBITMQ_PASSWORD | yes | RabbitMQ management user password |
| RABBITMQ_EMAILS_QUEUE | yes | RabbitMQ queue to listen to for new mail |
| RABBITMQ_EVENTS_OUTPUT_QUEUE | yes | RabbitMQ queue to send messages to about parsed events |
| MYSQL_HOST | yes | IP of the MySQL server |
| MYSQL_EVENTS_DB | yes | Database for this microservice to use |
| MYSQL_EVENTS_USER | yes | MySQL user with access to the previous database |
| MYSQL_EVENTS_PASSWORD | yes | MySQL user password |
| LLM_PATH | yes | Path to where the *.gguf LLM file is located at |
| EMAIL_ENCRYPTION_SECRET | yes | A URL-safe base64-encoded 32-byte key for Fernet to decrypt email content with |
| DEV_MODE | no | disables some encryption for easier testing, set to "1" to enable |

## RabbitMQ - sendable messages

| Brief name | Routing key | Description |
| - | - | - |
| Parsed events notification | {RABBITMQ_EVENTS_OUTPUT_QUEUE} | Parsed events are sent directly to that queue through the default (empty string) exchange |