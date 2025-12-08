
import pytest
from datetime import datetime, timedelta, date, time, UTC
from sqlalchemy import select, text, func
from app.infrastructure.database import models
from app.domain.entities.assinatura import AssinaturaStatus, PlanoType
from app.presentation import schemas
from app.core.config import get_settings
from app.infrastructure.repositories.sqlalchemy_usuario_repository import SqlAlchemyUsuarioRepository
from app.infrastructure.repositories.sqlalchemy_assinatura_repository import SqlAlchemyAssinaturaRepository
from app.infrastructure.repositories.sqlalchemy_turno_repository import SqlAlchemyTurnoRepository
from app.application.use_cases.usuarios.criar_usuario import CriarUsuarioUseCase
from app.application.use_cases.turnos.criar_turno import CriarTurnoUseCase
from app.domain.exceptions.freemium_exception import LimiteTurnosExcedidoException
from app.infrastructure.database.uow import SqlAlchemyUnitOfWork
from unittest.mock import MagicMock

# Helper to verify DB state
async def get_user_subscription(db, user_id):
    stmt = select(models.Assinatura).where(models.Assinatura.telegram_user_id == user_id)
    result = await db.execute(stmt)
    return result.scalar()

@pytest.mark.asyncio
async def test_novo_usuario_ganha_trial(db_session):
    """Test 1: New User gets 14-day Trial."""
    db = db_session
    telegram_id = 90001
    
    # Clean up
    await db.execute(text(f"DELETE FROM usuarios WHERE telegram_user_id = {telegram_id}"))
    await db.execute(text(f"DELETE FROM assinaturas WHERE telegram_user_id = {telegram_id}"))
    await db.commit()
    
    repo_user = SqlAlchemyUsuarioRepository(db)
    repo_sub = SqlAlchemyAssinaturaRepository(db)
    uow = SqlAlchemyUnitOfWork(db)
    use_case = CriarUsuarioUseCase(uow)
    
    payload = schemas.UsuarioCreate(telegram_user_id=telegram_id, nome="User Trial", numero_funcionario="TR001")
    await use_case.execute(payload)
    
    sub = await get_user_subscription(db, telegram_id)
    assert sub is not None
    assert sub.status == AssinaturaStatus.TRIALING.value
    assert sub.plano == PlanoType.PRO.value
    
    # Check 14 days
    now = datetime.now(UTC)
    expected_end = now + timedelta(days=14)
    if sub.data_fim.tzinfo is None:
        sub.data_fim = sub.data_fim.replace(tzinfo=UTC)
        
    diff = abs((expected_end - sub.data_fim).total_seconds())
    assert diff < 120 # Tolerance

@pytest.mark.asyncio
async def test_usuario_trial_expirado_vira_free(db_session):
    """Test 2: Trial Expiration -> Free behavior."""
    db = db_session
    telegram_id = 90002
    
    # Setup: Create user with trial
    repo_user = SqlAlchemyUsuarioRepository(db)
    repo_sub = SqlAlchemyAssinaturaRepository(db)
    uow = SqlAlchemyUnitOfWork(db)
    use_case_create = CriarUsuarioUseCase(uow)
    
    # Clean up
    await db.execute(text(f"DELETE FROM usuarios WHERE telegram_user_id = {telegram_id}"))
    await db.execute(text(f"DELETE FROM assinaturas WHERE telegram_user_id = {telegram_id}"))
    await db.execute(text(f"DELETE FROM turnos WHERE telegram_user_id = {telegram_id}"))
    await db.commit()
    
    await use_case_create.execute(schemas.UsuarioCreate(telegram_user_id=telegram_id, nome="User Expired", numero_funcionario="TR002"))
    
    # Manually expire subscription
    stmt = text(f"UPDATE assinaturas SET status = 'canceled' WHERE telegram_user_id = {telegram_id}")
    await db.execute(stmt)
    await db.commit()
    
    # Verify is_free logic in Domain Entity (indirectly via behavior)
    # But first check DB state
    sub = await get_user_subscription(db, telegram_id)
    assert sub.status == 'canceled'
    # NOTE: The domain entity property `is_free` returns True if status != active/trialing OR plan == free.
    # So 'canceled' + 'pro' should be treated as free.
    
    # Insert 30 shifts
    for i in range(30):
        # We use direct SQL for speed
        await db.execute(text(f"""
            INSERT INTO turnos (telegram_user_id, tipo_turno_id, data_referencia, hora_inicio, hora_fim, duracao_minutos, criado_em, atualizado_em)
            VALUES ({telegram_id}, NULL, '2025-01-{i+1:02d}', '09:00', '18:00', 540, NOW(), NOW())
        """))
    await db.commit()
    
    # Try to create 31st shift
    uow = SqlAlchemyUnitOfWork(db)
    calendar_mock = MagicMock()
    uc_turno = CriarTurnoUseCase(uow, settings=get_settings(), calendar_service=MagicMock(), caldav_sync_task_port=calendar_mock)
    # Mock settings to ensure limit is 30
    uc_turno.settings.free_tier_max_shifts = 30
    
    with pytest.raises(LimiteTurnosExcedidoException):
        await uc_turno.execute(
            telegram_user_id=telegram_id,
            data_referencia=date(2025, 1, 31),
            hora_inicio=time(9,0),
            hora_fim=time(18,0),
            tipo="Regular"
        )

