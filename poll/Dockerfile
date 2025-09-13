FROM python:3.13-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        cron \
        curl \
        ffmpeg \
        libx264-dev \
        apt-transport-https \
        ca-certificates \
        gnupg \
        zip \
        mariadb-client && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee /etc/apt/sources.list.d/google-cloud-sdk.list && \
    apt-get update && \
    apt-get install -y --no-install-recommends google-cloud-cli && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir b2sdk requests tqdm

COPY . /app
COPY crontab /etc/cron.d/mounted-cron
RUN chmod +x /app/job_dyndns.sh
RUN chmod +x /app/job_ffmpeg.sh

WORKDIR /app

ENTRYPOINT ["sh", "entrypoint.sh"]
