FROM python:3.12-slim-bookworm

WORKDIR /app

COPY pyproject.toml ./
COPY simulator ./simulator
RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
EXPOSE 8070

CMD ["scenario-simulator"]
