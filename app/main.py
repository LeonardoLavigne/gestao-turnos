"""
FastAPI application for Gestão de Turnos.

Provides REST API endpoints for managing work shifts (turnos),
users, and reports with Row-Level Security (RLS) for multi-tenancy.
"""
from datetime import date
import calendar

from fastapi import FastAPI, Depends, Query, Request, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session

from .database import Base, engine, get_db
from . import crud, schemas, models
from .reports import gerar_pdf_relatorio
from app.infrastructure.middleware import RLSMiddleware
from app.api import webhook, health, pages
from app.infrastructure.logger import setup_logging

# Configurar logs na inicialização
setup_logging()

app = FastAPI(
    title="Gestão de Turnos",
    description="API para gestão de turnos de trabalho com multi-tenancy via RLS",
    version="1.0.0",
)

# Registrar Webhooks (antes do middleware RLS para evitar bloqueio)
app.include_router(webhook.router)

# Registrar Health Check (público)
app.include_router(health.router)
app.include_router(pages.router)

# ✅ Registrar middleware RLS
app.add_middleware(RLSMiddleware)


# =============================================================================
# Endpoints de Turnos
# =============================================================================

@app.post(
    "/turnos",
    response_model=schemas.TurnoRead,
    tags=["Turnos"],
    summary="Criar novo turno",
)
def criar_turno(
    request: Request,
    turno_in: schemas.TurnoCreate,
    db: Session = Depends(get_db),
):
    """Cria um novo turno de trabalho para o usuário autenticado via RLS."""
    turno = crud.criar_turno(db, turno_in)
    return schemas.TurnoRead.from_model(turno)


@app.get(
    "/turnos",
    response_model=list[schemas.TurnoRead],
    tags=["Turnos"],
    summary="Listar turnos por período",
)
def listar_turnos(
    request: Request,
    inicio: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    fim: date = Query(..., description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Lista turnos do usuário dentro do período especificado."""
    turnos = crud.listar_turnos_periodo(db, inicio, fim)
    return [schemas.TurnoRead.from_model(t) for t in turnos]


@app.get(
    "/turnos/recentes",
    response_model=list[schemas.TurnoRead],
    tags=["Turnos"],
    summary="Listar turnos recentes",
)
def listar_recentes(
    request: Request,
    limit: int = Query(5, ge=1, le=50, description="Número máximo de turnos"),
    db: Session = Depends(get_db),
):
    """Lista os turnos mais recentes do usuário."""
    turnos = crud.listar_turnos_recentes(db, limit)
    return [schemas.TurnoRead.from_model(t) for t in turnos]


@app.delete(
    "/turnos/{turno_id}",
    status_code=204,
    tags=["Turnos"],
    summary="Deletar turno",
)
def deletar_turno(
    request: Request,
    turno_id: int,
    db: Session = Depends(get_db),
):
    """Deleta um turno do usuário."""
    sucesso = crud.delete_turno(db, turno_id)
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
def relatorio_periodo(
    request: Request,
    inicio: date = Query(..., description="Data inicial (YYYY-MM-DD)"),
    fim: date = Query(..., description="Data final (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """Gera relatório de turnos para um período customizado."""
    turnos = crud.listar_turnos_periodo(db, inicio, fim)
    return crud.gerar_relatorio_periodo(turnos, inicio, fim)


@app.get(
    "/relatorios/semana",
    response_model=schemas.RelatorioPeriodo,
    tags=["Relatórios"],
    summary="Relatório semanal",
)
def relatorio_semana(
    request: Request,
    ano: int = Query(..., ge=2000, le=2100),
    semana: int = Query(..., ge=1, le=53),
    db: Session = Depends(get_db),
):
    """Gera relatório de turnos para uma semana específica."""
    inicio = date.fromisocalendar(ano, semana, 1)
    fim = date.fromisocalendar(ano, semana, 7)
    turnos = crud.listar_turnos_periodo(db, inicio, fim)
    return crud.gerar_relatorio_periodo(turnos, inicio, fim)


@app.get(
    "/relatorios/mes",
    response_model=schemas.RelatorioPeriodo,
    tags=["Relatórios"],
    summary="Relatório mensal",
)
def relatorio_mes(
    request: Request,
    ano: int = Query(..., ge=2000, le=2100),
    mes: int = Query(..., ge=1, le=12),
    db: Session = Depends(get_db),
):
    """Gera relatório de turnos para um mês específico."""
    inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo_dia)
    turnos = crud.listar_turnos_periodo(db, inicio, fim)
    return crud.gerar_relatorio_periodo(turnos, inicio, fim)


@app.get(
    "/relatorios/mes/pdf",
    tags=["Relatórios"],
    summary="Relatório mensal em PDF",
)
def relatorio_mes_pdf(
    request: Request,
    ano: int = Query(..., ge=2000, le=2100),
    mes: int = Query(..., ge=1, le=12),
    telegram_user_id: int = Query(None, description="ID do usuário para cabeçalho"),
    db: Session = Depends(get_db),
):
    """Gera relatório de turnos em PDF para um mês específico."""
    inicio = date(ano, mes, 1)
    ultimo_dia = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo_dia)
    
    turnos = crud.listar_turnos_periodo(db, inicio, fim)
    
    # Buscar informações do usuário se telegram_user_id for fornecido
    usuario_info = None
    if telegram_user_id:
        usuario = crud.get_usuario_by_telegram_id(db, telegram_user_id)
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
def get_usuario(
    telegram_user_id: int,
    db: Session = Depends(get_db),
):
    """Busca um usuário pelo seu Telegram User ID."""
    usuario = crud.get_usuario_by_telegram_id(db, telegram_user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario


@app.post(
    "/usuarios",
    response_model=schemas.UsuarioRead,
    status_code=201,
    tags=["Usuários"],
    summary="Criar novo usuário",
)
def criar_usuario(
    usuario_in: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
):
    """Cria um novo usuário no sistema."""
    existe = crud.get_usuario_by_telegram_id(db, usuario_in.telegram_user_id)
    if existe:
        raise HTTPException(status_code=400, detail="Usuário já cadastrado")
    
    usuario = crud.criar_usuario(db, usuario_in)
    return usuario


@app.put(
    "/usuarios/{telegram_user_id}",
    response_model=schemas.UsuarioRead,
    tags=["Usuários"],
    summary="Atualizar usuário",
)
def atualizar_usuario(
    telegram_user_id: int,
    usuario_in: schemas.UsuarioUpdate,
    db: Session = Depends(get_db),
):
    """Atualiza dados de um usuário existente."""
    usuario = crud.atualizar_usuario(db, telegram_user_id, usuario_in)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario
