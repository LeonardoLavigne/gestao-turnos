from __future__ import annotations

from datetime import datetime, date, timedelta
import logging
import re
from zoneinfo import ZoneInfo
from typing import Tuple

import httpx
from telegram import Update
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

from .config import get_settings


LINHA_REGEX = re.compile(
    r"^(?:dia\s+(?P<data>\d{1,2}[/-]\d{1,2}[/-]\d{4})\s*[-–—:]?\s*)?"
    r"(?P<tipo>\S+)\s+(?P<h1>\d{1,2}:\d{2})\s*(?:as|às|a|ate)\s*(?P<h2>\d{1,2}:\d{2})$",
    re.IGNORECASE,
)


def _parse_data_token(token: str) -> date:
    token = token.replace("-", "/")
    return datetime.strptime(token, "%d/%m/%Y").date()


def _parse_linhas_turno(text: str, tz: ZoneInfo) -> list[Tuple[str, date, str, str]]:
    linhas = [linha.strip() for linha in text.splitlines() if linha.strip()]
    if not linhas:
        raise ValueError(
            "Mensagem vazia. Use algo como: REN 08:00 as 16:00 ou "
            "Dia 29/11/2025 - Casino 15:00 as 03:00"
        )

    agora = datetime.now(tz=tz)
    resultados: list[Tuple[str, date, str, str]] = []
    erros: list[str] = []

    for idx, linha in enumerate(linhas, start=1):
        m = LINHA_REGEX.match(linha)
        if not m:
            erros.append(
                f"Linha {idx} inválida. Exemplo válido: "
                "Dia 29/11/2025 - Casino 15:00 as 03:00"
            )
            continue

        data_token = m.group("data")
        try:
            data_ref = (
                _parse_data_token(data_token) if data_token else agora.date()
            )
        except ValueError:
            erros.append(
                f"Linha {idx}: data inválida '{data_token}'. Use dd/mm/aaaa."
            )
            continue

        resultados.append(
            (
                m.group("tipo"),
                data_ref,
                m.group("h1"),
                m.group("h2"),
            )
        )

    if erros:
        raise ValueError("\n".join(erros))

    return resultados


async def _post_turno_api(
    tipo: str,
    data_ref: date,
    h1: str,
    h2: str,
) -> dict:
    settings = get_settings()
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "http://localhost:8000/turnos",
            json={
                "data_referencia": data_ref.isoformat(),
                "hora_inicio": h1,
                "hora_fim": h2,
                "tipo": tipo,
                "origem": "telegram",
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        return resp.json()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "Olá! Envie mensagens como:\n"
        "REN 08:00 as 16:00\n"
        "Casino 21:00 as 03:00"
    )


def _usuario_autorizado(user_id: int) -> bool:
    settings = get_settings()
    return not settings.telegram_allowed_users or user_id in settings.telegram_allowed_users


