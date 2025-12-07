import pytest
from unittest.mock import AsyncMock, MagicMock
from src.handlers.commands import start_command, ajuda_command, perfil_command, assinar_command

@pytest.mark.asyncio
async def test_start_command():
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await start_command(update, context)
    update.message.reply_text.assert_called_once()
    args, _ = update.message.reply_text.call_args
    assert "Olá!" in args[0]

@pytest.mark.asyncio
async def test_ajuda_command():
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    await ajuda_command(update, context)
    update.message.reply_text.assert_called_once()
    args, _ = update.message.reply_text.call_args
    assert "Ajuda" in args[0]

@pytest.mark.asyncio
async def test_perfil_command_nao_cadastrado(monkeypatch):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    # Mock usuario_client.buscar_usuario returning None
    mock_buscar = AsyncMock(return_value=None)
    monkeypatch.setattr("src.handlers.commands.usuario_client.buscar_usuario", mock_buscar)

    await perfil_command(update, context)
    
    update.message.reply_text.assert_called_once()
    args, _ = update.message.reply_text.call_args
    assert "ainda não está cadastrado" in args[0]

@pytest.mark.asyncio
async def test_perfil_command_cadastrado(monkeypatch):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    # Mock usuario_client.buscar_usuario returning User data
    user_data = {
        "nome": "Test User",
        "numero_funcionario": "007",
        "assinatura_status": "active",
        "assinatura_plano": "pro",
        "criado_em": "2025-01-01T00:00:00"
    }
    mock_buscar = AsyncMock(return_value=user_data)
    monkeypatch.setattr("src.handlers.commands.usuario_client.buscar_usuario", mock_buscar)

    await perfil_command(update, context)
    
    update.message.reply_text.assert_called_once()
    args, _ = update.message.reply_text.call_args
    assert "Test User" in args[0]
    assert "007" in args[0]

@pytest.mark.asyncio
async def test_assinar_command(monkeypatch):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()

    mock_checkout = AsyncMock(return_value="http://stripe.url")
    monkeypatch.setattr("src.handlers.commands.usuario_client.criar_checkout_session", mock_checkout)

    await assinar_command(update, context)
    
    update.message.reply_text.assert_called_once()
    args, _ = update.message.reply_text.call_args
    assert "http://stripe.url" in args[0]
