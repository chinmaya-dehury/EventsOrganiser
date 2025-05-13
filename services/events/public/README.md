# Public events microservice

Subportion of the project responsible for allowing users to view, modify and delete events, change event settings & export them to a calendar.

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
| MYSQL_HOST | yes | IP of the MySQL server |
| MYSQL_EVENTS_USER | yes | MySQL user with access to the previous database |
| MYSQL_EVENTS_PASSWORD | yes | MySQL user password |
| JWT_SECRET | yes | Secret to verify JWT data with |
| JWT_SESSION_COOKIE_NAME | yes | Session cookie name where the JWT resides in |
| DEV_MODE | no | disables some encryption for easier testing, set to "1" to enable |