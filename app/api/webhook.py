import stripe
from fastapi import APIRouter, Request, Header, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import datetime, UTC

from app.config import get_settings
from app.database import get_db
from app.models import Assinatura
from app.services.stripe_service import StripeService

router = APIRouter()
settings = get_settings()

@router.post("/webhook/stripe")
async def stripe_webhook(request: Request, stripe_signature: str = Header(None), db: Session = Depends(get_db)):
    """
    Recebe eventos do Stripe e atualiza o status da assinatura.
    """
    payload = await request.body()
    
    try:
        event = stripe.Webhook.construct_event(
            payload, stripe_signature, settings.stripe_webhook_secret
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid payload")
    except stripe.error.SignatureVerificationError as e:
        raise HTTPException(status_code=400, detail="Invalid signature")

    # Processar eventos
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        await handle_checkout_completed(session, db)
    
    elif event['type'] == 'customer.subscription.updated':
        subscription = event['data']['object']
        await handle_subscription_updated(subscription, db)
        
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        await handle_subscription_deleted(subscription, db)

    return {"status": "success"}

async def handle_checkout_completed(session, db: Session):
    """
    Processa checkout bem-sucedido: cria ou atualiza assinatura.
    """
    telegram_user_id = session.get('client_reference_id')
    stripe_customer_id = session.get('customer')
    stripe_subscription_id = session.get('subscription')
    
    if not telegram_user_id:
        print("Webhook Error: telegram_user_id not found in session")
        return

    # Buscar assinatura existente
    assinatura = db.query(Assinatura).filter(Assinatura.telegram_user_id == int(telegram_user_id)).first()
    
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
    else:
        assinatura.stripe_customer_id = stripe_customer_id
        assinatura.stripe_subscription_id = stripe_subscription_id
        assinatura.status = "active"
        assinatura.plano = "pro"
        assinatura.atualizado_em = datetime.now(UTC)
    
    db.commit()
    print(f"Assinatura ativada para user {telegram_user_id}")

async def handle_subscription_updated(subscription, db: Session):
    """
    Atualiza status da assinatura (ex: pagamento falhou, renovou).
    """
    stripe_subscription_id = subscription.get('id')
    status = subscription.get('status')
    current_period_end = subscription.get('current_period_end')
    
    assinatura = db.query(Assinatura).filter(Assinatura.stripe_subscription_id == stripe_subscription_id).first()
    
    if assinatura:
        assinatura.status = status
        if current_period_end:
            assinatura.data_fim = datetime.fromtimestamp(current_period_end)
        assinatura.atualizado_em = datetime.now(UTC)
        db.commit()
        print(f"Assinatura {stripe_subscription_id} atualizada para {status}")

async def handle_subscription_deleted(subscription, db: Session):
    """
    Assinatura cancelada.
    """
    stripe_subscription_id = subscription.get('id')
    
    assinatura = db.query(Assinatura).filter(Assinatura.stripe_subscription_id == stripe_subscription_id).first()
    
    if assinatura:
        assinatura.status = "canceled"
        assinatura.plano = "free"
        assinatura.atualizado_em = datetime.now(UTC)
        db.commit()
        print(f"Assinatura {stripe_subscription_id} cancelada")
