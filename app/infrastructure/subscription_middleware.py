from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Assinatura

class SubscriptionMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Ignorar webhooks e rotas públicas
        if request.url.path.startswith("/webhook") or request.url.path in ["/docs", "/openapi.json"]:
            return await call_next(request)

        # Para requisições do Telegram (updates), a verificação é complexa aqui
        # pois o body é stream. O ideal é verificar no nível do handler do bot.
        # Mas se tivermos endpoints de API protegidos, este middleware serve.
        
        # Como este projeto é focado no Bot, a lógica de bloqueio deve estar
        # principalmente nos Handlers do Telegram ou em um Decorator.
        
        # MUDANÇA DE PLANO: Middleware HTTP não é o melhor lugar para bloquear 
        # comandos de bot que chegam via polling ou webhook misturado.
        # Vou manter este arquivo como placeholder para futura API REST,
        # mas a proteção real será via Decorator no bot.
        
        response = await call_next(request)
        return response

def check_subscription(telegram_user_id: int, db: Session) -> bool:
    """
    Verifica se o usuário tem assinatura ativa.
    """
    assinatura = db.query(Assinatura).filter(
        Assinatura.telegram_user_id == telegram_user_id,
        Assinatura.status.in_(["active", "trialing"])
    ).first()
    
    return assinatura is not None
