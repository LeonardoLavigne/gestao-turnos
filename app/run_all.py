import asyncio
import logging
import contextlib

import uvicorn

from .telegram_bot import build_application


async def main() -> None:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("gestao_turnos")

    logger.info("Inicializando aplicação do Telegram...")
    application = build_application()

    poller_task: asyncio.Task | None = None
    try:
        await application.initialize()
        await application.start()
        logger.info("Bot do Telegram iniciado com sucesso.")

        if application.updater is not None:
            poller_task = asyncio.create_task(application.updater.start_polling())
            logger.info("Polling do Telegram iniciado.")
        else:
            logger.warning("Updater do Telegram não disponível; polling não iniciado.")
    except Exception as exc:  # pragma: no cover - apenas log de runtime
        logger.exception("Falha ao iniciar bot do Telegram: %s", exc)
        # mesmo que o bot falhe, ainda podemos servir a API

    config = uvicorn.Config(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=False,
    )
    server = uvicorn.Server(config)

    try:
        await server.serve()
    finally:
        logger.info("Encerrando aplicação do Telegram...")
        if poller_task:
            poller_task.cancel()
            with contextlib.suppress(Exception):
                await poller_task
        with contextlib.suppress(Exception):
            await application.stop()
            await application.shutdown()


if __name__ == "__main__":
    asyncio.run(main())





