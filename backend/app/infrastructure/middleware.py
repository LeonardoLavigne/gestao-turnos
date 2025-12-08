"""
Middleware para Row-Level Security (RLS) no PostgreSQL.

Configura o contexto do usuário atual (telegram_user_id) para cada requisição,
permitindo que as políticas RLS do PostgreSQL isolem os dados automaticamente.

NOTA: O RLS é aplicado em get_db() usando request.state.telegram_user_id,
garantindo que SET LOCAL seja executado na mesma transação das queries.
"""
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from app.core.config import get_settings
import secrets


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


class InternalSecurityMiddleware(BaseHTTPMiddleware):
    """
    Middleware que verifica o Shared Secret (Internal API Key)
    para garantir que requisições venham do Bot ou fontes confiáveis.
    """
    
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        
        # 1. Whitelist de rotas públicas
        # 1. Whitelist de rotas públicas
        if (
            path.startswith("/docs") or 
            path.startswith("/redoc") or 
            path.startswith("/openapi.json") or
            path.startswith("/health") or 
            path.startswith("/webhook") or
            path.startswith("/auth")
        ):
            return await call_next(request)
            
        # 2. Verificar Shared Secret
        settings = get_settings()
        secret = request.headers.get("X-Internal-Secret")
        
        # 2a. Se tem secret válido, passa (Bot)
        if secret and secrets.compare_digest(secret, settings.internal_api_key):
             return await call_next(request)
             
        # 2b. Se tem Authorization header ou Cookie de auth, passa (Web - validação real será no endpoint via deps)
        if request.headers.get("Authorization") or request.cookies.get("auth_token"):
            return await call_next(request)
        
        # 3. Bloquear se não tem nenhum dos dois
        return JSONResponse(
            status_code=403, 
            content={"detail": "Forbidden: Invalid or missing Internal Secret"}
        )
