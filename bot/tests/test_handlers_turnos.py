import pytest
from unittest.mock import AsyncMock, MagicMock
from src.handlers.turnos import registrar_turno_msg, remover_command
from src.parsers import ParsedTurno
from datetime import date

@pytest.fixture
def mock_deps(monkeypatch):
    # Mock usuario_autorizado in utils (source) so it works everywhere it's imported
    monkeypatch.setattr("src.utils.usuario_autorizado", lambda uid: True)
    
    # Mock get_settings
    settings = MagicMock()
    settings.timezone = "UTC"
    monkeypatch.setattr("src.handlers.turnos.get_settings", lambda: settings)

@pytest.mark.asyncio
async def test_registrar_turno_msg_success(mock_deps, monkeypatch):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.text = "Hospital 08:00 as 16:00"
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.user_data = {}

    # Mock buscar_usuario (user exists AND has active subscription)
    user_mock = {"id": 1, "assinatura_status": "active"}
    # Patching the method on the instance imported in api_client so it affects decorators too
    monkeypatch.setattr("src.api_client.usuario_client.buscar_usuario", AsyncMock(return_value=user_mock))

    # Mock criar_turno
    mock_turno = {
        "id": 1, "tipo": "Hospital", 
        "hora_inicio": "08:00", "hora_fim": "16:00", 
        "data_referencia": "2025-01-01",
        "duracao_minutos": 480
    }
    monkeypatch.setattr("src.handlers.turnos.turno_client.criar_turno", AsyncMock(return_value=mock_turno))

    await registrar_turno_msg(update, context)

    update.message.reply_text.assert_called_once()
    args, _ = update.message.reply_text.call_args
    assert "Registrado Hospital" in args[0]

@pytest.mark.asyncio
async def test_registrar_turno_msg_parse_error(mock_deps, monkeypatch):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.text = "Texto invalido"
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.user_data = {}
    
    # Mock user authorized and subscribed
    user_mock = {"id": 1, "assinatura_status": "active"}
    monkeypatch.setattr("src.api_client.usuario_client.buscar_usuario", AsyncMock(return_value=user_mock))

    await registrar_turno_msg(update, context)

    update.message.reply_text.assert_called_once()
    assert "inválida" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_remover_command_success(mock_deps, monkeypatch):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    # Mock listar_turnos_recentes
    mock_turnos = [
        {"id": 1, "data_referencia": "2025-01-01", "hora_inicio": "08:00", "hora_fim": "16:00", "tipo": "Hospital"}
    ]
    monkeypatch.setattr("src.handlers.turnos.turno_client.listar_turnos_recentes", AsyncMock(return_value=mock_turnos))

    await remover_command(update, context)

    update.message.reply_text.assert_called_once()
    # Check for keyboard
    kwargs = update.message.reply_text.call_args.kwargs
    assert "reply_markup" in kwargs
    
@pytest.mark.asyncio
async def test_remover_command_empty(mock_deps, monkeypatch):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    monkeypatch.setattr("src.handlers.turnos.turno_client.listar_turnos_recentes", AsyncMock(return_value=[]))

    await remover_command(update, context)
    
    update.message.reply_text.assert_called_with("Nenhum turno recente encontrado.")
