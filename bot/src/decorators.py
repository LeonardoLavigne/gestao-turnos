"""
Rate limiting and subscription decorators for Telegram bot handlers.
"""
import time
import logging
from collections import defaultdict
from functools import wraps

from telegram import Update
from telegram.ext import ContextTypes

from src.api_client import usuario_client

logger = logging.getLogger(__name__)

# Rate Limit: 5 mensagens por minuto por usuário
RATE_LIMIT_MSG = 5
RATE_LIMIT_WINDOW = 60
user_message_timestamps: dict[int, list[float]] = defaultdict(list)


def rate_limit(func):
    """
    Decorator para limitar taxa de requisições.
    Permite no máximo RATE_LIMIT_MSG mensagens por RATE_LIMIT_WINDOW segundos.
    """
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        now = time.time()
        
        # Limpar timestamps antigos
        user_message_timestamps[user_id] = [
            t for t in user_message_timestamps[user_id] 
            if now - t < RATE_LIMIT_WINDOW
        ]
        
        if len(user_message_timestamps[user_id]) >= RATE_LIMIT_MSG:
            logger.warning(
                "Rate limit exceeded",
                extra={"user_id": user_id, "count": len(user_message_timestamps[user_id])}
            )
            await update.message.reply_text("⚠️ **Muitas mensagens!** Aguarde um pouco.")
            return

        user_message_timestamps[user_id].append(now)
        return await func(update, context, *args, **kwargs)
    return wrapper


def subscription_required(func):
    """
    Decorator para exigir assinatura ativa.
    Permite comandos básicos (/start, /help, /assinar) sem assinatura.
    """
    @wraps(func)
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if not user:
             return
             
        user_id = user.id
        
        # Permitir comandos básicos sem assinatura
        if update.message and update.message.text:
            text = update.message.text
            if text.startswith(('/start', '/help', '/assinar', '/ajuda')):
                return await func(update, context, *args, **kwargs)

        # Verificar Cache (5 minutos)
        now = time.time()
        cached_status = context.user_data.get("sub_status")
        cached_time = context.user_data.get("sub_check_time", 0)
        
        if cached_status and (now - cached_time < 300):
            status = cached_status
        else:
            # Verificar assinatura via API
            try:
                usuario = await usuario_client.buscar_usuario(user_id)
                status = usuario.get("assinatura_status") if usuario else None
                
                # Atualizar Cache
                context.user_data["sub_status"] = status
                context.user_data["sub_check_time"] = now
            except Exception:
                logger.error(f"Erro ao verificar assinatura para {user_id}")
                status = None

        if status not in ("active", "trialing"):
            await update.message.reply_text(
                "🔒 **Funcionalidade Exclusiva para Assinantes**\n\n"
                "Você precisa de uma assinatura ativa para usar este recurso.\n"
                "Use /assinar para fazer o upgrade.",
                parse_mode="Markdown"
            )
            return
        
        return await func(update, context, *args, **kwargs)
    return wrapper
