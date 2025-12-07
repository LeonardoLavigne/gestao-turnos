import pytest
from unittest.mock import MagicMock, AsyncMock
import httpx
from src.api_client import TurnoAPIClient, UsuarioAPIClient, INTERNAL_API_KEY
from datetime import date

@pytest.fixture
def mock_httpx(monkeypatch):
    """
    Mocks httpx.AsyncClient to return a controlled AsyncMock instance.
    The instance methods (post, get, delete) will return a MagicMock (response) 
    when awaited, NOT another coroutine-producing mock.
    """
    # The client instance that will be used in the 'async with' block
    mock_client_instance = AsyncMock()
    
    # Context manager setup
    mock_client_instance.__aenter__.return_value = mock_client_instance
    mock_client_instance.__aexit__.return_value = None

    # Ensure get/post/delete are AsyncMocks (awaitable)
    # AND their return_value is a MagicMock (the Response object)
    # We will instantiate a new response mock in each test, or a default one here.
    
    # We assign them as AsyncMock attributes so we can configure them in tests
    mock_client_instance.post = AsyncMock()
    mock_client_instance.get = AsyncMock()
    mock_client_instance.delete = AsyncMock()

    # Factory that returns our mocked client
    mock_constructor = MagicMock(return_value=mock_client_instance)
    
    monkeypatch.setattr("httpx.AsyncClient", mock_constructor)
    
    return mock_client_instance

@pytest.mark.asyncio
async def test_criar_turno_success(mock_httpx):
    client = TurnoAPIClient()
    
    # Setup Response
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 1, "tipo": "Hospital"}
    mock_response.raise_for_status = MagicMock()
    
    # Configure Client to return this response
    mock_httpx.post.return_value = mock_response
    
    result = await client.criar_turno("Hospital", date(2025, 1, 1), "08:00", "16:00", 123)
    
    assert result["id"] == 1
    mock_httpx.post.assert_called_once()
    
    # Verify headers
    call_kwargs = mock_httpx.post.call_args.kwargs
    assert call_kwargs["headers"]["X-Internal-Secret"] == INTERNAL_API_KEY
    assert call_kwargs["headers"]["X-Telegram-User-ID"] == "123"

@pytest.mark.asyncio
async def test_listar_turnos_recentes(mock_httpx):
    client = TurnoAPIClient()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = [{"id": 1}]
    mock_response.raise_for_status = MagicMock()
    
    mock_httpx.get.return_value = mock_response
    
    result = await client.listar_turnos_recentes(123)
    assert len(result) == 1
    mock_httpx.get.assert_called_once()

@pytest.mark.asyncio
async def test_deletar_turno_success(mock_httpx):
    client = TurnoAPIClient()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()
    
    mock_httpx.delete.return_value = mock_response
    
    result = await client.deletar_turno(1, 123)
    assert result is True

@pytest.mark.asyncio
async def test_deletar_turno_not_found(mock_httpx):
    client = TurnoAPIClient()
    
    mock_response = MagicMock()
    mock_response.status_code = 404
    
    mock_httpx.delete.return_value = mock_response
    
    result = await client.deletar_turno(1, 123)
    assert result is False

@pytest.mark.asyncio
async def test_usuario_client_buscar_usuario(mock_httpx):
    client = UsuarioAPIClient()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"nome": "Leo"}
    
    mock_httpx.get.return_value = mock_response
    
    result = await client.buscar_usuario(123)
    assert result["nome"] == "Leo"

@pytest.mark.asyncio
async def test_usuario_client_criar_usuario(mock_httpx):
    client = UsuarioAPIClient()
    
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"id": 1}
    mock_response.raise_for_status = MagicMock()
    
    mock_httpx.post.return_value = mock_response
    
    await client.criar_usuario(123, "Leo", "001")
    mock_httpx.post.assert_called_once()
