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

if __name__ == "__main__":
    logger.info("Iniciando Bot Telegram...")
    application = build_application()
    application.run_polling()
