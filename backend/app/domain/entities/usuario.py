"""
Domain entity for Usuario (user).

This is a pure domain object with no infrastructure dependencies.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Usuario:
    """
    Represents a user in the domain.
    
    Attributes:
        id: Unique identifier (None for new entities)
        telegram_user_id: Telegram user ID (unique)
        nome: User's full name
        numero_funcionario: Employee number (unique)
        criado_em: Creation timestamp
        atualizado_em: Last update timestamp
    """
    telegram_user_id: int
    nome: str
    numero_funcionario: str
    id: Optional[int] = None
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    @classmethod
    def criar(
        cls,
        telegram_user_id: int,
        nome: str,
        numero_funcionario: str,
    ) -> "Usuario":
        """
        Factory method para criar um novo Usuario.
        """
        return cls(
            telegram_user_id=telegram_user_id,
            nome=nome,
            numero_funcionario=numero_funcionario,
        )
