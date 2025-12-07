"""
Onboarding conversation handler for new user registration.

Handles the multi-step user registration flow.
"""
import logging

import httpx
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

from src.api_client import usuario_client

logger = logging.getLogger(__name__)

# Estados do ConversationHandler
AGUARDANDO_NOME, AGUARDANDO_NUMERO = range(2)


async def iniciar_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o processo de onboarding para coletar dados do usuário."""
    await update.message.reply_text(
        "👋 Bem-vindo! Para começar a registrar seus turnos, preciso de algumas informações.\n\n"
        "Por favor, me diga seu *nome completo*:",
        parse_mode="Markdown"
    )
    return AGUARDANDO_NOME


async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o nome do usuário e pede o número de funcionário."""
    nome = update.message.text.strip()
    
    if len(nome) < 3:
        await update.message.reply_text(
            "❌ Nome muito curto. Por favor, digite seu nome completo:"
        )
        return AGUARDANDO_NOME
    
    # Armazenar temporariamente no contexto
    context.user_data['nome'] = nome
    
    await update.message.reply_text(
        f"✅ Nome: *{nome}*\n\n"
        "Agora, me diga seu *número de funcionário*:",
        parse_mode="Markdown"
    )
    return AGUARDANDO_NUMERO


async def receber_numero(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o número de funcionário e finaliza o cadastro."""
    numero = update.message.text.strip()
    
    if len(numero) < 1:
        await update.message.reply_text(
            "❌ Número inválido. Por favor, digite seu número de funcionário:"
        )
        return AGUARDANDO_NUMERO
    
    nome = context.user_data.get('nome')
    user_id = update.effective_user.id
    
    # Cadastrar no backend
    try:
        await usuario_client.criar_usuario(user_id, nome, numero)
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 400:
            await update.message.reply_text(
                "❌ Este número de funcionário já está cadastrado. "
                "Por favor, use outro número:"
            )
            return AGUARDANDO_NUMERO
        else:
            logger.error(
                "Erro no cadastro",
                extra={"user_id": user_id, "status": exc.response.status_code}
            )
            await update.message.reply_text(
                "❌ Erro ao cadastrar. Tente novamente mais tarde."
            )
            return ConversationHandler.END
    except Exception as e:
        logger.error("Erro no cadastro", extra={"user_id": user_id, "error": str(e)})
        await update.message.reply_text(
            "❌ Erro ao cadastrar. Tente novamente mais tarde."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"✅ Cadastro concluído!\n\n"
        f"📝 Nome: *{nome}*\n"
        f"🆔 Número: *{numero}*\n\n"
        "Agora você já pode registrar seus turnos! Envie algo como:\n"
        "`<local> <hora_inicio> as <hora_fim>`\n"
        "Exemplo: `Hospital 08:00 as 16:00`",
        parse_mode="Markdown"
    )
    
    # Limpar dados temporários
    context.user_data.clear()
    
    return ConversationHandler.END


async def cancelar_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela o processo de onboarding."""
    await update.message.reply_text(
        "❌ Cadastro cancelado. Use /start quando quiser se cadastrar."
    )
    context.user_data.clear()
    return ConversationHandler.END
