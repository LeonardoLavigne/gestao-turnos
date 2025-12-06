"""
Use cases package.

Exposes all application use cases.
"""
from app.application.use_cases.turnos import (
    CriarTurnoUseCase,
    ListarTurnosPeriodoUseCase,
    ListarTurnosRecentesUseCase,
    DeletarTurnoUseCase,
)
from app.application.use_cases.relatorios import (
    GerarRelatorioUseCase,
    RelatorioDia,
    RelatorioPeriodo,
)

__all__ = [
    # Turnos
    "CriarTurnoUseCase",
    "ListarTurnosPeriodoUseCase",
    "ListarTurnosRecentesUseCase",
    "DeletarTurnoUseCase",
    # Relatórios
    "GerarRelatorioUseCase",
    "RelatorioDia",
    "RelatorioPeriodo",
]
