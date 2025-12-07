import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import date, time
from app.application.use_cases.turnos.criar_turno import CriarTurnoUseCase
from app.domain.entities.turno import Turno
from app.domain.entities.assinatura import Assinatura
from app.domain.exceptions.freemium_exception import LimiteTurnosExcedidoException

@pytest.fixture
def mock_turno_repo():
    repo = AsyncMock()
    # Setup default return for criar to return the input turno (mock persistence)
    repo.criar.side_effect = lambda t: t
    repo.atualizar.side_effect = lambda t: t
    return repo

@pytest.fixture
def mock_assinatura_repo():
    return AsyncMock()

@pytest.fixture
def mock_settings(monkeypatch):
    # Mock get_settings to return controlled limit
    mock_settings_obj = MagicMock()
    mock_settings_obj.free_tier_max_shifts = 30
    
    monkeypatch.setattr("app.application.use_cases.turnos.criar_turno.get_settings", lambda: mock_settings_obj)
    return mock_settings_obj

@pytest.fixture
def use_case(mock_turno_repo, mock_assinatura_repo):
    session = AsyncMock() # Mock Unit of Work session
    mock_calendar_service = MagicMock()
    return CriarTurnoUseCase(mock_turno_repo, mock_assinatura_repo, mock_calendar_service, session)

@pytest.mark.asyncio
async def test_create_shift_free_user_within_limit(use_case, mock_assinatura_repo, mock_turno_repo, mock_settings, monkeypatch):
    # Setup: User is Free, Count is 29 (Limit 30)
    user_id = 123
    mock_assinatura_repo.get_by_user_id.return_value = Assinatura(
        id=1, telegram_user_id=user_id, stripe_customer_id="cust_1", stripe_subscription_id=None,
        status="active", plano="free", data_inicio=None, data_fim=None, 
        criado_em=None, atualizado_em=None
    )
    mock_turno_repo.contar_por_periodo.return_value = 29
    
    mock_turno_repo.contar_por_periodo.return_value = 29
    
    # Mock CalDAV success handled via injection in fixture
    # But we need access to the mock inside the fixture to set result?
    # Actually, default magicmock returns another magicmock, truthy.
    # We can check specific behavior if we extracted the mock from the use_case object.
    
    # For this test, we just care that it doesn't fail. Use injected mock behavior.
    
    result = await use_case.execute(
        telegram_user_id=user_id,
        data_referencia=date(2025, 1, 15),
        hora_inicio=time(8, 0),
        hora_fim=time(12, 0),
        tipo="Trabalho"
    )

    assert isinstance(result, Turno)
    mock_turno_repo.criar.assert_called_once()

@pytest.mark.asyncio
async def test_create_shift_free_user_exceed_limit(use_case, mock_assinatura_repo, mock_turno_repo, mock_settings):
    # Setup: User is Free, Count is 30 (Limit 30)
    user_id = 123
    mock_assinatura_repo.get_by_user_id.return_value = Assinatura(
        id=1, telegram_user_id=user_id, stripe_customer_id="cust_1", stripe_subscription_id=None,
        status="active", plano="free", data_inicio=None, data_fim=None, 
        criado_em=None, atualizado_em=None
    )
    mock_turno_repo.contar_por_periodo.return_value = 30

    with pytest.raises(LimiteTurnosExcedidoException):
        await use_case.execute(
            telegram_user_id=user_id,
            data_referencia=date(2025, 1, 15),
            hora_inicio=time(8, 0),
            hora_fim=time(12, 0)
        )
    
    # Ensure creation was NOT called
    mock_turno_repo.criar.assert_not_called()

@pytest.mark.asyncio
async def test_create_shift_pro_user_ignores_limit(use_case, mock_assinatura_repo, mock_turno_repo, mock_settings, monkeypatch):
    # Setup: User is Pro, Count is 1000
    user_id = 123
    mock_assinatura_repo.get_by_user_id.return_value = Assinatura(
        id=1, telegram_user_id=user_id, stripe_customer_id="cust_1", stripe_subscription_id="sub_1",
        status="active", plano="pro", data_inicio=None, data_fim=None, 
        criado_em=None, atualizado_em=None
    )
    mock_turno_repo.contar_por_periodo.return_value = 1000

    mock_turno_repo.contar_por_periodo.return_value = 1000

    # Mock CalDAV success (handled by injected mock)

    await use_case.execute(
        telegram_user_id=user_id,
        data_referencia=date(2025, 1, 15),
        hora_inicio=time(8, 0),
        hora_fim=time(12, 0)
    )

    mock_turno_repo.criar.assert_called_once()
    # Ensure validation logic was skipped (optimization)
    mock_turno_repo.contar_por_periodo.assert_not_called()

@pytest.mark.asyncio
async def test_create_shift_caldav_failure_is_ignored(use_case, mock_assinatura_repo, mock_turno_repo, mock_settings, monkeypatch):
    # Setup: Pro user
    user_id = 123
    mock_assinatura_repo.get_by_user_id.return_value = Assinatura(
        id=1, telegram_user_id=user_id, stripe_customer_id="cust_1", stripe_subscription_id="sub_1",
        status="active", plano="pro", data_inicio=None, data_fim=None, 
        criado_em=None, atualizado_em=None
    )
    
    # Mock CalDAV failure
    use_case.calendar_service.sync_event.side_effect = Exception("CalDAV Error")

    result = await use_case.execute(
        telegram_user_id=user_id,
        data_referencia=date(2025, 1, 15),
        hora_inicio=time(8, 0),
        hora_fim=time(12, 0),
        tipo="Trabalho"
    )

    # Should succeed despite CalDAV error
    assert isinstance(result, Turno)
    mock_turno_repo.criar.assert_called_once()
