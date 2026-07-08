from __future__ import annotations

import logging

import uvicorn
from pydantic_settings import BaseSettings, SettingsConfigDict

from operator_ui.app import create_app

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    host: str = "0.0.0.0"
    port: int = 3000
    core_url: str = "http://localhost:8080"
    simulator_url: str = "http://localhost:8070"


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    uvicorn.run(create_app(settings), host=settings.host, port=settings.port)
