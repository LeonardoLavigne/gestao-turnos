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
from app.api.routers import turnos, usuarios, relatorios, assinaturas
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

# ✅ Registrar middleware RLS
app.add_middleware(RLSMiddleware)
app.add_middleware(InternalSecurityMiddleware) # Security Last (First to execute)


# =============================================================================
# Rotas da API (Business Logic)
# =============================================================================

# Prefixos ajudam a organizar a URL (ex: /api/v1/turnos)
app.include_router(turnos.router, prefix="/turnos", tags=["Turnos"])
app.include_router(usuarios.router, prefix="/usuarios", tags=["Usuários"])
app.include_router(relatorios.router, prefix="/relatorios", tags=["Relatórios"])
app.include_router(assinaturas.router, prefix="/assinaturas", tags=["Assinaturas"])
