
import pytest
from app import crud, models, schemas
from sqlalchemy import text, select
from datetime import datetime
from app.infrastructure.telegram.api_client import UsuarioAPIClient

# Mock the API client to test the logic or test the endpoint directly via test client?
# Since we are running in docker, we can use the existing test infrastructure.
# Let's create a test that calls the API endpoint directly using AsyncClient (via test_client if available) or use the existing pattern.

# Existing tests use `db_session_rls`.
# `tests/test_api.py` typically tests endpoints.

@pytest.mark.asyncio
async def test_get_usuario_com_plano(db_session_rls, client): # Assuming client fixture exists or we create one
    db = db_session_rls
    telegram_id = 999888777
    
    # Clean up
    await db.execute(text(f"SELECT set_config('app.current_user_id', '{telegram_id}', false)"))
    await db.execute(text(f"DELETE FROM usuarios WHERE telegram_user_id = {telegram_id}"))
    await db.execute(text(f"DELETE FROM assinaturas WHERE telegram_user_id = {telegram_id}"))
    await db.commit()
    
    # Create user and subscription manually to test endpoint
    usuario = models.Usuario(
        telegram_user_id=telegram_id,
        nome="Teste Perfil",
        numero_funcionario="12345"
    )
    db.add(usuario)
    
    assinatura = models.Assinatura(
        telegram_user_id=telegram_id,
        stripe_customer_id="cust_test",
        status="active",
        plano="especial",
        data_inicio=datetime.now(),
        data_fim=datetime.now()
    )
    db.add(assinatura)
    await db.commit()
    
    # Test Endpoint
    # We need to use valid headers for RLS middleware if we were testing through middleware, 
    # but db_session_rls fixture mocks the DB session.
    # However, `client.get` goes through the app -> get_db.
    
    response = client.get(
        f"/usuarios/{telegram_id}",
        headers={"X-Telegram-User-ID": str(telegram_id)}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["telegram_user_id"] == telegram_id
    assert data["assinatura_status"] == "active"
    assert data["assinatura_plano"] == "especial"
