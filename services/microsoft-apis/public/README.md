# Public events microservice

Subportion of the project responsible for allowing users to change Microsoft account related settings, fetch new emails (manually/automatically)

# Getting started
## Prerequisites

### Python
You will need to have at least Python version 3.12 installed.
Required modules also need to be installed with `pip install -r requirements.txt`

### MySQL
You will need to have a MySQL server set up. The MySQL host, password etc can be configured through environment variables listed in the Technical Details section.

### RabbitMQ
A RabbitMQ broker needs to be set up, the details can be configured through environment variables listed in the Technical Details section

### (Optional) Docker
Docker is needed to containerize the application, any version is fine.

## Running the microservice
For development mode, run `fastapi dev server.py` in this folder. This will enable hot-reloading the app when code changes. This also lets you view the documentation at `localhost:8000/docs` (if the port is 8000)

For production builds `fastapi dev server.py --port XXXX` is preferred.

## Containerizing the app
Build a container by running the command `docker build -t {username}/{imagename} --build-context common=../common .` in this folder. If you don't plan on pushing the image to a registry then leave out the `{username}/` part.

Add the image to Docker Hub by running `docker push {username}/{imagename}`.

# Technical details

This section brings out some details that you will need to get the app running properly. It also includes details needed if you want to integrate another microservice with this app.

## Environment variables
| Variable name | Required | Description |
| - | - | - |
| MICROSOFT_APP_CLIENT_ID | yes | Microsoft Entra application ID |
| MICROSOFT_APP_SECRET | yes | Microsoft Entra application secret |
| MICROSOFT_CALLBACK_SECRET | yes | A random string used to verify that Microsoft Graph API notifications aren't forged |
| MYSQL_HOST | yes | IP of the MySQL server |
| MYSQL_DB_USER | yes | MySQL user with access to the previous database |
| MYSQL_DB_PASSWORD | yes | MySQL user password |
| RABBITMQ_HOST | yes | IP of RabbitMQ broker |
| RABBITMQ_VIRTUALHOST | no | RabbitMQ virtual host |
| RABBITMQ_USERNAME | yes | RabbitMQ management user name |
| RABBITMQ_PASSWORD | yes | RabbitMQ management user password |
| RABBITMQ_EMAILS_QUEUE | yes | RabbitMQ queue to send new mail |
| JWT_SECRET | yes | Secret to verify JWT data with |
| JWT_SESSION_COOKIE_NAME | yes | Session cookie name where the JWT resides in |
| DOMAIN_URL | yes | URL of the domain where requests are coming in from |
| EMAIL_ENCRYPTION_SECRET | yes | A URL-safe base64-encoded 32-byte key for Fernet to encrypt email content with |
| DEV_MODE | no | disables some encryption for easier testing, set to "1" to enable |

## RabbitMQ - sendable messages
| Brief name | Routing key | Description |
| - | - | - |
| New mail | {RABBITMQ_EMAILS_QUEUE} | New e-mails are sent directly to {RABBITMQ_EMAILS_QUEUE} through the default (empty string) exchange |