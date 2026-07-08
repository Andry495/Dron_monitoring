FROM python:3.12-slim-bookworm

WORKDIR /app

COPY services/operator-ui/pyproject.toml ./
COPY services/operator-ui/operator_ui ./operator_ui
COPY ui ./ui
RUN pip install --no-cache-dir .

ENV PYTHONUNBUFFERED=1
EXPOSE 3000

CMD ["operator-ui"]
