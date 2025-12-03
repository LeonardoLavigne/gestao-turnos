import stripe
from typing import Optional
from app.config import get_settings

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
            # Buscar ou criar customer (simplificado: cria novo ou busca por metadados se implementado)
            # Idealmente, buscaríamos no banco local primeiro.
            # Aqui vamos assumir que o fluxo cria a sessão e o webhook vincula.
            
            checkout_session = stripe.checkout.Session.create(
                payment_method_types=['card'],
                line_items=[
                    {
                        'price': settings.stripe_price_id_pro,
                        'quantity': 1,
                    },
                ],
                mode='subscription',
                success_url=f"{settings.base_url}/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=f"{settings.base_url}/cancel",
                client_reference_id=str(telegram_user_id),
                metadata={
                    "telegram_user_id": str(telegram_user_id)
                },
                customer_email=customer_email,
            )
            return checkout_session.url
        except Exception as e:
            print(f"Erro ao criar checkout session: {e}")
            raise e

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
            print(f"Erro ao criar portal session: {e}")
            raise e
