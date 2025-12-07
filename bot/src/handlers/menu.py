"""
Menu and callback handlers for Telegram bot.

Handles: /menu command and all inline keyboard callbacks
"""
import logging
from datetime import datetime
from zoneinfo import ZoneInfo

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from src.config import get_settings
from src.config import get_settings
from src.api_client import turno_client, usuario_client
from src.utils import usuario_autorizado
from src.handlers.turnos import handle_delete_callback
from src.handlers.relatorios import (
    gerar_relatorio_semana_atual,
    gerar_relatorio_mes_atual,
    gerar_pdf_mes_atual,
)

logger = logging.getLogger(__name__)


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para comando /menu - exibe menu principal."""
    keyboard = [
        [InlineKeyboardButton("📊 Relatórios", callback_data="menu_relatorios")],
        [InlineKeyboardButton("🗑 Remover Turno", callback_data="menu_remover")],
        [InlineKeyboardButton("👤 Meu Perfil", callback_data="menu_perfil")],
        [InlineKeyboardButton("ℹ️ Ajuda", callback_data="menu_ajuda")],
    ]
    await update.message.reply_text(
        "📋 *Menu Principal*\n\nEscolha uma opção:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler principal para callbacks de inline keyboard."""
    query = update.callback_query
    await query.answer()

    if not usuario_autorizado(query.from_user.id):
        await query.edit_message_text("Não autorizado.")
        return

    data = query.data

    # Handle deletion callbacks
    if data.startswith("del_"):
        turno_id = data.split("_")[1]
        await handle_delete_callback(query, query.from_user.id, turno_id)
        return

    # Handle menu callbacks
    if data.startswith("menu_"):
        await _handle_menu_callback(query, context, data)
        return


async def _handle_menu_callback(query, context, data: str) -> None:
    """Processa callbacks do menu hierárquico."""
    action = data.replace("menu_", "")
    user_id = query.from_user.id

    if action == "main":
        keyboard = [
            [InlineKeyboardButton("📊 Relatórios", callback_data="menu_relatorios")],
            [InlineKeyboardButton("🗑 Remover Turno", callback_data="menu_remover")],
            [InlineKeyboardButton("👤 Meu Perfil", callback_data="menu_perfil")],
            [InlineKeyboardButton("ℹ️ Ajuda", callback_data="menu_ajuda")],
        ]
        await query.edit_message_text(
            "📋 *Menu Principal*\n\nEscolha uma opção:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif action == "relatorios":
        keyboard = [
            [InlineKeyboardButton("📅 Semana Atual", callback_data="menu_semana_atual")],
            [InlineKeyboardButton("📆 Mês Atual", callback_data="menu_mes_atual")],
            [InlineKeyboardButton("📄 PDF Mês Atual", callback_data="menu_mes_pdf")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="menu_main")],
        ]
        await query.edit_message_text(
            "📊 *Relatórios*\n\nEscolha o tipo de relatório:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif action == "semana_atual":
        texto = await gerar_relatorio_semana_atual(user_id)
        await query.edit_message_text(texto)

    elif action == "mes_atual":
        texto = await gerar_relatorio_mes_atual(user_id)
        await query.edit_message_text(texto)

    elif action == "mes_pdf":
        # Check Subscription
        try:
            profile = await usuario_client.buscar_usuario(user_id)
            status = profile.get("assinatura_status") if profile else None
            if status not in ("active", "trialing"):
                await query.edit_message_text(
                    "🔒 *Recurso Premium*\n\n"
                    "Relatórios em PDF são exclusivos para assinantes.\n"
                    "Use /assinar para liberar.",
                    parse_mode="Markdown"
                )
                return
        except Exception:
            await query.edit_message_text("Erro ao verificar assinatura.")
            return

        await query.edit_message_text("Gerando PDF do mês atual...")
        pdf_bytes, filename, caption = await gerar_pdf_mes_atual(user_id)
        
        if pdf_bytes:
            await query.message.reply_document(
                document=pdf_bytes,
                filename=filename,
                caption=caption
            )
            await query.edit_message_text("PDF enviado!")
        else:
            await query.edit_message_text(caption)  # caption contains error message

    elif action == "remover":
        try:
            turnos = await turno_client.listar_turnos_recentes(user_id, limit=5)
        except Exception as exc:
            await query.edit_message_text(f"Erro ao buscar turnos: {exc}")
            return

        if not turnos:
            await query.edit_message_text("Nenhum turno recente encontrado.")
            return

        keyboard = []
        for t in turnos:
            label = f"{t['data_referencia']} {t['hora_inicio'][:5]}-{t['hora_fim'][:5]} ({t['tipo'] or 'Livre'})"
            keyboard.append([InlineKeyboardButton(f"🗑 {label}", callback_data=f"del_{t['id']}")])
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="menu_main")])

        await query.edit_message_text(
            "🗑 *Remover Turno*\n\nSelecione um turno para remover:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )

    elif action == "perfil":
        perfil = await usuario_client.buscar_usuario(user_id)
        
        if not perfil:
            await query.edit_message_text(
                "⚠️ Você ainda não está cadastrado!\n\n"
                "Por favor, use o comando /start para completar seu cadastro."
            )
            return

        await query.edit_message_text(
            f"👤 *Seu Perfil*\n\n"
            f"📝 Nome: *{perfil['nome']}*\n"
            f"🆔 Número: *{perfil['numero_funcionario']}*\n"
            f"📅 Cadastrado em: {perfil['criado_em'][:10]}",
            parse_mode="Markdown"
        )

    elif action == "ajuda":
        await query.edit_message_text(
            "ℹ️ *Ajuda - Gestão de Turnos*\n\n"
            "Comandos disponíveis:\n"
            "/start - Iniciar cadastro\n"
            "/assinar - Assinar Plano Pro\n"
            "/mes - Relatório do mês atual\n"
            "/semana - Relatório da semana atual\n"
            "/remover - Remover turnos recentes\n"
            "/menu - Menu interativo\n\n"
            "Para registrar um turno, envie:\n"
            "`<local> <inicio> as <fim>`\n"
            "Ex: `Hospital 07:00 as 19:00`",
            parse_mode="Markdown"
        )
