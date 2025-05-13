# Authentication microservice

Subportion of the project responsible for allowing users to log in with their Microsoft account. This service gives out JWT's for authenticated users and handles account data deletion requests.

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
For development mode, run `fastapi dev server.py` in this folder. This will enable hot-reloading the app when code changes. This also lets you view the documentation at `localhost:8000/docs` (if the port is 8000)

For production builds `fastapi dev server.py --port XXXX` is preferred.

## Containerizing the app
Build a container by running the command `docker build -t {username}/{imagename} .` in this folder. If you don't plan on pushing the image to a registry then leave out the `{username}/` part.

Add the image to Docker Hub by running `docker push {username}/{imagename}`.

# Technical details

This section brings out some details that you will need to get the app running properly. It also includes details needed if you want to integrate another microservice with this app.

## Environment variables
| Variable name | Required | Description |
| - | - | - |
| MICROSOFT_APP_CLIENT_ID | yes | Microsoft Entra application ID |
| MICROSOFT_APP_SECRET | yes | Microsoft Entra application secret  |
| JWT_SECRET | yes | custom string to use as the JWT generation secret |
| RABBITMQ_HOST | yes | IP of RabbitMQ broker |
| RABBITMQ_VIRTUALHOST | no | RabbitMQ virtual host |
| RABBITMQ_USERNAME | yes | RabbitMQ management user name |
| RABBITMQ_PASSWORD | yes | RabbitMQ management user password 
| MYSQL_HOST | yes | IP of the MySQL server |
| MYSQL_DB_NAME | yes | Database for this microservice to use |
| MYSQL_DB_USER | yes | MySQL user with access to the previous database |
| MYSQL_DB_PASSWORD | yes | MySQL user password |
| DEV_MODE | no | disables some encryption for easier testing, set to "1" to enable |

## RabbitMQ - sendable messages

| Brief name | Routing key | Description |
| - | - | - |
| Login notification | notification.{account_type}.user_login | account_type is "outlook" (nothing else yet) |
| Account deletion | notification.{account_type}.delete_account | account_type is "outlook" (nothing else yet) |