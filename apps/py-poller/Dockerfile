FROM python:3.14-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        apt-transport-https \
        ca-certificates \
        curl \
        ffmpeg \
        gnupg \
        libx264-dev \
        mariadb-client \
        zip && \
    rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir b2sdk requests tqdm

COPY ./src/poller /app
RUN chmod +x /app/job_ffmpeg.sh
RUN chmod +x /app/job_backup.sh

WORKDIR /app
