
import pytest
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch
from app.main import app
from app.core.security import create_access_token
from app.core.config import get_settings
from app.api.deps import get_usuario_repo

@pytest.mark.asyncio
async def test_auth_login_success(monkeypatch):
    """Test login with mocked Telegram validation"""
    import hmac
    import hashlib
    
    # Mock settings
    settings = get_settings()
    monkeypatch.setattr(settings, "telegram_bot_token", "TEST_TOKEN")

    auth_date = int(1733600000)
    data_dict = {
        "id": 123456,
        "first_name": "Test",
        "username": "tester",
        "auth_date": auth_date
    }
    
    # Compute valid hash
    # "key=value" sorted
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(data_dict.items()))
    secret_key = hashlib.sha256(b"TEST_TOKEN").digest()
    valid_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    
    auth_data = data_dict.copy()
    auth_data["hash"] = valid_hash

    # Patch time.time to be close to auth_date
    with patch("time.time", return_value=auth_date + 100):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/auth/login", json=auth_data)
            
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["user"]["id"] == 123456

@pytest.mark.asyncio
async def test_dual_gatekeeper_bot_access():
    """Test accessing a protected route using Internal Secret (Bot Strategy)"""
    settings = get_settings()
    headers = {
        "X-Internal-Secret": settings.internal_api_key,
        "X-Telegram-User-ID": "999"
    }
    
    # We'll hit /usuarios/me or similar, or just a dummy endpoint. 
    # Let's hit /turnos/recentes which is protected
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # Need to mock the repository calls inside the route, otherwise it tries to connect to DB
        # But for middleware/deps check, 401 vs 200/500/etc is enough to prove Auth passed.
        # If Auth fails, we get 401 or 403.
        # If Auth passes, we get 200 or 500 (if DB fails).
        response = await ac.get("/turnos/recentes", headers=headers)
        
    # If we get past deps.py, we might hit DB error, but definitely NOT 401/403
    assert response.status_code != 401
    assert response.status_code != 403

@pytest.mark.asyncio
async def test_dual_gatekeeper_web_access(monkeypatch):
    """Test accessing a protected route using Bearer Token (Web Strategy)"""
    # Create valid user first
    # Or mock repository? 
    # Since we are using integration test, dependencies are real if not overridden due to overrides being empty in main app for now except session.
    # In test_integration, we are hitting the app.
    # Let's assume the user exists or mock the repo response.
    # Actually, GET /usuarios/me calls get_usuario which calls repo.buscar_por_telegram_id
    
    # We will mock get_usuario_repo to return a mock repo
    
    mock_repo = MagicMock()
    mock_data = {
        "id": 888, 
        "telegram_user_id": 888, 
        "first_name": "WebUser",
        "nome": "Web User", 
        "username": "web", 
        "numero_funcionario": "123",
        "criado_em": "2024-01-01T00:00:00",
        "atualizado_em": "2024-01-01T00:00:00"
    }
    mock_repo.buscar_por_telegram_id.return_value = mock_data
    # Async mock
    async def async_return(*args, **kwargs):
        return mock_data
    mock_repo.buscar_por_telegram_id.side_effect = async_return
    
    app.dependency_overrides[get_usuario_repo] = lambda: mock_repo

    token = create_access_token(subject="888")
    headers = {
        "Authorization": f"Bearer {token}"
    }
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
         # Hit /usuarios/me
         response = await ac.get("/usuarios/me", headers=headers)
         
    app.dependency_overrides = {}
         
    assert response.status_code == 200
    assert response.json()["telegram_user_id"] == 888

@pytest.mark.asyncio
async def test_dual_gatekeeper_fail():
    """Test access without credentials"""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
         response = await ac.get("/turnos/recentes")
         
    # Middleware or Deps should block
    # Logic: Middleware blocks if no Secret AND no Authorization header.
    assert response.status_code == 403