@pytest.mark.asyncio
async def test_bloqueio_free_30_turnos(db_session):
    """Test 3: Free Plan Enforcement (Strict 30)."""
    db = db_session
    telegram_id = 90003
    
    # Clean up
    await db.execute(text(f"DELETE FROM usuarios WHERE telegram_user_id = {telegram_id}"))
    await db.execute(text(f"DELETE FROM assinaturas WHERE telegram_user_id = {telegram_id}"))
    await db.execute(text(f"DELETE FROM turnos WHERE telegram_user_id = {telegram_id}"))
    await db.commit()
    
    # Create User + Manual Free Sub
    await db.execute(text(f"INSERT INTO usuarios (telegram_user_id, nome, numero_funcionario, criado_em, atualizado_em) VALUES ({telegram_id}, 'Free User', 'FREE123', NOW(), NOW())"))
    await db.execute(text(f"""
        INSERT INTO assinaturas (telegram_user_id, stripe_customer_id, status, plano, criado_em, atualizado_em)
        VALUES ({telegram_id}, 'cust_free', 'active', 'free', NOW(), NOW())
    """))
    await db.commit()
    
    # Insert 30 shifts
    # Using specific month (e.g., May 2025)
    for i in range(30):
        await db.execute(text(f"""
            INSERT INTO turnos (telegram_user_id, tipo_turno_id, data_referencia, hora_inicio, hora_fim, duracao_minutos, criado_em, atualizado_em)
            VALUES ({telegram_id}, NULL, '2025-05-{i+1:02d}', '09:00', '18:00', 540, NOW(), NOW())
        """))
    await db.commit()
    
    # Try 31st
    uow = SqlAlchemyUnitOfWork(db)
    calendar_mock = MagicMock()
    uc_turno = CriarTurnoUseCase(uow, settings=get_settings(), calendar_service=MagicMock(), caldav_sync_task_port=calendar_mock)
    uc_turno.settings.free_tier_max_shifts = 30

    with pytest.raises(LimiteTurnosExcedidoException):
        await uc_turno.execute(
            telegram_user_id=telegram_id,
            data_referencia=date(2025, 5, 31),
            hora_inicio=time(9,0),
            hora_fim=time(18,0)
        )

@pytest.mark.asyncio
async def test_usuario_legacy_autocorrecao(db_session):
    """Test 4: Legacy User (No Signature) -> Auto-create -> Limit Check."""
    db = db_session
    telegram_id = 90004
    
    # Clean up
    await db.execute(text(f"DELETE FROM usuarios WHERE telegram_user_id = {telegram_id}"))
    await db.execute(text(f"DELETE FROM assinaturas WHERE telegram_user_id = {telegram_id}"))
    await db.execute(text(f"DELETE FROM turnos WHERE telegram_user_id = {telegram_id}"))
    await db.commit()
    
    # Create Legacy User (No Assinatura)
    await db.execute(text(f"INSERT INTO usuarios (telegram_user_id, nome, numero_funcionario, criado_em, atualizado_em) VALUES ({telegram_id}, 'Legacy User', 'LEGACY123', NOW(), NOW())"))
    await db.commit()
    
    # Verify no signature
    sub = await get_user_subscription(db, telegram_id)
    assert sub is None
    
    # Create 1st Shift
    uow = SqlAlchemyUnitOfWork(db)
    calendar_mock = MagicMock()
    uc_turno = CriarTurnoUseCase(uow, settings=get_settings(), calendar_service=MagicMock(), caldav_sync_task_port=calendar_mock)
    
    await uc_turno.execute(
        telegram_user_id=telegram_id,
        data_referencia=date(2025, 6, 1),
        hora_inicio=time(8,0),
        hora_fim=time(12,0)
    )
    
    # Verify Signature WAS created
    sub_after = await get_user_subscription(db, telegram_id)
    assert sub_after is not None
    assert sub_after.plano == PlanoType.FREE.value
    assert sub_after.status == AssinaturaStatus.ACTIVE.value
    
    # Now verify blocking still works (add 29 more to reach 30, then fail 31st)
    for i in range(29):
        await db.execute(text(f"""
            INSERT INTO turnos (telegram_user_id, tipo_turno_id, data_referencia, hora_inicio, hora_fim, duracao_minutos, criado_em, atualizado_em)
            VALUES ({telegram_id}, NULL, '2025-06-{i+2:02d}', '09:00', '18:00', 540, NOW(), NOW())
        """))
    await db.commit()
    
    # Try 31st (1 + 29 = 30 existing)
    with pytest.raises(LimiteTurnosExcedidoException):
         await uc_turno.execute(
            telegram_user_id=telegram_id,
            # 1st was 2025-06-01.
            # Loop added 29 shifts: 2025-06-02 to 2025-06-30.
            # Total 30 shifts.
            # Try add another on 2025-06-15 (overlapping day doesn't matter for count)
            data_referencia=date(2025, 6, 15),
            hora_inicio=time(13,0),
            hora_fim=time(17,0)
        )
