"""
Domain entity for Turno (work shift).

This is a pure domain object with no infrastructure dependencies.
"""
from dataclasses import dataclass, field
from datetime import date, time, datetime
from typing import Optional


@dataclass
class Turno:
    """
    Represents a work shift (turno) in the domain.
    
    Attributes:
        id: Unique identifier (None for new entities)
        telegram_user_id: ID of the user who owns this shift
        data_referencia: Date of the shift
        hora_inicio: Start time
        hora_fim: End time
        duracao_minutos: Duration in minutes (calculated)
        tipo: Type/location of the shift
        descricao_opcional: Optional description
        criado_em: Creation timestamp
        atualizado_em: Last update timestamp
    """
    telegram_user_id: int
    data_referencia: date
    hora_inicio: time
    hora_fim: time
    duracao_minutos: int
    tipo: Optional[str] = None
    descricao_opcional: Optional[str] = None
    id: Optional[int] = None
    tipo_id: Optional[int] = None
    event_uid: Optional[str] = None
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    @staticmethod
    def calcular_duracao(data_ref: date, inicio: time, fim: time) -> int:
        """
        Calcula a duração em minutos entre dois horários.
        
        Lida com turnos que passam da meia-noite.
        """
        from datetime import timedelta
        
        dt_inicio = datetime.combine(data_ref, inicio)
        dt_fim = datetime.combine(data_ref, fim)
        
        if dt_fim <= dt_inicio:
            dt_fim += timedelta(days=1)
        
        return int((dt_fim - dt_inicio).total_seconds() // 60)

    @classmethod
    def criar(
        cls,
        telegram_user_id: int,
        data_referencia: date,
        hora_inicio: time,
        hora_fim: time,
        tipo: Optional[str] = None,
        descricao_opcional: Optional[str] = None,
    ) -> "Turno":
        """
        Factory method para criar um novo Turno com duração calculada.
        """
        duracao = cls.calcular_duracao(data_referencia, hora_inicio, hora_fim)
        
        return cls(
            telegram_user_id=telegram_user_id,
            data_referencia=data_referencia,
            hora_inicio=hora_inicio,
            hora_fim=hora_fim,
            duracao_minutos=duracao,
            tipo=tipo,
            descricao_opcional=descricao_opcional,
        )
