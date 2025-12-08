from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.assinatura import Assinatura

class AssinaturaRepository(ABC):
    @abstractmethod
    async def get_by_user_id(self, telegram_user_id: int, for_update: bool = False) -> Optional[Assinatura]:
        """Recupera a assinatura ativa de um usuário pelo ID do Telegram."""
        pass

    @abstractmethod
    async def criar(self, assinatura: Assinatura) -> Assinatura:
        """Cria e persiste uma nova assinatura."""
        pass
