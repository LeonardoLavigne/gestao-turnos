```python
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
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .config import get_settings


LINHA_REGEX = re.compile(
    r"^(?:dia\s+(?P<data>\d{1,2}[/-]\d{1,2}[/-]\d{4})\s*[-–—:]?\s*)?"
    r"(?P<tipo>[^\s\-–—:]+)\s*(?:[-–—:]\s*)?"
    r"(?P<h1>\d{1,2}:\d{2})\s*(?:as|às|a|ate)\s*(?P<h2>\d{1,2}:\d{2})$",
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
        "<local> <hora_inicio> as <hora_fim>\n"
        "Exemplo: Hospital 08:00 as 16:00"
    )


def _usuario_autorizado(user_id: int) -> bool:
    settings = get_settings()
    return not settings.telegram_allowed_users or user_id in settings.telegram_allowed_users


# Estados para ConversationHandler de onboarding
AGUARDANDO_NOME, AGUARDANDO_NUMERO = range(2)


async def _verificar_perfil_usuario(user_id: int) -> dict | None:
    """Verifica se usuário tem perfil cadastrado. Retorna dados ou None."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"http://localhost:8000/usuarios/{user_id}",
                timeout=10.0
            )
            if resp.status_code == 200:
                return resp.json()
            return None
    except Exception:
        return None


async def iniciar_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Inicia o processo de onboarding para coletar dados do usuário."""
    await update.message.reply_text(
        "👋 Bem-vindo! Para começar a registrar seus turnos, preciso de algumas informações.\n\n"
        "Por favor, me diga seu *nome completo*:",
        parse_mode="Markdown"
    )
    return AGUARDANDO_NOME


async def receber_nome(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o nome do usuário e pede o número de funcionário."""
    nome = update.message.text.strip()
    
    if len(nome) < 3:
        await update.message.reply_text(
            "❌ Nome muito curto. Por favor, digite seu nome completo:"
        )
        return AGUARDANDO_NOME
    
    # Armazenar temporariamente no contexto
    context.user_data['nome'] = nome
    
    await update.message.reply_text(
        f"✅ Nome: *{nome}*\n\n"
        "Agora, me diga seu *número de funcionário*:",
        parse_mode="Markdown"
    )
    return AGUARDANDO_NUMERO


async def receber_numero(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Recebe o número de funcionário e finaliza o cadastro."""
    numero = update.message.text.strip()
    
    if len(numero) < 1:
        await update.message.reply_text(
            "❌ Número inválido. Por favor, digite seu número de funcionário:"
        )
        return AGUARDANDO_NUMERO
    
    nome = context.user_data.get('nome')
    user_id = update.effective_user.id
    
    # Cadastrar no backend
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "http://localhost:8000/usuarios",
                json={
                    "telegram_user_id": user_id,
                    "nome": nome,
                    "numero_funcionario": numero
                },
                timeout=10.0
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 400:
            await update.message.reply_text(
                "❌ Este número de funcionário já está cadastrado. "
                "Por favor, use outro número:"
            )
            return AGUARDANDO_NUMERO
        else:
            await update.message.reply_text(
                "❌ Erro ao cadastrar. Tente novamente mais tarde."
            )
            return ConversationHandler.END
    except Exception:
        await update.message.reply_text(
            "❌ Erro ao cadastrar. Tente novamente mais tarde."
        )
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"✅ Cadastro concluído!\n\n"
        f"📝 Nome: *{nome}*\n"
        f"🆔 Número: *{numero}*\n\n"
        "Agora você já pode registrar seus turnos! Envie algo como:\n"
        "`<local> <hora_inicio> as <hora_fim>`\n"
        "Exemplo: `Hospital 08:00 as 16:00`",
        parse_mode="Markdown"
    )
    
    # Limpar dados temporários
    context.user_data.clear()
    
    return ConversationHandler.END


async def cancelar_onboarding(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Cancela o processo de onboarding."""
    await update.message.reply_text(
        "❌ Cadastro cancelado. Use /start quando quiser se cadastrar."
    )
    context.user_data.clear()
    return ConversationHandler.END


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

    # Verificar se usuário tem perfil cadastrado
    perfil = await _verificar_perfil_usuario(user.id)
    if not perfil:
        await update.message.reply_text(
            "⚠️ Você ainda não está cadastrado!\n\n"
            "Por favor, use o comando /start para completar seu cadastro antes de registrar turnos."
        )
        return

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
    if context.args and context.args[0].lower() == "pdf":
        await _relatorio_mes_pdf_cmd(update, context)
        return
    await _comando_relatorio(update, context, tipo="mes")


def _parse_mes_arg(arg: str) -> tuple[int, int | None]:
    """
    Retorna (mes, ano). Ano pode ser None se não especificado.
    Suporta:
    - 1..12
    - janeiro..dezembro (case insensitive, prefixos de 3 letras)
    - mm-yyyy ou mm/yyyy
    """
    arg = arg.lower().strip()
    
    # Check for mm-yyyy or mm/yyyy
    if "-" in arg:
        parts = arg.split("-")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0]), int(parts[1])
    if "/" in arg:
        parts = arg.split("/")
        if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
            return int(parts[0]), int(parts[1])

    # Map month names
    meses = {
        "jan": 1, "janeiro": 1,
        "fev": 2, "fevereiro": 2,
        "mar": 3, "marco": 3, "março": 3,
        "abr": 4, "abril": 4,
        "mai": 5, "maio": 5,
        "jun": 6, "junho": 6,
        "jul": 7, "julho": 7,
        "ago": 8, "agosto": 8,
        "set": 9, "setembro": 9,
        "out": 10, "outubro": 10,
        "nov": 11, "novembro": 11,
        "dez": 12, "dezembro": 12
    }
    
    # Check if it is a name
    for name, num in meses.items():
        if arg == name or (len(arg) >= 3 and name.startswith(arg)):
            return num, None
            
    # Try integer
    if arg.isdigit():
        return int(arg), None
        
    raise ValueError(f"Mês inválido: {arg}")


async def _relatorio_mes_pdf_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _autorizado_ou_erro(update):
        return

    settings = get_settings()
    tz = ZoneInfo(settings.timezone)
    hoje = datetime.now(tz).date()

    params: dict[str, int | str] = {}
    
    # /mes pdf [arg]
    # arg pode ser: "11", "novembro", "11-2025", "novembro 2025" (complexo, telegram split args)
    
    # Se tiver mais args, tenta juntar ou pegar o primeiro
    # context.args[0] é "pdf"
    
    mes_target = hoje.month
    ano_target = hoje.year
    
    if len(context.args) > 1:
        # Pode ser: ["pdf", "novembro"] ou ["pdf", "11-2025"] ou ["pdf", "novembro", "2025"]
        arg1 = context.args[1]
        try:
            mes_parsed, ano_parsed = _parse_mes_arg(arg1)
            mes_target = mes_parsed
            if ano_parsed:
                ano_target = ano_parsed
            elif len(context.args) > 2 and context.args[2].isdigit():
                ano_target = int(context.args[2])
        except ValueError:
            await update.message.reply_text("Mês inválido.")
            return

    params["ano"] = ano_target
    params["mes"] = mes_target
    params["telegram_user_id"] = update.effective_user.id

    url = "http://localhost:8000/relatorios/mes/pdf"
    
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params=params, timeout=30.0)
            resp.raise_for_status()
            pdf_bytes = resp.content
    except Exception as exc:
        await update.message.reply_text(f"Erro ao gerar PDF: {exc}")
        return

    await update.message.reply_document(
        document=pdf_bytes,
        filename=f"relatorio_{params['ano']}_{params['mes']:02d}.pdf",
        caption=f"Relatório Mensal PDF ({mes_target}/{ano_target})"
    )


async def remover_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _autorizado_ou_erro(update):
        return

    url = "http://localhost:8000/turnos/recentes"
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.get(url, params={"limit": 5}, timeout=10.0)
            resp.raise_for_status()
            turnos = resp.json()
    except Exception as exc:
        await update.message.reply_text(f"Erro ao buscar turnos recentes: {exc}")
        return

    if not turnos:
        await update.message.reply_text("Nenhum turno recente encontrado.")
        return

    keyboard = []
    for t in turnos:
        # t: id, data_referencia, hora_inicio, hora_fim, tipo...
        label = f"{t['data_referencia']} {t['hora_inicio'][:5]}-{t['hora_fim'][:5]} ({t['tipo'] or 'Livre'})"
        keyboard.append([InlineKeyboardButton(f"🗑 {label}", callback_data=f"del_{t['id']}")])

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Selecione um turno para remover:", reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if not _usuario_autorizado(query.from_user.id):
        await query.edit_message_text("Não autorizado.")
        return

    data = query.data
    
    # Handle deletion callbacks
    if data.startswith("del_"):
        turno_id = data.split("_")[1]
        
        url = f"http://localhost:8000/turnos/{turno_id}"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.delete(url, timeout=10.0)
                if resp.status_code == 404:
                    await query.edit_message_text("Turno não encontrado (já removido?).")
                    return
                resp.raise_for_status()
        except Exception as exc:
            await query.edit_message_text(f"Erro ao remover: {exc}")
            return

        await query.edit_message_text(f"Turno {turno_id} removido com sucesso.")
        return
    
    # Handle menu callbacks
    if data.startswith("menu_"):
        await _handle_menu_callback(query, context, data)
        return


async def _handle_menu_callback(query, context, data):
    """Handle hierarchical menu navigation."""
    action = data.replace("menu_", "")
    
    if action == "main":
        keyboard = [
            [InlineKeyboardButton("📊 Relatórios", callback_data="menu_relatorios")],
            [InlineKeyboardButton("🗑 Remover Turno", callback_data="menu_remover")],
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
            [InlineKeyboardButton("📆 Mês Anterior", callback_data="menu_mes_anterior")],
            [InlineKeyboardButton("📊 Últimos 3 Meses", callback_data="menu_ultimos_3_meses")],
            [InlineKeyboardButton("📄 PDF Mês Atual", callback_data="menu_mes_pdf")],
            [InlineKeyboardButton("📄 PDF Mês Anterior", callback_data="menu_mes_anterior_pdf")],
            [InlineKeyboardButton("📋 Escolher Mês", callback_data="menu_escolher_mes")],
            [InlineKeyboardButton("🔙 Voltar", callback_data="menu_main")],
        ]
        await query.edit_message_text(
            "📊 *Relatórios*\n\nEscolha o tipo de relatório:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif action == "semana_atual":
        # Generate report directly instead of calling the command
        if not _usuario_autorizado(query.from_user.id):
            await query.edit_message_text("Não autorizado.")
            return
            
        settings = get_settings()
        tz = ZoneInfo(settings.timezone)
        hoje = datetime.now(tz).date()
        iso = hoje.isocalendar()
        
        url = "http://localhost:8000/relatorios/semana"
        params = {"ano": iso.year, "semana": iso.week}
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=10.0)
                resp.raise_for_status()
                relatorio = resp.json()
        except Exception as exc:
            await query.edit_message_text(f"Erro ao gerar relatório: {exc}")
            return
        
        texto = _formatar_relatorio(relatorio)
        await query.edit_message_text(texto)
    
    elif action == "mes_atual":
        # Generate report directly
        if not _usuario_autorizado(query.from_user.id):
            await query.edit_message_text("Não autorizado.")
            return
            
        settings = get_settings()
        tz = ZoneInfo(settings.timezone)
        hoje = datetime.now(tz).date()
        
        url = "http://localhost:8000/relatorios/mes"
        params = {"ano": hoje.year, "mes": hoje.month}
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=10.0)
                resp.raise_for_status()
                relatorio = resp.json()
        except Exception as exc:
            await query.edit_message_text(f"Erro ao gerar relatório: {exc}")
            return
        
        texto = _formatar_relatorio(relatorio)
        await query.edit_message_text(texto)
    
    elif action == "mes_pdf":
        # Generate PDF directly
        if not _usuario_autorizado(query.from_user.id):
            await query.edit_message_text("Não autorizado.")
            return
            
        settings = get_settings()
        tz = ZoneInfo(settings.timezone)
        hoje = datetime.now(tz).date()
        
        url = "http://localhost:8000/relatorios/mes/pdf"
        params = {
            "ano": hoje.year,
            "mes": hoje.month,
            "telegram_user_id": query.from_user.id
        }
        
        await query.edit_message_text("Gerando PDF do mês atual...")
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=30.0)
                resp.raise_for_status()
                pdf_bytes = resp.content
        except Exception as exc:
            await query.edit_message_text(f"Erro ao gerar PDF: {exc}")
            return
        
        # Send as a new message since we can't edit to a document
        await query.message.reply_document(
            document=pdf_bytes,
            filename=f"relatorio_{hoje.year}_{hoje.month:02d}.pdf",
            caption=f"Relatório Mensal PDF ({hoje.month}/{hoje.year})"
        )
        await query.edit_message_text("PDF enviado!")
    
    elif action == "remover":
        # Fetch recent turns directly
        if not _usuario_autorizado(query.from_user.id):
            await query.edit_message_text("Não autorizado.")
            return
            
        url = "http://localhost:8000/turnos/recentes"
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params={"limit": 5}, timeout=10.0)
                resp.raise_for_status()
                turnos = resp.json()
        except Exception as exc:
            await query.edit_message_text(f"Erro ao buscar turnos recentes: {exc}")
            return

        if not turnos:
            await query.edit_message_text("Nenhum turno recente encontrado.")
            return

        keyboard = []
        for t in turnos:
            label = f"{t['data_referencia']} {t['hora_inicio'][:5]}-{t['hora_fim'][:5]} ({t['tipo'] or 'Livre'})"
            keyboard.append([InlineKeyboardButton(f"🗑 {label}", callback_data=f"del_{t['id']}")])

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Selecione um turno para remover:", reply_markup=reply_markup)
    
    elif action == "mes_anterior":
        # Generate report for previous month
        if not _usuario_autorizado(query.from_user.id):
            await query.edit_message_text("Não autorizado.")
            return
            
        settings = get_settings()
        tz = ZoneInfo(settings.timezone)
        hoje = datetime.now(tz).date()
        
        # Calculate previous month
        if hoje.month == 1:
            mes_anterior = 12
            ano_anterior = hoje.year - 1
        else:
            mes_anterior = hoje.month - 1
            ano_anterior = hoje.year
        
        url = "http://localhost:8000/relatorios/mes"
        params = {"ano": ano_anterior, "mes": mes_anterior}
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=10.0)
                resp.raise_for_status()
                relatorio = resp.json()
        except Exception as exc:
            await query.edit_message_text(f"Erro ao gerar relatório: {exc}")
            return
        
        texto = _formatar_relatorio(relatorio)
        await query.edit_message_text(texto)
    
    elif action == "mes_anterior_pdf":
        # Generate PDF for previous month
        if not _usuario_autorizado(query.from_user.id):
            await query.edit_message_text("Não autorizado.")
            return
            
        settings = get_settings()
        tz = ZoneInfo(settings.timezone)
        hoje = datetime.now(tz).date()
        
        # Calculate previous month
        if hoje.month == 1:
            mes_anterior = 12
            ano_anterior = hoje.year - 1
        else:
            mes_anterior = hoje.month - 1
            ano_anterior = hoje.year
        
        url = "http://localhost:8000/relatorios/mes/pdf"
        params = {
            "ano": ano_anterior,
            "mes": mes_anterior,
            "telegram_user_id": query.from_user.id
        }
        
        await query.edit_message_text("Gerando PDF do mês anterior...")
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=30.0)
                resp.raise_for_status()
                pdf_bytes = resp.content
        except Exception as exc:
            await query.edit_message_text(f"Erro ao gerar PDF: {exc}")
            return
        
        await query.message.reply_document(
            document=pdf_bytes,
            filename=f"relatorio_{ano_anterior}_{mes_anterior:02d}.pdf",
            caption=f"Relatório Mensal PDF ({mes_anterior}/{ano_anterior})"
        )
        await query.edit_message_text("PDF enviado!")
    
    elif action == "ultimos_3_meses":
        # Generate report for last 3 months
        if not _usuario_autorizado(query.from_user.id):
            await query.edit_message_text("Não autorizado.")
            return
            
        settings = get_settings()
        tz = ZoneInfo(settings.timezone)
        hoje = datetime.now(tz).date()
        
        # Calculate date 3 months ago
        fim = hoje
        inicio = hoje - timedelta(days=90)  # Approximately 3 months
        
        url = "http://localhost:8000/relatorios/periodo"
        params = {"inicio": inicio.isoformat(), "fim": fim.isoformat()}
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=10.0)
                resp.raise_for_status()
                relatorio = resp.json()
        except Exception as exc:
            await query.edit_message_text(f"Erro ao gerar relatório: {exc}")
            return
        
        texto = _formatar_relatorio(relatorio)
        await query.edit_message_text(texto)
    
    elif action == "escolher_mes":
        # Show month selection menu
        meses = [
            ("Janeiro", 1), ("Fevereiro", 2), ("Março", 3),
            ("Abril", 4), ("Maio", 5), ("Junho", 6),
            ("Julho", 7), ("Agosto", 8), ("Setembro", 9),
            ("Outubro", 10), ("Novembro", 11), ("Dezembro", 12)
        ]
        
        keyboard = []
        for i in range(0, 12, 2):
            row = []
            for j in range(2):
                if i + j < 12:
                    nome, num = meses[i + j]
                    row.append(InlineKeyboardButton(nome, callback_data=f"menu_mes_{num}"))
            keyboard.append(row)
        
        keyboard.append([InlineKeyboardButton("🔙 Voltar", callback_data="menu_relatorios")])
        
        await query.edit_message_text(
            "📋 *Escolher Mês*\n\nSelecione o mês:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif action.startswith("mes_"):
        # Handle specific month selection (e.g., "mes_11" for November)
        try:
            mes_num = int(action.split("_")[1])
        except (ValueError, IndexError):
            await query.edit_message_text("Erro ao processar mês.")
            return
            
        if not _usuario_autorizado(query.from_user.id):
            await query.edit_message_text("Não autorizado.")
            return
            
        settings = get_settings()
        tz = ZoneInfo(settings.timezone)
        hoje = datetime.now(tz).date()
        
        # Use current year by default
        ano = hoje.year
        
        url = "http://localhost:8000/relatorios/mes"
        params = {"ano": ano, "mes": mes_num}
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(url, params=params, timeout=10.0)
                resp.raise_for_status()
                relatorio = resp.json()
        except Exception as exc:
            await query.edit_message_text(f"Erro ao gerar relatório: {exc}")
            return
        
        texto = _formatar_relatorio(relatorio)
        await query.edit_message_text(texto)
    
    elif action == "perfil":
        # Mostrar perfil do usuário
        if not _usuario_autorizado(query.from_user.id):
            await query.edit_message_text("Não autorizado.")
            return
        
        user_id = query.from_user.id
        perfil = await _verificar_perfil_usuario(user_id)
        
        if not perfil:
            await query.edit_message_text(
                "⚠️ Você ainda não está cadastrado!\n\n"
                "Use o comando /start para completar seu cadastro."
            )
            return
        
        keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="menu_main")]]
        await query.edit_message_text(
            f"📝 *Seu Perfil*\n\n"
            f"Nome: *{perfil['nome']}*\n"
            f"Número de Funcionário: *{perfil['numero_funcionario']}*\n\n"
            f"_Cadastrado em: {perfil['criado_em'][:10]}_",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )
    
    elif action == "ajuda":
        help_text = (
            "ℹ️ *Comandos Disponíveis*\n\n"
            "📝 *Registrar:*\n"
            "• Envie: `<local> <hora_inicio> as <hora_fim>`\n"
            "• Exemplo: `Hospital 08:00 as 16:00`\n"
            "• Com data: `Dia DD/MM/AAAA - <local> <hora_inicio> as <hora_fim>`\n\n"
            "📊 *Relatórios:*\n"
            "• `/semana` - Relatório semanal\n"
            "• `/mes` - Relatório mensal\n"
            "• `/mes pdf` - PDF do mês atual\n"
            "• `/mes pdf <nome_mes>` - PDF de um mês específico\n\n"
            "🗑 *Remover:*\n"
            "• `/remover` - Remover turnos recentes\n\n"
            "👤 *Perfil:*\n"
            "• `/perfil` - Ver seus dados cadastrados\n\n"
            "📋 *Menu:*\n"
            "• `/menu` - Mostrar este menu\n"
        )
        keyboard = [[InlineKeyboardButton("🔙 Voltar", callback_data="menu_main")]]
        await query.edit_message_text(
            help_text,
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown"
        )


async def menu_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show main menu with hierarchical options."""
    if not _autorizado_ou_erro(update):
        return
    
    keyboard = [
        [InlineKeyboardButton("📊 Relatórios", callback_data="menu_relatorios")],
        [InlineKeyboardButton("🗑 Remover Turno", callback_data="menu_remover")],
        [InlineKeyboardButton("👤 Perfil", callback_data="menu_perfil")],
        [InlineKeyboardButton("ℹ️ Ajuda", callback_data="menu_ajuda")],
    ]
    
    await update.message.reply_text(
        "📋 *Menu Principal*\n\nEscolha uma opção:",
        reply_markup=InlineKeyboardMarkup(keyboard),
        parse_mode="Markdown"
    )


async def perfil_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Mostra o perfil do usuário ou inicia fluxo de edição."""
    if not _autorizado_ou_erro(update):
        return
    
    user_id = update.effective_user.id
    perfil = await _verificar_perfil_usuario(user_id)
    
    if not perfil:
        await update.message.reply_text(
            "⚠️ Você ainda não está cadastrado!\n\n"
            "Use o comando /start para completar seu cadastro."
        )
        return
    
    await update.message.reply_text(
        f"📝 *Seu Perfil*\n\n"
        f"Nome: *{perfil['nome']}*\n"
        f"Número de Funcionário: *{perfil['numero_funcionario']}*\n\n"
        f"_Cadastrado em: {perfil['criado_em'][:10]}_",
        parse_mode="Markdown"
    )


def build_application() -> Application:
    settings = get_settings()

    if not settings.telegram_bot_token:
        logging.warning("TELEGRAM_BOT_TOKEN não configurado; bot do Telegram não será iniciado.")

    app = (
        ApplicationBuilder()
        .token(settings.telegram_bot_token)
        .build()
    )

    # ConversationHandler para onboarding
    onboarding_handler = ConversationHandler(
        entry_points=[CommandHandler("start", iniciar_onboarding)],
        states={
            AGUARDANDO_NOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_nome)],
            AGUARDANDO_NUMERO: [MessageHandler(filters.TEXT & ~filters.COMMAND, receber_numero)],
        },
        fallbacks=[CommandHandler("cancelar", cancelar_onboarding)],
    )

    app.add_handler(onboarding_handler)
    app.add_handler(CommandHandler("perfil", perfil_cmd))
    app.add_handler(CommandHandler("semana", relatorio_semana_cmd))
    app.add_handler(CommandHandler("mes", relatorio_mes_cmd))
    app.add_handler(CommandHandler("remover", remover_cmd))
    app.add_handler(CommandHandler("menu", menu_cmd))
    app.add_handler(CommandHandler("ajuda", ajuda))
    app.add_handler(CommandHandler("assinar", assinar))  # ✅ Novo comando
    app.add_handler(CallbackQueryHandler(button_handler))
    
    # Aplicar rate limit ao handler de texto (onde spam é mais provável)
    # Nota: Decorators em handlers registrados assim precisam ser aplicados na definição da função.
    # Como registrar_turno_msg está definida acima, vamos aplicá-lo lá.
    
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), registrar_turno_msg))
    return app
```
