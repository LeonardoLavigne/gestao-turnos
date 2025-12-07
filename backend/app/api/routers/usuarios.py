from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database.session import get_db
from app.presentation import schemas
from app.infrastructure.database import models
from app.infrastructure.repositories.sqlalchemy_usuario_repository import SqlAlchemyUsuarioRepository
from app.application.use_cases.usuarios.criar_usuario import CriarUsuarioUseCase
from app.application.use_cases.usuarios.atualizar_usuario import AtualizarUsuarioUseCase
from app.api.deps import (
    get_usuario_repo,
    get_criar_usuario_use_case,
    get_atualizar_usuario_use_case,
    get_current_user_id,
)

router = APIRouter()

@router.get(
    "/me",
    response_model=schemas.UsuarioRead,
    summary="Buscar perfil do usuário logado",
)
async def get_me(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
    repo: SqlAlchemyUsuarioRepository = Depends(get_usuario_repo),
):
    """Busca os dados do próprio usuário autenticado (via Token ou Header)."""
    # Reutiliza a lógica de busca por ID
    return await get_usuario(current_user_id, db, repo)


@router.get(
    "/{telegram_user_id}",
    response_model=schemas.UsuarioRead,
    summary="Buscar usuário por Telegram ID",
)
async def get_usuario(
    telegram_user_id: int,
    db: AsyncSession = Depends(get_db), # Direct DB needed for eager load (custom query)
    repo: SqlAlchemyUsuarioRepository = Depends(get_usuario_repo),
):
    """Busca um usuário pelo seu Telegram User ID."""
    usuario = await repo.buscar_por_telegram_id(telegram_user_id)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    # 🌟 Buscar assinatura para enriquecer resposta (eager loading manual)
    # Mantendo isso aqui por enquanto, pois é lógica de apresentação/query específica
    stmt = select(models.Assinatura).where(
        models.Assinatura.telegram_user_id == telegram_user_id
    )
    result = await db.execute(stmt)
    assinatura = result.scalar()
    
    # 🌟 Contar turnos do mês atual (para controle do plano Free)
    from datetime import date
    from sqlalchemy import func
    today = date.today()
    start_date = date(today.year, today.month, 1)
    if today.month == 12:
        end_date = date(today.year + 1, 1, 1)
    else:
        end_date = date(today.year, today.month + 1, 1) # Primeiro dia do mês seguinte (exclusivo)

    # Precisamos do ID interno do usuário (FK na tabela Turno é owner_id)
    # CORREÇÃO: O modelo Turno usa telegram_user_id direto, não FK para tabela usuario
    count_stmt = select(func.count()).select_from(models.Turno).where(
        models.Turno.telegram_user_id == telegram_user_id,
        models.Turno.data_referencia >= start_date,
        models.Turno.data_referencia < end_date
    )
    count_result = await db.execute(count_stmt)
    turnos_mes = count_result.scalar() or 0

    # Converter para schema e preencher campos extras
    usuario_read = schemas.UsuarioRead.model_validate(usuario)
    usuario_read.turnos_registrados_mes_atual = turnos_mes

    if assinatura:
        usuario_read.assinatura_status = assinatura.status
        usuario_read.assinatura_plano = assinatura.plano
    
    return usuario_read


@router.post(
    "",
    response_model=schemas.UsuarioRead,
    status_code=201,
    summary="Criar novo usuário",
)
async def criar_usuario(
    usuario_in: schemas.UsuarioCreate,
    repo: SqlAlchemyUsuarioRepository = Depends(get_usuario_repo),
    use_case: CriarUsuarioUseCase = Depends(get_criar_usuario_use_case),
):
    """Cria um novo usuário no sistema."""
    # Check existence
    existe = await repo.buscar_por_telegram_id(usuario_in.telegram_user_id)
    if existe:
        raise HTTPException(status_code=400, detail="Usuário já cadastrado")
    
    usuario = await use_case.execute(usuario_in)
    return usuario


@router.put(
    "/{telegram_user_id}",
    response_model=schemas.UsuarioRead,
    summary="Atualizar usuário",
)
async def atualizar_usuario(
    telegram_user_id: int,
    usuario_in: schemas.UsuarioUpdate,
    use_case: AtualizarUsuarioUseCase = Depends(get_atualizar_usuario_use_case),
):
    """Atualiza dados de um usuário existente."""
    usuario = await use_case.execute(telegram_user_id, usuario_in)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario
