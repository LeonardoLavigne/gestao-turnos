"""
Stripe service for managing subscriptions and checkout sessions.
"""
import logging
import stripe
from typing import Optional

from app.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()
stripe.api_key = settings.stripe_api_key


class StripeService:
    @staticmethod
    def create_checkout_session(telegram_user_id: int, customer_email: Optional[str] = None) -> str:
        """
        Cria uma sessão de checkout do Stripe para upgrade para Pro.
        Retorna a URL de checkout.
        """
        try:
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': settings.stripe_price_id_pro,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=f"{settings.base_url}/success",
                cancel_url=f"{settings.base_url}/cancel",
                client_reference_id=str(telegram_user_id),
                metadata={
                    "telegram_user_id": str(telegram_user_id)
                },
                customer_email=customer_email,
            )
            return checkout_session.url
        except Exception as e:
            logger.error(
                "Erro ao criar checkout session",
                extra={"telegram_user_id": telegram_user_id, "error": str(e)}
            )
            raise

    @staticmethod
    def get_portal_url(stripe_customer_id: str) -> str:
        """
        Gera URL para o portal de clientes (gerenciamento de assinatura).
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=stripe_customer_id,
                return_url=f"{settings.base_url}/return",
            )
            return session.url
        except Exception as e:
            logger.error(
                "Erro ao criar portal session",
                extra={"stripe_customer_id": stripe_customer_id, "error": str(e)}
            )
            raise
