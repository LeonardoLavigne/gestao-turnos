"""
Middleware para Row-Level Security (RLS) no PostgreSQL.

Configura o contexto do usuário atual (telegram_user_id) para cada requisição,
permitindo que as políticas RLS do PostgreSQL isolem os dados automaticamente.

NOTA: O RLS é aplicado em get_db() usando request.state.telegram_user_id,
garantindo que SET LOCAL seja executado na mesma transação das queries.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware


class RLSMiddleware(BaseHTTPMiddleware):
    """
    Middleware que extrai telegram_user_id do header X-Telegram-User-ID
    e armazena em request.state para uso posterior em get_db().
    
    O SET LOCAL é executado em get_db() para garantir que esteja
    na mesma transação das queries do endpoint.
    """
    
    async def dispatch(self, request: Request, call_next):
        # Extrair telegram_user_id do header e armazenar em request.state
        user_id = request.headers.get("X-Telegram-User-ID")
        
        if user_id:
            try:
                request.state.telegram_user_id = int(user_id)
            except ValueError:
                # Header inválido, ignorar
                pass
        
        # Processar request
        response = await call_next(request)
        return response
