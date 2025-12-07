import pytest
from unittest.mock import AsyncMock, MagicMock
from src.handlers.menu import menu_command, button_handler

@pytest.fixture
def mock_deps(monkeypatch):
    monkeypatch.setattr("src.handlers.menu.usuario_autorizado", lambda uid: True)
    
@pytest.mark.asyncio
async def test_menu_command(mock_deps):
    update = MagicMock()
    update.message.reply_text = AsyncMock()
    context = MagicMock()
    
    await menu_command(update, context)
    
    update.message.reply_text.assert_called_once()
    assert "Menu Principal" in update.message.reply_text.call_args[0][0]

@pytest.mark.asyncio
async def test_button_handler_unauthorized(monkeypatch):
    update = MagicMock()
    query = update.callback_query
    query.from_user.id = 123
    query.answer = AsyncMock()
    query.edit_message_text = AsyncMock()
    context = MagicMock()
    
    monkeypatch.setattr("src.handlers.menu.usuario_autorizado", lambda uid: False)
    
    await button_handler(update, context)
    
    query.edit_message_text.assert_called_with("Não autorizado.")

@pytest.mark.asyncio
async def test_button_handler_del(mock_deps, monkeypatch):
    update = MagicMock()
    query = update.callback_query
    query.data = "del_123"
    query.from_user.id = 1
    query.answer = AsyncMock()
    context = MagicMock()
    
    mock_handle_delete = AsyncMock()
    monkeypatch.setattr("src.handlers.menu.handle_delete_callback", mock_handle_delete)
    
    await button_handler(update, context)
    
    mock_handle_delete.assert_called_with(query, 1, "123")

@pytest.mark.asyncio
async def test_button_handler_menu_main(mock_deps):
    update = MagicMock()
    query = update.callback_query
    query.data = "menu_main"
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()
    context = MagicMock()
    
    await button_handler(update, context)
    
    query.edit_message_text.assert_called_once()
    assert "Menu Principal" in query.edit_message_text.call_args[0][0]

@pytest.mark.asyncio
async def test_button_handler_menu_relatorios(mock_deps):
    update = MagicMock()
    query = update.callback_query
    query.data = "menu_relatorios"
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()
    context = MagicMock()
    
    await button_handler(update, context)
    
    query.edit_message_text.assert_called_once()
    assert "Relatórios" in query.edit_message_text.call_args[0][0]

@pytest.mark.asyncio
async def test_button_handler_menu_semana_atual(mock_deps, monkeypatch):
    update = MagicMock()
    query = update.callback_query
    query.data = "menu_semana_atual"
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()
    context = MagicMock()
    
    monkeypatch.setattr("src.handlers.menu.gerar_relatorio_semana_atual", AsyncMock(return_value="Relatorio Semana"))
    
    await button_handler(update, context)
    
    query.edit_message_text.assert_called_with("Relatorio Semana")

@pytest.mark.asyncio
async def test_button_handler_menu_mes_atual(mock_deps, monkeypatch):
    update = MagicMock()
    query = update.callback_query
    query.data = "menu_mes_atual"
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()
    context = MagicMock()
    
    monkeypatch.setattr("src.handlers.menu.gerar_relatorio_mes_atual", AsyncMock(return_value="Relatorio Mes"))
    
    await button_handler(update, context)
    
    query.edit_message_text.assert_called_with("Relatorio Mes")

@pytest.mark.asyncio
async def test_button_handler_menu_perfil(mock_deps, monkeypatch):
    update = MagicMock()
    query = update.callback_query
    query.data = "menu_perfil"
    query.edit_message_text = AsyncMock()
    query.answer = AsyncMock()
    context = MagicMock()
    query.from_user.id = 123
    
    user_mock = {"nome": "Leo", "numero_funcionario": "001", "criado_em": "2025-01-01"}
    # Patch usuario_client used inside the function
    # It imports from src.api_client import usuario_client
    monkeypatch.setattr("src.api_client.usuario_client.buscar_usuario", AsyncMock(return_value=user_mock))
    
    await button_handler(update, context)
    
    args = query.edit_message_text.call_args[0][0]
    assert "Seu Perfil" in args
    assert "Leo" in args
