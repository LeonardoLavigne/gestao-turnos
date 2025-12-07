import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.config import get_settings
from app.domain.entities.assinatura import Assinatura, PlanoType, AssinaturaStatus
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_pdf_endpoint_forbidden_for_free_user(monkeypatch):
    """
    Verify that a Free user receives 403 Forbidden when accessing the PDF endpoint.
    """
    settings = get_settings()
    
    # Mock AssinaturaRepository to return a Free subscription
    mock_repo = AsyncMock()
    mock_repo.get_by_user_id.return_value = Assinatura(
        id=1, telegram_user_id=123, stripe_customer_id="cust_1", stripe_subscription_id=None,
        status=AssinaturaStatus.ACTIVE, plano=PlanoType.FREE, 
        data_inicio=None, data_fim=None, criado_em=None, atualizado_em=None
    )
    
    # Patch the repository injection in main.py
    # Since main.py instantiates SqlAlchemyAssinaturaRepository(db), we need to mock the class
    mock_repo_cls = MagicMock(return_value=mock_repo)
    monkeypatch.setattr("app.infrastructure.repositories.sqlalchemy_assinatura_repository.SqlAlchemyAssinaturaRepository", mock_repo_cls)

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {
            "X-Internal-Secret": settings.internal_api_key,
            "X-Telegram-User-ID": "123"
        }
        # Request access to PDF
        response = await ac.get("/relatorios/mes/pdf?ano=2025&mes=1", headers=headers)
        
        # Assert 403 Forbidden
        assert response.status_code == 403
        assert "exclusiva para assinantes Premium" in response.json()["detail"]

@pytest.mark.asyncio
async def test_pdf_endpoint_allowed_for_pro_user(monkeypatch):
    """
    Verify that a Pro user is allowed (status code non-403) when accessing the PDF endpoint.
    """
    settings = get_settings()
    
    # Mock AssinaturaRepository to return a Pro subscription
    mock_repo = AsyncMock()
    mock_repo.get_by_user_id.return_value = Assinatura(
        id=1, telegram_user_id=456, stripe_customer_id="cust_2", stripe_subscription_id="sub_2",
        status=AssinaturaStatus.ACTIVE, plano=PlanoType.PRO, 
        data_inicio=None, data_fim=None, criado_em=None, atualizado_em=None
    )
    
    mock_repo_cls = MagicMock(return_value=mock_repo)
    monkeypatch.setattr("app.infrastructure.repositories.sqlalchemy_assinatura_repository.SqlAlchemyAssinaturaRepository", mock_repo_cls)
    
    # Also mock ListarTurnosPeriodoUseCase to avoid db errors
    mock_use_case = AsyncMock() # The instance has async methods
    mock_use_case.execute.return_value = []
    
    mock_use_case_cls = MagicMock(return_value=mock_use_case) # The constructor is sync
    monkeypatch.setattr("app.application.use_cases.turnos.listar_turnos.ListarTurnosPeriodoUseCase", mock_use_case_cls)
    
    # Mock crud.get_usuario_by_telegram_id (used in main.py)
    monkeypatch.setattr("app.crud.get_usuario_by_telegram_id", AsyncMock(return_value=None))
    
    # Mock pdf generation
    monkeypatch.setattr("app.main.gerar_pdf_relatorio", lambda *args: b"%PDF-1.4...")
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        headers = {
            "X-Internal-Secret": settings.internal_api_key,
            "X-Telegram-User-ID": "456"
        }
        response = await ac.get("/relatorios/mes/pdf?ano=2025&mes=1", headers=headers)
        
        # Should be 200 OK
        assert response.status_code == 200
