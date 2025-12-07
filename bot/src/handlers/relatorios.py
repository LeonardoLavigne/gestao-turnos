"""
Relatório (report) handlers for Telegram bot.

Handles: /semana, /mes commands and PDF generation
"""
import logging
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from telegram import Update
from telegram.ext import ContextTypes

from src.config import get_settings
from src.api_client import relatorio_client
from src.parsers import parse_mes_arg
from src.utils import usuario_autorizado, formatar_relatorio
from src.decorators import subscription_required

logger = logging.getLogger(__name__)


async def relatorio_semana_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para comando /semana - relatório semanal."""
    user = update.effective_user
    if not user or not usuario_autorizado(user.id):
        return

    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    hoje = datetime.now(tz).date()

    # Determinar período baseado em argumentos
    if context.args:
        token = context.args[0].lower()
        if token in {"ultimos7", "ultimos_7", "7d"}:
            inicio = hoje - timedelta(days=6)
            fim = hoje
            try:
                relatorio = await relatorio_client.relatorio_periodo(inicio, fim, user.id)
            except Exception as exc:
                await update.message.reply_text(f"Erro ao gerar relatório: {exc}")
                return
        elif "-" in token and len(token) == 10:
            # formato data -> usar semana ISO dessa data
            data_ref = datetime.strptime(token, "%Y-%m-%d").date()
            iso = data_ref.isocalendar()
            try:
                relatorio = await relatorio_client.relatorio_semana(iso.year, iso.week, user.id)
            except Exception as exc:
                await update.message.reply_text(f"Erro ao gerar relatório: {exc}")
                return
        elif "-" in token:
            ano_str, semana_str = token.split("-", 1)
            try:
                relatorio = await relatorio_client.relatorio_semana(
                    int(ano_str), int(semana_str), user.id
                )
            except Exception as exc:
                await update.message.reply_text(f"Erro ao gerar relatório: {exc}")
                return
        else:
            iso = hoje.isocalendar()
            try:
                relatorio = await relatorio_client.relatorio_semana(iso.year, int(token), user.id)
            except Exception as exc:
                await update.message.reply_text(f"Erro ao gerar relatório: {exc}")
                return
    else:
        iso = hoje.isocalendar()
        try:
            relatorio = await relatorio_client.relatorio_semana(iso.year, iso.week, user.id)
        except Exception as exc:
            await update.message.reply_text(f"Erro ao gerar relatório: {exc}")
            return

    texto = formatar_relatorio(relatorio)
    await update.message.reply_text(texto)


async def relatorio_mes_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para comando /mes - relatório mensal ou PDF."""
    # Check if requesting PDF
    if context.args and context.args[0].lower() == "pdf":
        await _relatorio_mes_pdf_command(update, context)
        return

    user = update.effective_user
    if not user or not usuario_autorizado(user.id):
        return

    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    hoje = datetime.now(tz).date()

    # Determinar período baseado em argumentos
    if context.args:
        token = context.args[0]
        if "-" in token:
            ano_str, mes_str = token.split("-", 1)
            ano = int(ano_str)
            mes = int(mes_str)
        else:
            ano = hoje.year
            mes = int(token)
    else:
        ano = hoje.year
        mes = hoje.month

    try:
        relatorio = await relatorio_client.relatorio_mes(ano, mes, user.id)
    except Exception as exc:
        await update.message.reply_text(f"Erro ao gerar relatório: {exc}")
        return

    texto = formatar_relatorio(relatorio)
    await update.message.reply_text(texto)


@subscription_required
async def _relatorio_mes_pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handler para comando /mes pdf - relatório mensal em PDF."""
    user = update.effective_user
    if not user or not usuario_autorizado(user.id):
        return

    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    hoje = datetime.now(tz).date()

    mes_target = hoje.month
    ano_target = hoje.year

    # /mes pdf [arg]
    # context.args[0] é "pdf"
    if len(context.args) > 1:
        arg1 = context.args[1]
        try:
            mes_parsed, ano_parsed = parse_mes_arg(arg1)
            mes_target = mes_parsed
            if ano_parsed:
                ano_target = ano_parsed
            elif len(context.args) > 2 and context.args[2].isdigit():
                ano_target = int(context.args[2])
        except ValueError:
            await update.message.reply_text("Mês inválido.")
            return

    try:
        pdf_bytes = await relatorio_client.relatorio_mes_pdf(ano_target, mes_target, user.id)
    except Exception as exc:
        await update.message.reply_text(f"Erro ao gerar PDF: {exc}")
        return

    await update.message.reply_document(
        document=pdf_bytes,
        filename=f"relatorio_{ano_target}_{mes_target:02d}.pdf",
        caption=f"Relatório Mensal PDF ({mes_target}/{ano_target})"
    )


# Functions for menu callbacks
async def gerar_relatorio_semana_atual(user_id: int) -> dict | str:
    """Gera relatório da semana atual para callback do menu."""
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    hoje = datetime.now(tz).date()
    iso = hoje.isocalendar()

    try:
        relatorio = await relatorio_client.relatorio_semana(iso.year, iso.week, user_id)
        return formatar_relatorio(relatorio)
    except Exception as exc:
        return f"Erro ao gerar relatório: {exc}"


async def gerar_relatorio_mes_atual(user_id: int) -> dict | str:
    """Gera relatório do mês atual para callback do menu."""
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    hoje = datetime.now(tz).date()

    try:
        relatorio = await relatorio_client.relatorio_mes(hoje.year, hoje.month, user_id)
        return formatar_relatorio(relatorio)
    except Exception as exc:
        return f"Erro ao gerar relatório: {exc}"


async def gerar_pdf_mes_atual(user_id: int) -> tuple[bytes | None, str | None, str | None]:
    """Gera PDF do mês atual para callback do menu."""
    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    hoje = datetime.now(tz).date()

    try:
        pdf_bytes = await relatorio_client.relatorio_mes_pdf(hoje.year, hoje.month, user_id)
        filename = f"relatorio_{hoje.year}_{hoje.month:02d}.pdf"
        caption = f"Relatório Mensal PDF ({hoje.month}/{hoje.year})"
        return pdf_bytes, filename, caption
    except Exception as exc:
        return None, None, f"Erro ao gerar PDF: {exc}"
