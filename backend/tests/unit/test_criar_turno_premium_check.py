import pytest
from unittest.mock import AsyncMock, MagicMock
from app.application.use_cases.turnos.criar_turno import CriarTurnoUseCase
from app.domain.entities.turno import Turno
from app.domain.entities.assinatura import Assinatura, AssinaturaStatus, PlanoType
from app.domain.uow import AbstractUnitOfWork
from datetime import date, time

# Mock UoW Helper
class MockUoW(AbstractUnitOfWork):
    def __init__(self, turno_repo, assinatura_repo):
        self.turnos = turno_repo
        self.assinaturas = assinatura_repo
        self.usuarios = AsyncMock() 
    
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass
    async def commit(self):
        pass
    async def rollback(self):
        pass

@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.contar_por_periodo = AsyncMock(return_value=0)
    repo.criar = AsyncMock(side_effect=lambda t: t) # Return same turno
    repo.atualizar = AsyncMock(side_effect=lambda t: t)
    repo.buscar_tipo_por_nome = AsyncMock(return_value=None)
    return repo

@pytest.fixture
def mock_assinatura_repo():
    repo = MagicMock()
    return repo

@pytest.mark.asyncio
async def test_caldav_sync_skipped_for_free_user(mock_repo, mock_assinatura_repo):
    # Setup
    uow = MockUoW(mock_repo, mock_assinatura_repo)
    mock_calendar_service = MagicMock()
    mock_settings = MagicMock()
    mock_settings.free_tier_max_shifts = 10
    use_case = CriarTurnoUseCase(uow, mock_calendar_service, mock_settings)
    
    # Mock Free Assinatura
    free_assinatura = Assinatura(
        id=1, telegram_user_id=123, 
        plano=PlanoType.FREE, status=AssinaturaStatus.ACTIVE,
        stripe_customer_id="sub_123", stripe_subscription_id=None,
        data_inicio=None, data_fim=None, criado_em=None, atualizado_em=None
    )
    mock_assinatura_repo.get_by_user_id = AsyncMock(return_value=free_assinatura)

    # Execute
    await use_case.execute(123, date(2025, 1, 1), time(8, 0), time(16, 0), "Hospital")
    
    # Assert
    mock_calendar_service.sync_event.assert_not_called()
    mock_repo.criar.assert_called_once()


@pytest.mark.asyncio
async def test_caldav_sync_called_for_pro_user(mock_repo, mock_assinatura_repo):
    # Setup
    uow = MockUoW(mock_repo, mock_assinatura_repo)
    mock_calendar_service = MagicMock()
    mock_settings = MagicMock()
    mock_settings.free_tier_max_shifts = 10
    use_case = CriarTurnoUseCase(uow, mock_calendar_service, mock_settings)
    
     # Mock Pro Assinatura
    pro_assinatura = Assinatura(
        id=1, telegram_user_id=123, 
        plano=PlanoType.PRO, status=AssinaturaStatus.ACTIVE,
        stripe_customer_id="cust_1", stripe_subscription_id="sub_123",
        data_inicio=None, data_fim=None, criado_em=None, atualizado_em=None
    )
    mock_assinatura_repo.get_by_user_id = AsyncMock(return_value=pro_assinatura)
    
    # Execute
    await use_case.execute(123, date(2025, 1, 1), time(8, 0), time(16, 0), "Hospital")
    
    # Assert
    mock_calendar_service.sync_event.assert_called_once()
    mock_repo.criar.assert_called_once()
