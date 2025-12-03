import pytest
from sqlalchemy import text, create_engine
from sqlalchemy.orm import sessionmaker
from app.api.webhook import handle_checkout_completed, handle_subscription_updated, handle_subscription_deleted
from app.infrastructure.subscription_middleware import check_subscription
from app.models import Assinatura

# Mock de objetos Stripe
class MockStripeObject(dict):
    def get(self, key, default=None):
        return super().get(key, default)

def test_stripe_webhook_flow(db_session):
    """
    Testa o fluxo completo de assinatura via Webhook handlers.
    """
    telegram_user_id = 999999
    stripe_customer_id = "cus_test_123"
    stripe_subscription_id = "sub_test_456"
    
    # 1. Simular Checkout Completed (Criação)
    session_mock = MockStripeObject({
        'client_reference_id': str(telegram_user_id),
        'customer': stripe_customer_id,
        'subscription': stripe_subscription_id
    })
    
    # Executar handler (async mockado ou rodar sync se possível, aqui chamamos a lógica interna)
    # Como os handlers são async, precisamos de um loop ou refatorar para teste.
    # Para simplificar, vamos testar a lógica de banco diretamente ou usar pytest-asyncio.
    pass

@pytest.mark.asyncio
async def test_subscription_lifecycle():
    """
    Testa ciclo completo de assinatura usando sessão privilegiada (superuser).
    Webhooks do Stripe são processos de sistema e não passam pelo RLS.
    """
    telegram_user_id = 888888
    stripe_customer_id = "cus_lifecycle_123"
    stripe_subscription_id = "sub_lifecycle_456"
    
    # Usar sessão de superuser para todo o teste (webhooks são processos de sistema)
    superuser_url = "postgresql+psycopg://postgres:postgres@localhost:5432/gestao_turnos"
    engine = create_engine(superuser_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Limpar estado anterior
        session.execute(text(f"DELETE FROM assinaturas WHERE telegram_user_id = {telegram_user_id}"))
        session.commit()
        
        # 1. Checkout Completed -> Ativa Assinatura
        session_data = {
            'client_reference_id': str(telegram_user_id),
            'customer': stripe_customer_id,
            'subscription': stripe_subscription_id
        }
        await handle_checkout_completed(session_data, session)
        
        # Verificar criação
        assinatura = session.query(Assinatura).filter_by(telegram_user_id=telegram_user_id).first()
        assert assinatura is not None
        assert assinatura.status == "active"
        assert assinatura.plano == "pro"
        
        # 2. Subscription Updated -> Pagamento Falhou
        sub_data = {
            'id': stripe_subscription_id,
            'status': 'past_due',
            'current_period_end': 1735689600  # 2025-01-01
        }
        await handle_subscription_updated(sub_data, session)
        
        # Re-query para verificar atualização
        session.expire(assinatura)
        session.refresh(assinatura)
        assert assinatura.status == "past_due"
        
        # 3. Subscription Deleted -> Cancelado
        sub_data_del = {
            'id': stripe_subscription_id
        }
        await handle_subscription_deleted(sub_data_del, session)
        
        # Re-query para verificar cancelamento
        session.expire(assinatura)
        session.refresh(assinatura)
        assert assinatura.status == "canceled"
        assert assinatura.plano == "free"
        
    finally:
        session.close()
        engine.dispose()
