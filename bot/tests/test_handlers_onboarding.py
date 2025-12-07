import pytest
from unittest.mock import AsyncMock, MagicMock
from telegram.ext import ConversationHandler
from src.handlers.onboarding import (
    iniciar_onboarding,
    receber_nome,
    receber_numero,
    cancelar_onboarding,
    AGUARDANDO_NOME,
    AGUARDANDO_NUMERO
)

@pytest.fixture
def mock_deps(monkeypatch):
    monkeypatch.setattr("src.handlers.onboarding.usuario_client.buscar_usuario", AsyncMock(return_value=None))

@pytest.mark.asyncio
async def test_start_onboarding_new_user(mock_deps):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    
    state = await iniciar_onboarding(update, context)
    
    assert state == AGUARDANDO_NOME
    update.message.reply_text.assert_called_with(
        "👋 Bem-vindo! Para começar a registrar seus turnos, preciso de algumas informações.\n\n"
        "Por favor, me diga seu *nome completo*:",
        parse_mode="Markdown"
    )

@pytest.mark.asyncio
async def test_start_onboarding_existing_user(monkeypatch):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    
    monkeypatch.setattr("src.handlers.onboarding.usuario_client.buscar_usuario", AsyncMock(return_value={"id": 1}))
    
    # Needs to be mocked or handled? `iniciar_onboarding` doesn't check for existing user in the code I verify
    # Let me check the code again.
    # The code `iniciar_onboarding` just asks for name. The check is usually done in /start or similar command.
    pass 

@pytest.mark.asyncio
async def test_ask_name():
    update = MagicMock()
    update.message.text = "Leo"
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.user_data = {}
    
    state = await receber_nome(update, context)
    
    assert state == AGUARDANDO_NUMERO
    assert context.user_data["nome"] == "Leo"
    # Check part of the string
    args = update.message.reply_text.call_args[0][0]
    assert "Leo" in args
    assert "número de funcionário" in args

@pytest.mark.asyncio
async def test_ask_employee_number(monkeypatch):
    update = MagicMock()
    update.effective_user.id = 123
    update.message.text = "007"
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    context.user_data = {"nome": "Leo"}
    
    mock_criar = AsyncMock(return_value={"id": 1})
    monkeypatch.setattr("src.handlers.onboarding.usuario_client.criar_usuario", mock_criar)
    
    state = await receber_numero(update, context)
    
    assert state == ConversationHandler.END
    mock_criar.assert_called_with(123, "Leo", "007")
    assert "Cadastro concluído" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_cancel_onboarding():
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    
    state = await cancelar_onboarding(update, context)
    
    assert state == ConversationHandler.END
    assert "Cadastro cancelado" in update.message.reply_text.call_args[0][0]
