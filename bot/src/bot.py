"""
Telegram Bot Application Builder.

This module provides the main entry point for building and configuring
the Telegram bot application with all handlers.
"""
import logging

from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from src.config import get_settings
from src.handlers.commands import (
    start_command,
    ajuda_command,
    assinar_command,
    perfil_command,
)
from src.handlers.onboarding import (
    AGUARDANDO_NOME,
    AGUARDANDO_NUMERO,
    iniciar_onboarding,
    receber_nome,
    receber_numero,
    cancelar_onboarding,
)
from src.handlers.turnos import (
    registrar_turno_msg,
    remover_command,
)
from src.handlers.relatorios import (
    relatorio_semana_command,
    relatorio_mes_command,
)
from src.handlers.menu import (
    menu_command,
    button_handler,
)

logger = logging.getLogger(__name__)


def build_application() -> Application:
    """
    Builds and configures the Telegram bot application.
    
    Returns:
        Configured Application instance ready to run
    """
    settings = get_settings()
    
    application = ApplicationBuilder().token(settings.telegram_bot_token).build()
    
    # ConversationHandler para onboarding de novos usuários
    onboarding_handler = ConversationHandler(
        entry_points=[CommandHandler("start", iniciar_onboarding)],
        states={
            AGUARDANDO_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome)],
            AGUARDANDO_NUMERO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_numero)],
        },
        fallbacks=[CommandHandler("cancel", cancelar_onboarding)],
    )
    
    # Registrar handlers na ordem correta
    # 1. ConversationHandler primeiro para capturar /start
    application.add_handler(onboarding_handler)
    
    # 2. Comandos simples
    application.add_handler(CommandHandler("ajuda", ajuda_command))
    application.add_handler(CommandHandler("help", ajuda_command))
    application.add_handler(CommandHandler("assinar", assinar_command))
    application.add_handler(CommandHandler("perfil", perfil_command))
    application.add_handler(CommandHandler("menu", menu_command))
    
    # 3. Comandos de relatórios
    application.add_handler(CommandHandler("semana", relatorio_semana_command))
    application.add_handler(CommandHandler("mes", relatorio_mes_command))
    
    # 4. Comando de remoção
    application.add_handler(CommandHandler("remover", remover_command))
    
    # 5. Handler para callbacks de inline keyboard
    application.add_handler(CallbackQueryHandler(button_handler))
    
    # 6. Handler para mensagens de texto (registro de turnos) - deve ser por último
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, registrar_turno_msg)
    )
    
    logger.info("Telegram bot application built successfully")
    
    return application
