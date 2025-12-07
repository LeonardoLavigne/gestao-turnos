import pytest
from sqlalchemy import text, select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.api.webhook import handle_checkout_completed, handle_subscription_updated, handle_subscription_deleted
from app.infrastructure.subscription_middleware import check_subscription
from app.models import Assinatura

# Mock de objetos Stripe
class MockStripeObject(dict):
    def get(self, key, default=None):
        return super().get(key, default)

def test_stripe_webhook_flow():
    """
    Testa o fluxo completo de assinatura via Webhook handlers.
    (Placeholder original mantido sync, mas vazio)
    """
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
    
    # Usar sessão de superuser para todo o teste
    # Usando DATABASE_URL do ambiente (que aponta para 'postgres' no Docker) ou fallback
    from app.config import get_settings
    settings = get_settings()
    superuser_url = settings.database_url
    if not superuser_url:
        superuser_url = "postgresql+psycopg://postgres:postgres@localhost:5432/gestao_turnos"
    elif superuser_url.startswith("postgresql://"):
        superuser_url = superuser_url.replace("postgresql://", "postgresql+psycopg://")
        
    engine = create_async_engine(superuser_url)
    Session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    
    async with Session() as session:
        try:
            # Limpar estado anterior
            await session.execute(text(f"DELETE FROM assinaturas WHERE telegram_user_id = {telegram_user_id}"))
            await session.commit()
            
            # 1. Checkout Completed -> Ativa Assinatura
            session_data = {
                'client_reference_id': str(telegram_user_id),
                'customer': stripe_customer_id,
                'subscription': stripe_subscription_id
            }
            await handle_checkout_completed(session_data, session)
            
            # Verificar criação
            result = await session.execute(select(Assinatura).filter_by(telegram_user_id=telegram_user_id))
            assinatura = result.scalar()
            
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
            await session.refresh(assinatura)
            assert assinatura.status == "past_due"
            
            # 3. Subscription Deleted -> Cancelado
            sub_data_del = {
                'id': stripe_subscription_id
            }
            await handle_subscription_deleted(sub_data_del, session)
            
            # Re-query para verificar cancelamento
            await session.refresh(assinatura)
            assert assinatura.status == "canceled"
            assert assinatura.plano == "free"
            
        finally:
            await engine.dispose()
