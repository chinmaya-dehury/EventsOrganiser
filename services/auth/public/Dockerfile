FROM python:3.12-slim
EXPOSE 80

WORKDIR /app
COPY . .
COPY requirements.txt requirements.txt

RUN apt-get update && apt-get install -y git
RUN pip install --no-cache-dir -r requirements.txt

CMD ["fastapi", "run", "server.py", "--port", "80"] 