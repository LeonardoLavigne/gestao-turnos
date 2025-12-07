"""
Basic command handlers for Telegram bot.

Handles: /start, /ajuda, /assinar, /perfil
"""
import logging

from telegram import Update
from telegram.ext import ContextTypes

from app.config import get_settings
from app.services.stripe_service import StripeService
from app.infrastructure.telegram.api_client import usuario_client

logger = logging.getLogger(__name__)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para comando /start."""
    await update.message.reply_text(
        "Olá! Envie mensagens como:\n"
        "<local> <hora_inicio> as <hora_fim>\n"
        "Exemplo: Hospital 08:00 as 16:00"
    )


async def ajuda_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Envia mensagem de ajuda com lista de comandos."""
    await update.message.reply_text(
        "ℹ️ **Ajuda - Gestão de Turnos**\n\n"
        "Comandos disponíveis:\n"
        "/start - Iniciar cadastro\n"
        "/assinar - Assinar Plano Pro\n"
        "/mes - Relatório do mês atual\n"
        "/semana - Relatório da semana atual\n"
        "/remover - Remover turnos recentes\n"
        "/menu - Menu interativo\n\n"
        "Para registrar um turno, envie:\n"
        "`<local> <inicio> as <fim>`\n"
        "Ex: `Hospital 07:00 as 19:00`",
        parse_mode="Markdown"
    )


async def assinar_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Gera link de checkout para assinatura Pro."""
    user = update.effective_user
    try:
        checkout_url = StripeService.create_checkout_session(user.id)
        await update.message.reply_text(
            f"🚀 **Faça o upgrade para o Plano Pro!**\n\n"
            f"Clique no link abaixo para assinar:\n[Assinar Agora]({checkout_url})\n\n"
            f"Ou copie o link:\n`{checkout_url}`\n\n"
            f"Após o pagamento, sua assinatura será ativada automaticamente.",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error("Erro ao gerar checkout", extra={"user_id": user.id, "error": str(e)})
        await update.message.reply_text(
            "Erro ao gerar link de pagamento. Tente novamente mais tarde."
        )


async def perfil_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra o perfil do usuário ou inicia fluxo de edição."""
    user_id = update.effective_user.id
    
    perfil = await usuario_client.buscar_usuario(user_id)
    
    if not perfil:
        await update.message.reply_text(
            "⚠️ Você ainda não está cadastrado!\n\n"
            "Por favor, use o comando /start para completar seu cadastro."
        )
        return
    
    await update.message.reply_text(
        f"👤 **Seu Perfil**\n\n"
        f"📝 Nome: *{perfil['nome']}*\n"
        f"🆔 Número: *{perfil['numero_funcionario']}*\n\n"
        f"💎 **Assinatura**\n"
        f"Status: `{perfil.get('assinatura_status', 'inactive')}`\n"
        f"Plano: `{perfil.get('assinatura_plano', 'free')}`\n"
        f"📅 Cadastrado em: {perfil['criado_em'][:10]}",
        parse_mode="Markdown"
    )
