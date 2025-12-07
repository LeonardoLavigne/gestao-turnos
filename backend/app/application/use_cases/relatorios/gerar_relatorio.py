from datetime import date
from typing import List, Dict, Any
from app.domain.repositories.turno_repository import TurnoRepository
from app.domain.entities.turno import Turno
from app.presentation import schemas

class GerarRelatorioUseCase:
    def __init__(self, turno_repository: TurnoRepository):
        self.turno_repository = turno_repository

    def _nome_tipo(self, turno: Turno) -> str | None:
        if turno.tipo is not None:
            return turno.tipo # Assuming it's a string from Entity
        return None # Entity might differ from Model, check logic

    async def execute(self, telegram_user_id: int, inicio: date, fim: date) -> schemas.RelatorioPeriodo:
        # 1. Fetch data
        turnos = await self.turno_repository.listar_por_periodo(telegram_user_id, inicio, fim)
        
        # 2. Process Stats
        por_data: Dict[date, List[Turno]] = {}
        for turno in turnos:
            por_data.setdefault(turno.data_referencia, []).append(turno)

        dias: List[schemas.RelatorioDia] = []
        total_minutos_periodo = 0

        for dia in sorted(por_data.keys()):
            turnos_dia = por_data[dia]
            total_dia = sum(t.duracao_minutos for t in turnos_dia)
            total_minutos_periodo += total_dia

            por_tipo: Dict[str, int] = {}
            for t in turnos_dia:
                nome_tipo = t.tipo or t.tipo_livre or "sem_tipo"
                por_tipo[nome_tipo] = por_tipo.get(nome_tipo, 0) + t.duracao_minutos

            dias.append(
                schemas.RelatorioDia(
                    data=dia,
                    total_minutos=total_dia,
                    por_tipo=por_tipo,
                )
            )

        # 3. Return Schema
        return schemas.RelatorioPeriodo(
            inicio=inicio,
            fim=fim,
            total_minutos=total_minutos_periodo,
            dias=dias,
        )
