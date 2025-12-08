import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import AsyncMock, MagicMock

from app.main import app
from app.core.config import get_settings
from app.domain.entities.assinatura import Assinatura, PlanoType, AssinaturaStatus
from app.api.deps import (
    get_assinatura_repo,
    get_usuario_repo,
    get_turno_repo,
    get_relatorio_service
)

@pytest.mark.asyncio
async def test_pdf_endpoint_forbidden_for_free_user():
    """
    Verify that a Free user receives 403 Forbidden when accessing the PDF endpoint.
    """
    settings = get_settings()
    
    # 1. Prepare Mock Repo
    mock_repo = AsyncMock()
    mock_repo.get_by_user_id.side_effect = lambda *args, **kwargs: Assinatura(
        id=1, telegram_user_id=123, stripe_customer_id="cust_1", stripe_subscription_id=None,
        status=AssinaturaStatus.ACTIVE, plano=PlanoType.FREE, 
        data_inicio=None, data_fim=None, criado_em=None, atualizado_em=None
    )
    
    # 2. Override Dependency
    app.dependency_overrides[get_assinatura_repo] = lambda: mock_repo
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            headers = {
                "X-Internal-Secret": settings.internal_api_key,
                "X-Telegram-User-ID": "123"
            }
            # Request access to PDF
            response = await ac.get("/relatorios/mes/pdf?ano=2025&mes=1", headers=headers)
            
            # Assert 403 Forbidden
            assert response.status_code == 403
            assert "Funcionalidade disponível apenas para usuários Premium" in response.json()["detail"]
    finally:
        app.dependency_overrides = {}

@pytest.mark.asyncio
async def test_pdf_endpoint_allowed_for_pro_user():
    """
    Verify that a Pro user is allowed (status code non-403) when accessing the PDF endpoint.
    """
    settings = get_settings()
    
    # 1. Mock AssinaturaRepository (Pro)
    mock_assinatura_repo = AsyncMock()
    mock_assinatura_repo.get_by_user_id.side_effect = lambda *args, **kwargs: Assinatura(
        id=1, telegram_user_id=456, stripe_customer_id="cust_2", stripe_subscription_id="sub_2",
        status=AssinaturaStatus.ACTIVE, plano=PlanoType.PRO, 
        data_inicio=None, data_fim=None, criado_em=None, atualizado_em=None
    )
    
    # 2. Mock Other Dependencies (avoid DB calls)
    mock_turno_repo = AsyncMock()
    mock_turno_repo.listar_por_periodo.return_value = []
    
    mock_usuario_repo = AsyncMock()
    mock_usuario_repo.buscar_por_telegram_id.return_value = None 
    
    # Mock PDF Service
    mock_pdf_service = MagicMock()
    mock_pdf_service.gerar_pdf_mes.return_value = b"%PDF-1.4..."
    
    # 3. Override Dependencies
    app.dependency_overrides[get_assinatura_repo] = lambda: mock_assinatura_repo
    app.dependency_overrides[get_turno_repo] = lambda: mock_turno_repo
    app.dependency_overrides[get_usuario_repo] = lambda: mock_usuario_repo
    app.dependency_overrides[get_relatorio_service] = lambda: mock_pdf_service
    
    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            headers = {
                "X-Internal-Secret": settings.internal_api_key,
                "X-Telegram-User-ID": "456"
            }
            response = await ac.get("/relatorios/mes/pdf?ano=2025&mes=1", headers=headers)
            
            # Should be 200 OK
            assert response.status_code == 200
            assert response.content == b"%PDF-1.4..."
    finally:
         app.dependency_overrides = {}
