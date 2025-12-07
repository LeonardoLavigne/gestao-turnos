"""
Use case for generating reports.
"""
from dataclasses import dataclass
from datetime import date
from typing import List, Dict

from app.domain.entities.turno import Turno
from app.domain.repositories.turno_repository import TurnoRepository


@dataclass
class RelatorioDia:
    """Relatório de um dia específico."""
    data: date
    total_minutos: int
    por_tipo: Dict[str, int]


@dataclass
class RelatorioPeriodo:
    """Relatório de um período."""
    inicio: date
    fim: date
    total_minutos: int
    dias: List[RelatorioDia]


class GerarRelatorioUseCase:
    """
    Use case for generating period reports.
    
    Aggregates turno data into daily and period summaries.
    """

    def __init__(self, turno_repository: TurnoRepository):
        self.turno_repository = turno_repository

    async def execute(
        self,
        telegram_user_id: int,
        inicio: date,
        fim: date,
    ) -> RelatorioPeriodo:
        """
        Generates a report for the given period.
        
        Args:
            telegram_user_id: ID of the user
            inicio: Start date (inclusive)
            fim: End date (inclusive)
            
        Returns:
            RelatorioPeriodo with aggregated data
        """
        turnos = await self.turno_repository.listar_por_periodo(
            telegram_user_id=telegram_user_id,
            inicio=inicio,
            fim=fim,
        )
        
        return self._gerar_relatorio(turnos, inicio, fim)

    def gerar_de_turnos(
        self,
        turnos: List[Turno],
        inicio: date,
        fim: date,
    ) -> RelatorioPeriodo:
        """
        Generates a report from a list of turnos (for use without repository).
        """
        return self._gerar_relatorio(turnos, inicio, fim)

    def _gerar_relatorio(
        self,
        turnos: List[Turno],
        inicio: date,
        fim: date,
    ) -> RelatorioPeriodo:
        """Internal method to generate report from turno list."""
        # Group by date
        por_data: Dict[date, List[Turno]] = {}
        for turno in turnos:
            por_data.setdefault(turno.data_referencia, []).append(turno)

        dias: List[RelatorioDia] = []
        total_minutos_periodo = 0

        for dia in sorted(por_data.keys()):
            turnos_dia = por_data[dia]
            total_dia = sum(t.duracao_minutos for t in turnos_dia)
            total_minutos_periodo += total_dia

            # Aggregate by type
            por_tipo: Dict[str, int] = {}
            for t in turnos_dia:
                tipo = t.tipo or "sem_tipo"
                por_tipo[tipo] = por_tipo.get(tipo, 0) + t.duracao_minutos

            dias.append(
                RelatorioDia(
                    data=dia,
                    total_minutos=total_dia,
                    por_tipo=por_tipo,
                )
            )

        return RelatorioPeriodo(
            inicio=inicio,
            fim=fim,
            total_minutos=total_minutos_periodo,
            dias=dias,
        )
