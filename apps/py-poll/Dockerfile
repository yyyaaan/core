FROM python:3.14-slim

RUN pip install --no-cache-dir b2sdk requests tqdm

COPY ./src /app
RUN chmod +x /app/job_dyndns.sh
RUN chmod +x /app/job_ffmpeg.sh
RUN chmod +x /app/job_backup.sh

WORKDIR /app
