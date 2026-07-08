FROM python:3.12-slim-bookworm

WORKDIR /app

COPY pyproject.toml ./
COPY ai_engine ./ai_engine
RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
EXPOSE 8090

CMD ["ai-engine"]
