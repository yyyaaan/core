FROM python:3.13-slim

RUN pip install --no-cache-dir requests
RUN apt-get update && apt-get install -y cron curl ffmpeg libx264-dev

COPY . /app
COPY crontab /etc/cron.d/mounted-cron
RUN chmod +x /app/job_dyndns.sh
RUN chmod +x /app/job_ffmpeg.sh

WORKDIR /app

ENTRYPOINT ["sh", "entrypoint.sh"]
