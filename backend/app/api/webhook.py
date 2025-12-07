"""
Stripe webhook handlers for subscription management.
"""
import logging
import stripe
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import datetime, UTC

from app.core.config import get_settings
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import Assinatura

logger = logging.getLogger(__name__)

router = APIRouter()
settings = get_settings()


@router.post("/webhook/stripe", tags=["Webhooks"])
async def stripe_webhook(
    request: Request,
    stripe_signature: str = Header(None),
    db: AsyncSession = Depends(get_db),
):
    """
    Recebe eventos do Stripe e atualiza o status da assinatura.
    """
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except ValueError:
        logger.warning("Stripe webhook: Invalid payload received")
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError:
        logger.warning("Stripe webhook: Invalid signature")
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Processar eventos
    event_type = event['type']
    logger.info(f"Processing Stripe event: {event_type}")
    
    if event_type == 'checkout.session.completed':
        session = event['data']['object']
        await handle_checkout_completed(session, db)
    
    elif event_type == 'customer.subscription.updated':
        subscription = event['data']['object']
        await handle_subscription_updated(subscription, db)
        
    elif event_type == 'customer.subscription.deleted':
        subscription = event['data']['object']
        await handle_subscription_deleted(subscription, db)

    return {"status": "success"}


async def handle_checkout_completed(session, db: AsyncSession):
    """
    Processa checkout bem-sucedido: cria ou atualiza assinatura.
    """
    telegram_user_id = session.get('client_reference_id')
    stripe_customer_id = session.get('customer')
    stripe_subscription_id = session.get('subscription')
    
    if not telegram_user_id:
        logger.error("Webhook Error: telegram_user_id not found in checkout session")
        return

    # Buscar assinatura existente
    stmt = select(Assinatura).where(Assinatura.telegram_user_id == int(telegram_user_id))
    result = await db.execute(stmt)
    assinatura = result.scalar()
    
    if not assinatura:
        assinatura = Assinatura(
            telegram_user_id=int(telegram_user_id),
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            status="active",
            plano="pro",
            criado_em=datetime.now(UTC),
            atualizado_em=datetime.now(UTC)
        )
        db.add(assinatura)
        logger.info(
            "Nova assinatura criada",
            extra={"telegram_user_id": telegram_user_id, "plano": "pro"}
        )
    else:
        assinatura.stripe_customer_id = stripe_customer_id
        assinatura.stripe_subscription_id = stripe_subscription_id
        assinatura.status = "active"
        assinatura.plano = "pro"
        assinatura.atualizado_em = datetime.now(UTC)
        logger.info(
            "Assinatura atualizada para ativa",
            extra={"telegram_user_id": telegram_user_id, "plano": "pro"}
        )
    
    await db.commit()


async def handle_subscription_updated(subscription, db: AsyncSession):
    """
    Atualiza status da assinatura (ex: pagamento falhou, renovou).
    """
    stripe_subscription_id = subscription.get('id')
    status = subscription.get('status')
    current_period_end = subscription.get('current_period_end')
    
    stmt = select(Assinatura).where(Assinatura.stripe_subscription_id == stripe_subscription_id)
    result = await db.execute(stmt)
    assinatura = result.scalar()
    
    if assinatura:
        assinatura.status = status
        if current_period_end:
            assinatura.data_fim = datetime.fromtimestamp(current_period_end)
        assinatura.atualizado_em = datetime.now(UTC)
        await db.commit()
        logger.info(
            "Status de assinatura atualizado",
            extra={"stripe_subscription_id": stripe_subscription_id, "status": status}
        )


async def handle_subscription_deleted(subscription, db: AsyncSession):
    """
    Assinatura cancelada.
    """
    stripe_subscription_id = subscription.get('id')
    
    stmt = select(Assinatura).where(Assinatura.stripe_subscription_id == stripe_subscription_id)
    result = await db.execute(stmt)
    assinatura = result.scalar()
    
    if assinatura:
        assinatura.status = "canceled"
        assinatura.plano = "free"
        assinatura.atualizado_em = datetime.now(UTC)
        await db.commit()
        logger.info(
            "Assinatura cancelada",
            extra={"stripe_subscription_id": stripe_subscription_id}
        )
