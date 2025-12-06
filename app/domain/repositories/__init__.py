"""
Domain repositories package.

Exposes repository interfaces for use in application layer.
"""
from app.domain.repositories.turno_repository import TurnoRepository
from app.domain.repositories.usuario_repository import UsuarioRepository

__all__ = [
    "TurnoRepository",
    "UsuarioRepository",
]
