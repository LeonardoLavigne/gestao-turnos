"""
Middleware para Row-Level Security (RLS) no PostgreSQL.

Configura o contexto do usuário atual (telegram_user_id) para cada requisição,
permitindo que as políticas RLS do PostgreSQL isolem os dados automaticamente.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.orm import Session

from app.database import SessionLocal


class RLSMiddleware(BaseHTTPMiddleware):
    """
    Middleware que configura app.current_user_id no PostgreSQL
    para cada requisição baseado no header X-Telegram-User-ID.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extrair telegram_user_id do header
        user_id = request.headers.get("X-Telegram-User-ID")
        
        if user_id:
            # Configurar contexto RLS no PostgreSQL
            db: Session = SessionLocal()
            try:
                # SET LOCAL funciona apenas dentro de uma transação
                db.execute(
                    "SET LOCAL app.current_user_id = :user_id",
                    {"user_id": int(user_id)}
                )
                db.commit()
            finally:
                db.close()
        
        # Processar request
        response = await call_next(request)
        return response
