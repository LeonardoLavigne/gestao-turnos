"""
Turno (shift) handlers for Telegram bot.

Handles: turno registration messages, /remover command
"""
import logging
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.config import get_settings
from src.decorators import rate_limit, subscription_required
from src.parsers import parse_linhas_turno
from src.api_client import turno_client, usuario_client
from src.utils import usuario_autorizado
import httpx

logger = logging.getLogger(__name__)


@rate_limit

async def registrar_turno_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para mensagens de registro de turno."""
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    if not user or not usuario_autorizado(user.id):
        logger.info(
            "Mensagem ignorada de user_id=%s (não autorizado ou sem user).",
            getattr(user, "id", None)
        )
        return

    logger.info(
        "Mensagem recebida do Telegram: user_id=%s username=%s texto=%r",
        user.id,
        getattr(user, "username", None),
        update.message.text,
    )

    # Verificar se usuário tem perfil cadastrado
    perfil = await usuario_client.buscar_usuario(user.id)
    if not perfil:
        await update.message.reply_text(
            "⚠️ Você ainda não está cadastrado!\n\n"
            "Por favor, use o comando /start para completar seu cadastro antes de registrar turnos."
        )
        return

    settings = get_settings()
    tz = ZoneInfo(settings.timezone)

    try:
        entradas = parse_linhas_turno(update.message.text, tz)
    except ValueError as e:
        await update.message.reply_text(str(e))
        return

    mensagens_resposta: list[str] = []

    for idx, parsed in enumerate(entradas, start=1):
        try:
            turno = await turno_client.criar_turno(
                tipo=parsed.tipo,
                data_ref=parsed.data_referencia,
                hora_inicio=parsed.hora_inicio,
                hora_fim=parsed.hora_fim,
                telegram_user_id=user.id,
            )
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 403:
                mensagens_resposta.append(
                    f"⚠️ **Limite de turnos atingido!** ({parsed.data_referencia})\n"
                    "O plano Free permite apenas 30 turnos recentes.\n"
                    "Use /assinar para liberar turnos ilimitados."
                )
            elif e.response.status_code == 422:
                 mensagens_resposta.append(f"❌ Erro de validação: Verifique os dados enviados.")
            else:
                 mensagens_resposta.append(f"❌ Erro ao registrar: {e.response.text}")
            continue
        except Exception as exc:
            mensagens_resposta.append(
                f"Linha {idx} ({parsed.tipo} {parsed.hora_inicio}-{parsed.hora_fim} "
                f"{parsed.data_referencia}): erro desconhecido: {exc}"
            )
            continue

        dur_horas = turno["duracao_minutos"] / 60.0
        mensagens_resposta.append(
            f"Linha {idx}: Registrado {parsed.tipo} {turno['hora_inicio']} - {turno['hora_fim']} "
            f"({dur_horas:.2f}h) em {turno['data_referencia']}."
        )

    await update.message.reply_text("\n".join(mensagens_resposta))


async def remover_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para comando /remover - lista turnos recentes para remoção."""
    user = update.effective_user
    if not user or not usuario_autorizado(user.id):
        return

    try:
        turnos = await turno_client.listar_turnos_recentes(user.id, limit=5)
    except Exception as exc:
        await update.message.reply_text(f"Erro ao buscar turnos recentes: {exc}")
        return

    if not turnos:
        await update.message.reply_text("Nenhum turno recente encontrado.")
        return

    keyboard = []
    for t in turnos:
        label = f"{t['data_referencia']} {t['hora_inicio'][:5]}-{t['hora_fim'][:5]} ({t['tipo'] or 'Livre'})"
        keyboard.append([InlineKeyboardButton(f"🗑 {label}", callback_data=f"del_{t['id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Selecione um turno para remover:", reply_markup=reply_markup)


async def handle_delete_callback(query, user_id: int, turno_id: str) -> None:
    """Processa callback de deleção de turno."""
    try:
        success = await turno_client.deletar_turno(int(turno_id), user_id)
        if not success:
            await query.edit_message_text("Turno não encontrado (já removido?).")
            return
    except Exception as exc:
        await query.edit_message_text(f"Erro ao remover: {exc}")
        return

    await query.edit_message_text(f"Turno {turno_id} removido com sucesso.")
