from datetime import datetime, timedelta, UTC
from app.domain.entities.usuario import Usuario
from app.domain.entities.assinatura import Assinatura, PlanoType, AssinaturaStatus
from app.domain.uow import AbstractUnitOfWork
from app.presentation import schemas

class CriarUsuarioUseCase:
    def __init__(self, uow: AbstractUnitOfWork):
        self.uow = uow

    async def execute(self, payload: schemas.UsuarioCreate) -> Usuario:
        async with self.uow:
            # 1. Create User
            novo_usuario = Usuario(
                telegram_user_id=payload.telegram_user_id,
                nome=payload.nome,
                numero_funcionario=payload.numero_funcionario
            )
            # Use repository from UoW
            usuario_salvo = await self.uow.usuarios.criar(novo_usuario)
            
            # 2. Create Trial Subscription (14 days)
            agora = datetime.now(UTC)
            fim_trial = agora + timedelta(days=14)
            
            nova_assinatura = Assinatura(
                telegram_user_id=payload.telegram_user_id,
                stripe_customer_id=f"trial_{payload.telegram_user_id}",
                stripe_subscription_id=None,
                status=AssinaturaStatus.TRIALING.value,
                plano=PlanoType.PRO.value,
                data_inicio=agora,
                data_fim=fim_trial,
                criado_em=agora,
                atualizado_em=agora,
                id=None
            )
            await self.uow.assinaturas.criar(nova_assinatura)
            
            # 3. Commit Transaction (Atomic)
            await self.uow.commit()
            
            return usuario_salvo
