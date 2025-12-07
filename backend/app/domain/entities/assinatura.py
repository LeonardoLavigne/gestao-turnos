"""
Domain entity for Assinatura (subscription).

This is a pure domain object with no infrastructure dependencies.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum


class PlanoType(str, Enum):
    """Tipos de plano disponíveis."""
    FREE = "free"
    PRO = "pro"


class AssinaturaStatus(str, Enum):
    """Status possíveis da assinatura."""
    INACTIVE = "inactive"
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"


@dataclass
class Assinatura:
    """
    Represents a subscription in the domain.
    
    Attributes:
        id: Unique identifier (None for new entities)
        telegram_user_id: Telegram user ID (unique)
        stripe_customer_id: Stripe customer ID
        stripe_subscription_id: Stripe subscription ID
        status: Subscription status
        plano: Plan type (free, pro)
        data_inicio: Subscription start date
        data_fim: Subscription end date
        criado_em: Creation timestamp
        atualizado_em: Last update timestamp
    """
    telegram_user_id: int
    stripe_customer_id: str
    status: AssinaturaStatus = AssinaturaStatus.INACTIVE
    plano: PlanoType = PlanoType.FREE
    stripe_subscription_id: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    id: Optional[int] = None
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    def is_active(self) -> bool:
        """Verifica se a assinatura está ativa."""
        return self.status == AssinaturaStatus.ACTIVE

    def is_pro(self) -> bool:
        """Verifica se é plano Pro."""
        return self.plano == PlanoType.PRO and self.is_active()

    def ativar(self, stripe_subscription_id: str) -> None:
        """Ativa a assinatura com plano Pro."""
        self.stripe_subscription_id = stripe_subscription_id
        self.status = AssinaturaStatus.ACTIVE
        self.plano = PlanoType.PRO
        self.data_inicio = datetime.utcnow()

    def cancelar(self) -> None:
        """Cancela a assinatura."""
        self.status = AssinaturaStatus.CANCELED
        self.plano = PlanoType.FREE
