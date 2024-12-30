FROM python:3.13-slim

RUN pip install --no-cache-dir requests
RUN apt-get update && apt-get install -y cron curl

COPY . /app
COPY crontab /etc/cron.d/mounted-cron
RUN chmod +x /app/job_dyndns.sh

WORKDIR /app

ENTRYPOINT ["sh", "entrypoint.sh"]
