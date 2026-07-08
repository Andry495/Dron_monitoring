FROM python:3.12-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libxml2-dev libxslt1-dev zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml ./
COPY monitor_core ./monitor_core
RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
EXPOSE 8080

CMD ["monitor-core"]
