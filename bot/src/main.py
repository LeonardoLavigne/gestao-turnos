"""
Telegram Bot Entrypoint.
"""
import logging
from src.bot import build_application

# Configure logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

from src.config import get_settings

if __name__ == "__main__":
    logger.info("Iniciando Bot Telegram...")
    application = build_application()
    settings = get_settings()
    
    if settings.execution_mode == "webhook":
        logger.info(f"Modo Webhook: Escutando em {settings.host}:{settings.port} com URL {settings.webhook_url}")
        application.run_webhook(
            listen=settings.host,
            port=settings.port,
            webhook_url=settings.webhook_url,
            secret_token=settings.internal_api_key, # Segurança extra do Telegram
        )
    else:
        logger.info("Modo Polling iniciado")
        application.run_polling()
