from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app import models
from app.domain.entities.assinatura import Assinatura
from app.domain.repositories.assinatura_repository import AssinaturaRepository

class SqlAlchemyAssinaturaRepository(AssinaturaRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    def _to_entity(self, model: models.Assinatura) -> Assinatura:
        return Assinatura(
            id=model.id,
            telegram_user_id=model.telegram_user_id,
            stripe_customer_id=model.stripe_customer_id,
            stripe_subscription_id=model.stripe_subscription_id,
            status=model.status,
            plano=model.plano,
            data_inicio=model.data_inicio,
            data_fim=model.data_fim,
            criado_em=model.criado_em,
            atualizado_em=model.atualizado_em,
        )

    async def get_by_user_id(self, telegram_user_id: int) -> Optional[Assinatura]:
        stmt = select(models.Assinatura).where(
            models.Assinatura.telegram_user_id == telegram_user_id
        )
        result = await self.session.scalar(stmt)
        if not result:
            return None
        return self._to_entity(result)
