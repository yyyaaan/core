FROM python:3.13-slim

RUN apt-get update && apt-get install -y cron curl ffmpeg libx264-dev apt-transport-https ca-certificates gnupg
RUN curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list
RUN apt-get update && apt-get install -y google-cloud-cli

RUN pip install --no-cache-dir requests

COPY . /app
COPY crontab /etc/cron.d/mounted-cron
RUN chmod +x /app/job_dyndns.sh
RUN chmod +x /app/job_ffmpeg.sh

WORKDIR /app

ENTRYPOINT ["sh", "entrypoint.sh"]
