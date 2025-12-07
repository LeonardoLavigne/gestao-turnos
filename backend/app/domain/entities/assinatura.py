from dataclasses import dataclass
from datetime import datetime
from typing import Optional
from enum import Enum

class PlanoType(str, Enum):
    FREE = "free"
    PRO = "pro"

class AssinaturaStatus(str, Enum):
    ACTIVE = "active"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    UNPAID = "unpaid"
    CANCELED = "canceled"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    PAST_DUE = "past_due"


@dataclass
class Assinatura:
    id: int
    telegram_user_id: int
    stripe_customer_id: str
    stripe_subscription_id: Optional[str]
    status: str
    plano: str
    data_inicio: Optional[datetime]
    data_fim: Optional[datetime]
    criado_em: datetime
    atualizado_em: datetime

    def is_active(self) -> bool:
        return self.status in ("active", "trialing")

    @property
    def is_free(self) -> bool:
        return self.plano == "free" or not self.is_active()
