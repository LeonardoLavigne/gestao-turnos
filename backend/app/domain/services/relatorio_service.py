from abc import ABC, abstractmethod
from datetime import date
from typing import List, Dict, Optional
from app.domain.entities.turno import Turno

class RelatorioService(ABC):
    @abstractmethod
    def gerar_pdf_mes(self, turnos: List[Turno], inicio: date, fim: date, usuario_info: Optional[Dict] = None) -> bytes:
        """
        Gera o binário PDF do relatório mensal de turnos.
        """
        pass
