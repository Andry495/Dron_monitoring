from __future__ import annotations

import uvicorn

from turret_sim.app import create_app


def main() -> None:
    app = create_app()
    uvicorn.run(app, host="0.0.0.0", port=8030, log_level="info")


if __name__ == "__main__":
    main()
