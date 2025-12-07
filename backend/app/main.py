"""
FastAPI application for Gestão de Turnos.

Provides REST API endpoints for managing work shifts (turnos),
users, and reports with Row-Level Security (RLS) for multi-tenancy.
"""
from datetime import date
import calendar
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends, Query, Request, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from .database import Base, engine, get_db
from . import crud, schemas, models
from .reports import gerar_pdf_relatorio
from app.infrastructure.middleware import RLSMiddleware, InternalSecurityMiddleware
from app.api import webhook, health, pages
from app.infrastructure.logger import setup_logging
from sqlalchemy import select
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

# Registrar Health Check (público)
app.include_router(health.router)
app.include_router(pages.router)

# ✅ Registrar middleware RLS
app.add_middleware(RLSMiddleware)
app.add_middleware(InternalSecurityMiddleware) # Security Last (First to execute)


# =============================================================================
# Endpoints de Turnos
# =============================================================================

@app.post(
    "/turnos",
    response_model=schemas.TurnoRead,
    tags=["Turnos"],
    summary="Criar novo turno",
)
async def criar_turno(
    request: Request,
    turno_in: schemas.TurnoCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo turno de trabalho para o usuário autenticado via RLS."""
    # Obter telegram_user_id do state (setado pelo Middleware ou RLS)
    telegram_user_id = getattr(request.state, "telegram_user_id", None)
    if not telegram_user_id:
         # Fallback: tentar header diretamente se middleware falhar (redundancia)
         user_id_header = request.headers.get("X-Telegram-User-ID")
         if user_id_header:
             telegram_user_id = int(user_id_header)
         else:
             raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")
             
    from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
    from app.application.use_cases.turnos.criar_turno import CriarTurnoUseCase
    from app.infrastructure.repositories.sqlalchemy_assinatura_repository import SqlAlchemyAssinaturaRepository

    repo = SqlAlchemyTurnoRepository(db)
    assinatura_repo = SqlAlchemyAssinaturaRepository(db)
    use_case = CriarTurnoUseCase(repo, assinatura_repo, db)
    
    turno_entity = await use_case.execute(

        telegram_user_id=telegram_user_id,
        data_referencia=turno_in.data_referencia,
        hora_inicio=turno_in.hora_inicio,
        hora_fim=turno_in.hora_fim,
        tipo=turno_in.tipo,
        descricao_opcional=turno_in.descricao_opcional,
    )
    
    # Entity já tem tipo como string, compatível com schema diretamente
    return schemas.TurnoRead.model_validate(turno_entity)


@app.get(
    "/turnos",
    response_model=list[schemas.TurnoRead],
    tags=["Turnos"],
    summary="Listar turnos por período",
)
async def listar_turnos(
    request: Request,
    inicio: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    fim: date = Query(..., description="Data final (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """Lista turnos do usuário dentro do período especificado."""
    # Obter telegram_user_id do state
    telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                      (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")

    from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
    from app.application.use_cases.turnos.listar_turnos import ListarTurnosPeriodoUseCase

    repo = SqlAlchemyTurnoRepository(db)
    use_case = ListarTurnosPeriodoUseCase(repo)
    
    turnos = await use_case.execute(telegram_user_id, inicio, fim)
    return [schemas.TurnoRead.model_validate(t) for t in turnos]


@app.get(
    "/turnos/recentes",
    response_model=list[schemas.TurnoRead],
    tags=["Turnos"],
    summary="Listar turnos recentes",
)
async def listar_recentes(
    request: Request,
    limit: int = Query(5, ge=1, le=50, description="Número máximo de turnos"),
    db: AsyncSession = Depends(get_db),
):
    """Lista os turnos mais recentes do usuário."""
    # Obter telegram_user_id do state
    telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                      (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")

    from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
    from app.application.use_cases.turnos.listar_turnos import ListarTurnosRecentesUseCase

    repo = SqlAlchemyTurnoRepository(db)
    use_case = ListarTurnosRecentesUseCase(repo)

    turnos = await use_case.execute(telegram_user_id, limit)
    return [schemas.TurnoRead.model_validate(t) for t in turnos]


@app.delete(
    "/turnos/{turno_id}",
    status_code=204,
    tags=["Turnos"],
    summary="Deletar turno",
)
async def deletar_turno(
    request: Request,
    turno_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Deleta um turno do usuário."""
    # Obter telegram_user_id do state
    telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                      (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")

    from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
    from app.application.use_cases.turnos.deletar_turno import DeletarTurnoUseCase

    repo = SqlAlchemyTurnoRepository(db)
    use_case = DeletarTurnoUseCase(repo, db)

    sucesso = await use_case.execute(turno_id, telegram_user_id)
    if not sucesso:
        raise HTTPException(status_code=404, detail="Turno não encontrado")
    return None


# =============================================================================
# Endpoints de Relatórios
# =============================================================================

@app.get(
    "/relatorios/periodo",
    response_model=schemas.RelatorioPeriodo,
    tags=["Relatórios"],
    summary="Relatório por período customizado",
)
async def relatorio_periodo(
    request: Request,
    inicio: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    fim: date = Query(..., description="Data final (YYYY-MM-DD)"),
    db: AsyncSession = Depends(get_db),
):
    """Gera relatório de turnos para um período customizado."""
    # Obter telegram_user_id do state
    telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                      (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")

    from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
    from app.application.use_cases.relatorios.gerar_relatorio import GerarRelatorioUseCase

    repo = SqlAlchemyTurnoRepository(db)
    use_case = GerarRelatorioUseCase(repo)
    
    # Use Case retorna dataclass, Pydantic Schema valida
    return await use_case.execute(telegram_user_id, inicio, fim)


@app.get(
    "/relatorios/semana",
    response_model=schemas.RelatorioPeriodo,
    tags=["Relatórios"],
    summary="Relatório semanal",
)
async def relatorio_semana(
    request: Request,
    ano: int = Query(..., ge=2000, le=2100),
    semana: int = Query(..., ge=1, le=53),
    db: AsyncSession = Depends(get_db),
):
    """Gera relatório de turnos para uma semana específica."""
    # Obter telegram_user_id do state
    telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                      (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")

    inicio = date.fromisocalendar(ano, semana, 1)
    fim = date.fromisocalendar(ano, semana, 7)

    from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
    from app.application.use_cases.relatorios.gerar_relatorio import GerarRelatorioUseCase
    
    repo = SqlAlchemyTurnoRepository(db)
    use_case = GerarRelatorioUseCase(repo)

    return await use_case.execute(telegram_user_id, inicio, fim)


@app.get(
    "/relatorios/mes",
    response_model=schemas.RelatorioPeriodo,
    tags=["Relatórios"],
    summary="Relatório mensal",
)
async def relatorio_mes(
    request: Request,
    ano: int = Query(..., ge=2000, le=2100),
    mes: int = Query(..., ge=1, le=12),
    db: AsyncSession = Depends(get_db),
):
    """Gera relatório de turnos para um mês específico."""
    # Obter telegram_user_id do state
    telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                      (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
    if not telegram_user_id:
        raise HTTPException(status_code=401, detail="X-Telegram-User-ID obrigatório")

    inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo_dia)
    
    from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
    from app.application.use_cases.relatorios.gerar_relatorio import GerarRelatorioUseCase
    
    repo = SqlAlchemyTurnoRepository(db)
    use_case = GerarRelatorioUseCase(repo)

    return await use_case.execute(telegram_user_id, inicio, fim)


@app.get(
    "/relatorios/mes/pdf",
    tags=["Relatórios"],
    summary="Relatório mensal em PDF",
)
async def relatorio_mes_pdf(
    request: Request,
    ano: int = Query(..., ge=2000, le=2100),
    mes: int = Query(..., ge=1, le=12),
    telegram_user_id: int = Query(None, description="ID do usuário para cabeçalho"),
    db: AsyncSession = Depends(get_db),
):
    """Gera relatório de turnos em PDF para um mês específico."""
    inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo_dia)
    
    # Check user ID (header or param if bot)
    # logic in original code used telegram_user_id param OR implied context?
    # Original endpoint has telegram_user_id query param explicitly!
    if not telegram_user_id:
        # Tenta header
        telegram_user_id = getattr(request.state, "telegram_user_id", None) or \
                           (int(request.headers.get("X-Telegram-User-ID")) if request.headers.get("X-Telegram-User-ID") else None)
        
    if not telegram_user_id:
         raise HTTPException(status_code=401, detail="User ID required")

    from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
    from app.application.use_cases.turnos.listar_turnos import ListarTurnosPeriodoUseCase
    
    repo = SqlAlchemyTurnoRepository(db)
    use_case = ListarTurnosPeriodoUseCase(repo)
    
    turnos = await use_case.execute(telegram_user_id, inicio, fim)
    
    # Buscar informações do usuário se telegram_user_id for fornecido
    usuario_info = None
    if telegram_user_id:
        usuario = await crud.get_usuario_by_telegram_id(db, telegram_user_id)
        if usuario:
            usuario_info = {
                "nome": usuario.nome,
                "numero_funcionario": usuario.numero_funcionario
            }
    
    pdf_bytes = gerar_pdf_relatorio(turnos, inicio, fim, usuario_info)
    
    filename = f"relatorio_{ano}_{mes:02d}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# =============================================================================
# Endpoints de Usuários
# =============================================================================

@app.get(
    "/usuarios/{telegram_user_id}",
    response_model=schemas.UsuarioRead,
    tags=["Usuários"],
    summary="Buscar usuário por Telegram ID",
)
async def get_usuario(
    telegram_user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Busca um usuário pelo seu Telegram User ID."""
    usuario = await crud.get_usuario_by_telegram_id(db, telegram_user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # 🌟 Buscar assinatura para enriquecer resposta (eager loading manual)
    stmt = select(models.Assinatura).where(
        models.Assinatura.telegram_user_id == telegram_user_id
    )
    result = await db.execute(stmt)
    assinatura = result.scalar()
    
    # Converter para schema e preencher campos extras
    usuario_read = schemas.UsuarioRead.model_validate(usuario)
    if assinatura:
        usuario_read.assinatura_status = assinatura.status
        usuario_read.assinatura_plano = assinatura.plano
    
    return usuario_read


@app.post("/assinaturas/checkout")
async def criar_checkout(payload: schemas.CheckoutRequest):
    """
    Cria uma sessão de checkout do Stripe para o usuário.
    """
    from app.services.stripe_service import StripeService
    try:
        url = StripeService.create_checkout_session(payload.telegram_user_id)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post(
    "/usuarios",
    response_model=schemas.UsuarioRead,
    status_code=201,
    tags=["Usuários"],
    summary="Criar novo usuário",
)
async def criar_usuario(
    usuario_in: schemas.UsuarioCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo usuário no sistema."""
    existe = await crud.get_usuario_by_telegram_id(db, usuario_in.telegram_user_id)
    if existe:
        raise HTTPException(status_code=400, detail="Usuário já cadastrado")
    
    usuario = await crud.criar_usuario(db, usuario_in)
    return usuario


@app.put(
    "/usuarios/{telegram_user_id}",
    response_model=schemas.UsuarioRead,
    tags=["Usuários"],
    summary="Atualizar usuário",
)
async def atualizar_usuario(
    telegram_user_id: int,
    usuario_in: schemas.UsuarioUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Atualiza dados de um usuário existente."""
    usuario = await crud.atualizar_usuario(db, telegram_user_id, usuario_in)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario
