from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models import Assinatura

class SubscriptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Ignorar webhooks e rotas públicas
        if request.url.path.startswith("/webhook") or request.url.path in ["/docs", "/openapi.json"]:
            return await call_next(request)

        # Para requisições do Telegram (updates), a verificação é complexa aqui
        # pois o body é stream. O ideal é verificar no nível do handler do bot.
        # Mas se tivermos endpoints de API protegidos, este middleware serve.
        
        # MUDANÇA DE PLANO: Middleware HTTP não é o melhor lugar para bloquear 
        # comandos de bot que chegam via polling ou webhook misturado.
        # Vou manter este arquivo como placeholder para futura API REST,
        # mas a proteção real será via Decorator no bot.
        
        response = await call_next(request)
        return response

async def check_subscription(telegram_user_id: int, db: AsyncSession) -> bool:
    """
    Verifica se o usuário tem assinatura ativa.
    """
    stmt = select(Assinatura).where(
        Assinatura.telegram_user_id == telegram_user_id,
        Assinatura.status.in_(["active", "trialing"])
    )
    result = await db.execute(stmt)
    assinatura = result.scalar()
    
    return assinatura is not None
