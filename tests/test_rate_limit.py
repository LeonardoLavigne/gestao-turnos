import pytest
import time
from unittest.mock import AsyncMock, MagicMock
from app.infrastructure.telegram.decorators import rate_limit, user_message_timestamps, RATE_LIMIT_MSG, RATE_LIMIT_WINDOW

@pytest.mark.asyncio
async def test_rate_limit_decorator():
    # Mock do objeto Update e Context
    update = MagicMock()
    update.effective_user.id = 12345
    update.message.reply_text = AsyncMock()
    
    context = MagicMock()
    
    # Função mockada decorada
    mock_func = AsyncMock(return_value="success")
    decorated_func = rate_limit(mock_func)
    
    # Limpar estado do rate limit
    user_message_timestamps.clear()
    
    # 1. Executar N vezes dentro do limite
    for _ in range(RATE_LIMIT_MSG):
        result = await decorated_func(update, context)
        assert result == "success"
        
    # 2. Executar N+1 vez (deve ser bloqueado)
    result = await decorated_func(update, context)
    assert result is None  # Retorna None quando bloqueado
    update.message.reply_text.assert_called_with("⚠️ **Muitas mensagens!** Aguarde um pouco.")
    
    # 3. Simular passagem do tempo (limpar timestamps)
    # Como não podemos esperar 60s no teste, vamos manipular o dicionário diretamente
    # ou mockar time.time. Vamos manipular o dicionário para ser mais rápido.
    user_message_timestamps[12345] = [] # Reset manual
    
    # 4. Deve funcionar novamente
    result = await decorated_func(update, context)
    assert result == "success"
