from typing import Optional
from app.domain.entities.usuario import Usuario
from app.domain.repositories.usuario_repository import UsuarioRepository
from app.presentation import schemas

class AtualizarUsuarioUseCase:
    def __init__(self, usuario_repository: UsuarioRepository):
        self.usuario_repository = usuario_repository

    async def execute(self, telegram_user_id: int, payload: schemas.UsuarioUpdate) -> Optional[Usuario]:
        # 1. Fetch existing user
        usuario = await self.usuario_repository.buscar_por_telegram_id(telegram_user_id)
        if not usuario:
            return None
            
        # 2. Update fields if provided
        if payload.nome is not None:
            usuario.nome = payload.nome
        if payload.numero_funcionario is not None:
            usuario.numero_funcionario = payload.numero_funcionario
            
        # 3. Persist
        return await self.usuario_repository.atualizar(usuario)
