import asyncio
import logging
import contextlib

import uvicorn




async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("gestao_turnos_api")

    logger.info("Inicializando API Backend...")

    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())





