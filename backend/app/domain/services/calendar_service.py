from abc import ABC, abstractmethod
from typing import Optional
from app.domain.entities.turno import Turno

class CalendarService(ABC):
    @abstractmethod
    def sync_event(self, turno: Turno) -> Optional[str]:
        """
        Sincroniza um turno com o calendário externo.
        Retorna o UID do evento criado/atualizado ou None se falhar/não aplicável.
        """
        pass
