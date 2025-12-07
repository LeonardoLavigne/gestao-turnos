import pytest
from unittest.mock import AsyncMock, MagicMock
from src.handlers.relatorios import relatorio_mes_command, relatorio_semana_command

@pytest.fixture
def mock_deps(monkeypatch):
    monkeypatch.setattr("src.handlers.relatorios.usuario_autorizado", lambda uid: True)
    settings = MagicMock()
    settings.timezone = "UTC"
    monkeypatch.setattr("src.handlers.relatorios.get_settings", lambda: settings)
    monkeypatch.setattr("src.handlers.relatorios.formatar_relatorio", lambda r: "Relatorio Formatado")

@pytest.mark.asyncio
async def test_relatorio_mes_default(mock_deps, monkeypatch):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = []

    mock_client = AsyncMock()
    mock_client.relatorio_mes.return_value = {}
    monkeypatch.setattr("src.handlers.relatorios.relatorio_client", mock_client)

    await relatorio_mes_command(update, context)
    
    mock_client.relatorio_mes.assert_called_once()
    update.message.reply_text.assert_called_with("Relatorio Formatado")

@pytest.mark.asyncio
async def test_relatorio_mes_arg(mock_deps, monkeypatch):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = ["01"]

    mock_client = AsyncMock()
    mock_client.relatorio_mes.return_value = {}
    monkeypatch.setattr("src.handlers.relatorios.relatorio_client", mock_client)

    await relatorio_mes_command(update, context)
    
    # check if called with month 1
    args = mock_client.relatorio_mes.call_args
    assert args[0][1] == 1 # mes

@pytest.mark.asyncio
async def test_relatorio_semana_default(mock_deps, monkeypatch):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = []

    mock_client = AsyncMock()
    mock_client.relatorio_semana.return_value = {}
    monkeypatch.setattr("src.handlers.relatorios.relatorio_client", mock_client)

    await relatorio_semana_command(update, context)
    
    mock_client.relatorio_semana.assert_called_once()

@pytest.mark.asyncio
async def test_relatorio_semana_7d(mock_deps, monkeypatch):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.args = ["7d"]

    mock_client = AsyncMock()
    mock_client.relatorio_periodo.return_value = {}
    monkeypatch.setattr("src.handlers.relatorios.relatorio_client", mock_client)

    await relatorio_semana_command(update, context)
    
    mock_client.relatorio_periodo.assert_called_once()
