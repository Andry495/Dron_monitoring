from __future__ import annotations

import uvicorn

from monitor_core.api.app import create_app
from monitor_core.config import Settings


def main() -> None:
    settings = Settings()
    app = create_app(settings)
    uvicorn.run(app, host=settings.api_host, port=settings.api_port, log_level="info")


if __name__ == "__main__":
    main()
