import pytest
from datetime import datetime, timedelta, UTC
from sqlalchemy import select, text
from app.infrastructure.database import models
from app.presentation import schemas

@pytest.mark.asyncio
async def test_criar_usuario_com_trial(db_session_rls):
    """Testa se ao criar usuário, cria assinatura trial de 14 dias."""
    db = db_session_rls
    
    # Mock user payload
    telegram_id = 123456789
    payload = schemas.UsuarioCreate(
        telegram_user_id=telegram_id,
        nome="Teste Trial",
        numero_funcionario="TRIAL123"
    )
    
    
    # Set RLS context FIRST (is_local=False so it persists)
    await db.execute(text(f"SELECT set_config('app.current_user_id', '{telegram_id}', false)"))
    
    # Ensure user does not exist (RLS allows deleting own row)
    await db.execute(text(f"DELETE FROM usuarios WHERE telegram_user_id = {telegram_id}"))
    await db.execute(text(f"DELETE FROM assinaturas WHERE telegram_user_id = {telegram_id}"))
    await db.commit()
    
    # 1. Create user
    # 1. Create user via UseCase
    from app.infrastructure.repositories.sqlalchemy_usuario_repository import SqlAlchemyUsuarioRepository
    from app.infrastructure.repositories.sqlalchemy_assinatura_repository import SqlAlchemyAssinaturaRepository
    from app.application.use_cases.usuarios.criar_usuario import CriarUsuarioUseCase
    
    usuario_repo = SqlAlchemyUsuarioRepository(db)
    assinatura_repo = SqlAlchemyAssinaturaRepository(db)
    use_case = CriarUsuarioUseCase(usuario_repo, assinatura_repo)
    
    usuario = await use_case.execute(payload)
    assert usuario.telegram_user_id == telegram_id
    
    # 2. Verify subscription created
    stmt = select(models.Assinatura).where(
        models.Assinatura.telegram_user_id == telegram_id
    )
    result = await db.execute(stmt)
    assinatura = result.scalar()
    
    assert assinatura is not None
    assert assinatura.status == "trialing"
    assert assinatura.plano == "pro"
    assert assinatura.stripe_customer_id == f"trial_{telegram_id}"
    
    # Check dates
    now = datetime.now(UTC)
    assert assinatura.data_inicio is not None
    assert assinatura.data_fim is not None
    
    # Handle naive datetime from DB (assuming stored as UTC)
    data_inicio = assinatura.data_inicio
    if data_inicio.tzinfo is None:
        data_inicio = data_inicio.replace(tzinfo=UTC)
        
    data_fim = assinatura.data_fim
    if data_fim.tzinfo is None:
        data_fim = data_fim.replace(tzinfo=UTC)
    
    # Tolerância de 1 minuto para início
    assert (now - data_inicio).total_seconds() < 60
    
    # Fim ~ 14 dias depois
    expected_end = now + timedelta(days=14)
    # Check if end date is roughly 14 days from now (within 1 minute tolerance)
    diff_seconds = abs((expected_end - data_fim).total_seconds())
    assert diff_seconds < 60
