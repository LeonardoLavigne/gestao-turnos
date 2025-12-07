"""
FastAPI application for Gestão de Turnos.

Provides REST API endpoints for managing work shifts (turnos),
users, and reports with Row-Level Security (RLS) for multi-tenancy.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import Response

from app.infrastructure.middleware import RLSMiddleware, InternalSecurityMiddleware
from app.api import webhook, health, pages
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import turnos, usuarios, relatorios, assinaturas, auth
from app.infrastructure.logger import setup_logging
from app.domain.exceptions.freemium_exception import LimiteTurnosExcedidoException

# Configurar logs na inicialização
setup_logging()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Setup
    yield
    # Cleanup

app = FastAPI(
    title="Gestão de Turnos API",
    description="API com RLS e Integração CalDAV",
    version="1.0.0",
    lifespan=lifespan,
)



@app.exception_handler(LimiteTurnosExcedidoException)
async def freemium_exception_handler(request: Request, exc: LimiteTurnosExcedidoException):
    return Response(
        content=f'{{"detail": "{str(exc)}"}}',
        status_code=403,
        media_type="application/json"
    )

# Registrar Webhooks (antes do middleware RLS para evitar bloqueio)
app.include_router(webhook.router)

# Registrar Health Check e Pages (públicos)
app.include_router(health.router)
app.include_router(pages.router)

# Registrar middleware RLS
app.add_middleware(RLSMiddleware)
app.add_middleware(InternalSecurityMiddleware) # Security Last (First to execute)

# Configurar CORS (Deve ser o último adicionado para ser o PRIMEIRO a executar)
from app.core.config import get_settings
settings = get_settings()

print(f"DEBUG: Loaded CORS Origins: {settings.backend_cors_origins}")

if settings.backend_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

from app.domain.exceptions import AcessoNegadoException

@app.exception_handler(AcessoNegadoException)
async def acesso_negado_handler(request: Request, exc: AcessoNegadoException):
    return Response(
        content=f'{{"detail": "{str(exc)}"}}',
        status_code=403,
        media_type="application/json"
    )


# =============================================================================
# Rotas da API (Business Logic)
# =============================================================================

# Prefixos ajudam a organizar a URL (ex: /api/v1/turnos)
app.include_router(turnos.router, prefix="/turnos", tags=["Turnos"])
app.include_router(usuarios.router, prefix="/usuarios", tags=["Usuários"])
app.include_router(relatorios.router, prefix="/relatorios", tags=["Relatórios"])
app.include_router(assinaturas.router, prefix="/assinaturas", tags=["Assinaturas"])
app.include_router(auth.router, prefix="/auth", tags=["Autenticação"])