async def registrar_turno_msg(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    user = update.effective_user
    if not user or not _usuario_autorizado(user.id):
        logging.info("Mensagem ignorada de user_id=%s (não autorizado ou sem user).", getattr(user, "id", None))
        return

    logging.info(
        "Mensagem recebida do Telegram: user_id=%s username=%s texto=%r",
        user.id,
        getattr(user, "username", None),
        update.message.text,
    )

    settings = get_settings()
    tz = ZoneInfo(settings.timezone)

    try:
        entradas = _parse_linhas_turno(update.message.text, tz)
    except ValueError as e:
        await update.message.reply_text(str(e))
        return

    mensagens_resposta: list[str] = []

    for idx, (tipo, data_ref, h1, h2) in enumerate(entradas, start=1):
        try:
            turno = await _post_turno_api(tipo, data_ref, h1, h2)
        except Exception as exc:
            mensagens_resposta.append(
                f"Linha {idx} ({tipo} {h1}-{h2} {data_ref}): erro ao registrar: {exc}"
            )
            continue

        dur_horas = turno["duracao_minutos"] / 60.0
        mensagens_resposta.append(
            f"Linha {idx}: Registrado {tipo} {turno['hora_inicio']} - {turno['hora_fim']} "
            f"({dur_horas:.2f}h) em {turno['data_referencia']}."
        )

    await update.message.reply_text("\n".join(mensagens_resposta))


def _autorizado_ou_erro(update: Update) -> bool:
    user = update.effective_user
    if not user:
        return False
    if not _usuario_autorizado(user.id):
        logging.info(
            "Comando ignorado de user_id=%s (não autorizado).",
            user.id,
        )
        return False
    return True


def _formatar_relatorio(relatorio: dict) -> str:
    total_horas = relatorio["total_minutos"] / 60.0
    linhas = [f"Total: {total_horas:.2f}h entre {relatorio['inicio']} e {relatorio['fim']}."]
    for dia in relatorio["dias"]:
        horas_dia = dia["total_minutos"] / 60.0
        partes = [
            f"{dia['data']}: {horas_dia:.2f}h",
        ]
        if dia["por_tipo"]:
            tipos_txt = ", ".join(
                f"{tipo} {mins/60.0:.2f}h" for tipo, mins in dia["por_tipo"].items()
            )
            partes.append(f"({tipos_txt})")
        linhas.append(" ".join(partes))
    return "\n".join(linhas)


async def _comando_relatorio(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    *,
    tipo: str,
) -> None:
    if not _autorizado_ou_erro(update):
        return

    settings = get_settings()
    tz = ZoneInfo(settings.timezone)

    hoje = datetime.now(tz).date()

    params: dict[str, int | str] = {}
    if tipo == "semana":
        # Suportes:
        # /semana                -> semana ISO atual
        # /semana 2025-48        -> ano/semana explícitos
        # /semana 48             -> semana do ano atual
        # /semana 2025-11-29     -> semana ISO da data informada
        # /semana ultimos7       -> últimos 7 dias (usa relatorios/periodo)
        if context.args:
            token = context.args[0].lower()
            if token in {"ultimos7", "ultimos_7", "7d"}:
                inicio = hoje.replace() - timedelta(days=6)
                fim = hoje
                url = "http://localhost:8000/relatorios/periodo"
                params = {
                    "inicio": inicio.isoformat(),
                    "fim": fim.isoformat(),
                }
                tipo_chamada = "periodo"
            elif "-" in token and len(token) == 10:
                # formato data -> usar semana ISO dessa data
                data_ref = datetime.strptime(token, "%Y-%m-%d").date()
                iso = data_ref.isocalendar()
                params["ano"] = iso.year
                params["semana"] = iso.week
                url = "http://localhost:8000/relatorios/semana"
                tipo_chamada = "semana"
            elif "-" in token:
                ano_str, semana_str = token.split("-", 1)
                params["ano"] = int(ano_str)
                params["semana"] = int(semana_str)
                url = "http://localhost:8000/relatorios/semana"
                tipo_chamada = "semana"
            else:
                iso = hoje.isocalendar()
                params["ano"] = iso.year
                params["semana"] = int(token)
                url = "http://localhost:8000/relatorios/semana"
                tipo_chamada = "semana"
        else:
            iso = hoje.isocalendar()
            params["ano"] = iso.year
            params["semana"] = iso.week
            url = "http://localhost:8000/relatorios/semana"
            tipo_chamada = "semana"
    elif tipo == "mes":
        if context.args:
            token = context.args[0]
            if "-" in token:
                ano_str, mes_str = token.split("-", 1)
                params["ano"] = int(ano_str)
                params["mes"] = int(mes_str)
            else:
                params["ano"] = hoje.year
                params["mes"] = int(token)
        else:
            params["ano"] = hoje.year
            params["mes"] = hoje.month
        url = "http://localhost:8000/relatorios/mes"
        tipo_chamada = "mes"

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=10.0)
            resp.raise_for_status()
            relatorio = resp.json()
    except Exception as exc:
        await update.message.reply_text(
            f"Erro ao gerar relatório {tipo}: {exc}"
        )
        return

    texto = _formatar_relatorio(relatorio)
    await update.message.reply_text(texto)


async def relatorio_semana_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _comando_relatorio(update, context, tipo="semana")


async def relatorio_mes_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _comando_relatorio(update, context, tipo="mes")


def build_application() -> Application:
    settings = get_settings()

    if not settings.telegram_bot_token:
        logging.warning("TELEGRAM_BOT_TOKEN não configurado; bot do Telegram não será iniciado.")

    app = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .build()
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("semana", relatorio_semana_cmd))
    app.add_handler(CommandHandler("mes", relatorio_mes_cmd))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), registrar_turno_msg))
    return app


