from datetime import datetime, timedelta, UTC
from app.domain.entities.usuario import Usuario
from app.domain.entities.assinatura import Assinatura, PlanoType, AssinaturaStatus
from app.domain.repositories.usuario_repository import UsuarioRepository
from app.domain.repositories.assinatura_repository import AssinaturaRepository
from app.presentation import schemas

class CriarUsuarioUseCase:
    def __init__(self, usuario_repository: UsuarioRepository, assinatura_repository: AssinaturaRepository):
        self.usuario_repository = usuario_repository
        self.assinatura_repository = assinatura_repository

    async def execute(self, payload: schemas.UsuarioCreate) -> Usuario:
        # 1. Create User
        novo_usuario = Usuario(
            telegram_user_id=payload.telegram_user_id,
            nome=payload.nome,
            numero_funcionario=payload.numero_funcionario
        )
        usuario_salvo = await self.usuario_repository.criar(novo_usuario)
        
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
        await self.assinatura_repository.criar(nova_assinatura)
        
        return usuario_salvo
