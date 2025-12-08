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
import socket
import time

def wait_for_internet(host="api.telegram.org", port=443, timeout=5):
    """Aguardar conexão com a internet antes de iniciar."""
    logger.info(f"Aguardando resolução de DNS para {host}...")
    while True:
        try:
            _ = socket.getaddrinfo(host, port, proto=socket.IPPROTO_TCP)
            logger.info("DNS resolvido com sucesso.")
            break
        except socket.gaierror:
            logger.warning("Falha temporária no DNS, aguardando 2 segundos...")
            time.sleep(2)
        except Exception as e:
            logger.warning(f"Erro ao verificar conexão: {e}, aguardando 2 segundos...")
            time.sleep(2)



if __name__ == "__main__":
    wait_for_internet()
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
