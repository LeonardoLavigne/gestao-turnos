from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.infrastructure.database.session import get_db
from app.presentation import schemas
from app.infrastructure.database import models
from app.infrastructure.repositories.sqlalchemy_usuario_repository import SqlAlchemyUsuarioRepository
from app.infrastructure.repositories.sqlalchemy_assinatura_repository import SqlAlchemyAssinaturaRepository
from app.application.use_cases.usuarios.criar_usuario import CriarUsuarioUseCase
from app.application.use_cases.usuarios.atualizar_usuario import AtualizarUsuarioUseCase

router = APIRouter()

@router.get(
    "/{telegram_user_id}",
    response_model=schemas.UsuarioRead,
    summary="Buscar usuário por Telegram ID",
)
async def get_usuario(
    telegram_user_id: int,
    db: AsyncSession = Depends(get_db),
):
    """Busca um usuário pelo seu Telegram User ID."""
    repo = SqlAlchemyUsuarioRepository(db)
    usuario = await repo.buscar_por_telegram_id(telegram_user_id)
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


@router.post(
    "",
    response_model=schemas.UsuarioRead,
    status_code=201,
    summary="Criar novo usuário",
)
async def criar_usuario(
    usuario_in: schemas.UsuarioCreate,
    db: AsyncSession = Depends(get_db),
):
    """Cria um novo usuário no sistema."""
    usuario_repo = SqlAlchemyUsuarioRepository(db)
    assinatura_repo = SqlAlchemyAssinaturaRepository(db)
    use_case = CriarUsuarioUseCase(usuario_repo, assinatura_repo)

    # Check existence
    existe = await usuario_repo.buscar_por_telegram_id(usuario_in.telegram_user_id)
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
    db: AsyncSession = Depends(get_db),
):
    """Atualiza dados de um usuário existente."""
    usuario_repo = SqlAlchemyUsuarioRepository(db)
    use_case = AtualizarUsuarioUseCase(usuario_repo)

    usuario = await use_case.execute(telegram_user_id, usuario_in)
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    return usuario
