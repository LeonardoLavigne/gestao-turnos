"""
Repository interface for Turno (work shift).

Defines the contract that any Turno repository implementation must follow.
"""
from abc import ABC, abstractmethod
from datetime import date
from typing import List, Optional

from app.domain.entities.turno import Turno
from app.domain.entities.tipo_turno import TipoTurno


class TurnoRepository(ABC):
    """
    Abstract repository interface for Turno operations.
    
    Implementations must provide concrete behavior for all methods.
    """

    @abstractmethod
    async def criar(self, turno: Turno) -> Turno:
        """
        Persiste um novo turno.
        
        Args:
            turno: Entidade Turno a ser persistida
            
        Returns:
            Turno persistido com ID e timestamps preenchidos
        """
        pass

    @abstractmethod
    async def buscar_por_id(self, turno_id: int, telegram_user_id: int) -> Optional[Turno]:
        """
        Busca um turno por ID.
        
        Args:
            turno_id: ID do turno
            telegram_user_id: ID do usuário (para RLS)
            
        Returns:
            Turno encontrado ou None
        """
        pass

    @abstractmethod
    async def listar_por_periodo(
        self,
        telegram_user_id: int,
        inicio: date,
        fim: date,
    ) -> List[Turno]:
        """
        Lista turnos de um usuário em um período.
        
        Args:
            telegram_user_id: ID do usuário
            inicio: Data inicial (inclusive)
            fim: Data final (inclusive)
            
        Returns:
            Lista de turnos ordenados por data e hora
        """
        pass

    @abstractmethod
    async def listar_recentes(
        self,
        telegram_user_id: int,
        limit: int = 5,
    ) -> List[Turno]:
        """
        Lista os turnos mais recentes de um usuário.
        
        Args:
            telegram_user_id: ID do usuário
            limit: Número máximo de turnos a retornar
            
        Returns:
            Lista de turnos ordenados por criação (mais recente primeiro)
        """
        pass

    @abstractmethod
    async def deletar(self, turno_id: int, telegram_user_id: int) -> bool:
        """
        Deleta um turno.
        
        Args:
            turno_id: ID do turno a deletar
            telegram_user_id: ID do usuário (para RLS)
            
        Returns:
            True se deletado, False se não encontrado
        """
        pass

    @abstractmethod
    async def atualizar(self, turno: Turno) -> Turno:
        """
        Atualiza um turno existente.
        """
        pass

    @abstractmethod
    async def contar_por_periodo(
        self,
        telegram_user_id: int,
        inicio: date,
        fim: date,
    ) -> int:
        """
        Conta o número de turnos em um período.
        """
        pass

    @abstractmethod
    async def buscar_tipo_por_nome(self, nome: str) -> Optional[TipoTurno]:
        """
        Busca um tipo de turno pelo nome.
        """
        pass
