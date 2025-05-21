FROM python:3.13-slim

RUN apt-get update && apt-get install -y \
    ffmpeg \
    icecast2 \
    supervisor \
    libasound2 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

