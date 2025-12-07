from fastapi import APIRouter, HTTPException
from app.presentation import schemas
from app.services.stripe_service import StripeService

router = APIRouter()

@router.post("/checkout")
async def criar_checkout(payload: schemas.CheckoutRequest):
    """
    Cria uma sessão de checkout do Stripe para o usuário.
    """
    try:
        # Static method call, no DB dependency needed currently
        url = StripeService.create_checkout_session(payload.telegram_user_id)
        return {"url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
