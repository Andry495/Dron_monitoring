FROM python:3.12-slim-bookworm

WORKDIR /app

COPY pyproject.toml ./
COPY turret_sim ./turret_sim
RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
EXPOSE 8030

CMD ["turret-sim"]
