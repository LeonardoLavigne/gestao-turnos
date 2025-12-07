"""
Repository interface for Usuario (user).

Defines the contract that any Usuario repository implementation must follow.
"""
from abc import ABC, abstractmethod
from typing import Optional

from app.domain.entities.usuario import Usuario


class UsuarioRepository(ABC):
    """
    Abstract repository interface for Usuario operations.
    
    Implementations must provide concrete behavior for all methods.
    """

    @abstractmethod
    def buscar_por_telegram_id(self, telegram_user_id: int) -> Optional[Usuario]:
        """
        Busca um usuário pelo Telegram user ID.
        
        Args:
            telegram_user_id: ID do usuário no Telegram
            
        Returns:
            Usuario encontrado ou None
        """
        pass

    @abstractmethod
    def criar(self, usuario: Usuario) -> Usuario:
        """
        Persiste um novo usuário.
        
        Args:
            usuario: Entidade Usuario a ser persistida
            
        Returns:
            Usuario persistido com ID e timestamps preenchidos
        """
        pass

    @abstractmethod
    def atualizar(self, usuario: Usuario) -> Usuario:
        """
        Atualiza um usuário existente.
        
        Args:
            usuario: Entidade Usuario com dados atualizados
            
        Returns:
            Usuario atualizado
            
        Raises:
            ValueError: Se o usuário não existir
        """
        pass

    @abstractmethod
    def existe_por_numero_funcionario(self, numero_funcionario: str) -> bool:
        """
        Verifica se já existe um usuário com o número de funcionário.
        
        Args:
            numero_funcionario: Número de funcionário a verificar
            
        Returns:
            True se existe, False caso contrário
        """
        pass
