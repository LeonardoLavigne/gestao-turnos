## Gestão de Turnos – Bot Telegram + FastAPI

Aplicação pessoal para registrar turnos de trabalho via bot do Telegram e enviar esses registros para um calendário CalDAV (Disroot/Nextcloud), com relatórios semanais e mensais.

### Requisitos

- Python 3.14 (se rodar fora de Docker).
- Conta no Telegram e um bot criado via `@BotFather`.
- Calendário CalDAV (ex: Disroot).

### Variáveis de ambiente principais

Use um arquivo `.env` (veja `.env.example`) com:

- `APP_TIMEZONE`: fuso horário para cálculo dos turnos (ex: `Europe/Lisbon`).
- `SQLITE_PATH`: caminho do arquivo SQLite (no container já fica como `/app/data/gestao_turnos.db`).
- `TELEGRAM_BOT_TOKEN`: token do bot no Telegram.
- `TELEGRAM_ALLOWED_USERS`: lista de `user_id` do Telegram separados por vírgula (ex: `123456789,987654321`).
- `CALDAV_URL`: URL base do CalDAV (ex: `https://cloud.disroot.org/remote.php/dav`).
- `CALDAV_USERNAME`: usuário do CalDAV.
- `CALDAV_PASSWORD`: senha ou app-token do CalDAV.
- `CALDAV_CALENDAR_PATH`: parte do caminho/URL do calendário desejado (ex: `personal` ou similar).

### Subir com Docker

```bash
docker compose up -d --build
```

O serviço expõe a API em `http://localhost:8000` (ajuste conforme sua rede/Tailscale).

### Uso via Telegram

- Envie mensagens como:
  - `REN 08:00 as 16:00`
  - `Casino 21:00 as 03:00`
- Pode mandar várias linhas (uma por turno) e data explícita:
  ```
  Dia 29/11/2025 - Casino 15:00 as 03:00
  Dia 30/11/2025 - Palacio 09:30 as 19:30
  Dia 01/12/2025 - REN 00:00 as 08:00
  ```

Se o seu `user_id` estiver em `TELEGRAM_ALLOWED_USERS`, o bot irá:

- Registrar o turno na API.
- Calcular a duração, inclusive se passar da meia-noite.
- Criar/atualizar um evento no calendário CalDAV configurado.
- Comandos extras:
  - `/semana` → semana ISO atual.
  - `/semana 2025-48` → semana 48 de 2025.
  - `/semana 2025-11-29` → semana da data informada.
  - `/semana ultimos7` → últimos 7 dias corridos.
  - `/mes` ou `/mes 2025-12` → resumo do mês atual ou especificado.

### Endpoints principais (API)

- `POST /turnos`
  - Cria um turno.
- `GET /turnos?inicio=YYYY-MM-DD&fim=YYYY-MM-DD`
  - Lista turnos no intervalo.
- `GET /relatorios/periodo?inicio=YYYY-MM-DD&fim=YYYY-MM-DD`
  - Relatório agregado do período.
- `GET /relatorios/semana?ano=YYYY&semana=WW`
  - Relatório da semana ISO (ex: `ano=2025&semana=10`).
- `GET /relatorios/mes?ano=YYYY&mes=MM`
  - Relatório do mês.


