# Gestão de Turnos 🕒

![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Aplicação completa para gestão de turnos de trabalho via **Bot do Telegram** com API FastAPI, integração CalDAV e geração de relatórios em PDF.

## ✨ Funcionalidades

### 🤖 Bot do Telegram
- **Registro de Turnos**: Envie mensagens simples como `Hospital 08:00 as 16:00`
- **Parsing Flexível**: Suporta diversos formatos de entrada
  - `<local> <hora_inicio> as <hora_fim>`
  - `Dia DD/MM/AAAA - <local> <hora_inicio> as <hora_fim>`
- **Menu Interativo**: Navegação hierárquica com inline keyboards
  - 📊 Relatórios (Semana, Mês, PDF)
  - 🗑 Remover turnos recentes
  - 👤 Visualizar perfil
  - ℹ️ Ajuda
- **Sistema de Perfil Obrigatório**: 
  - Cadastro de Nome e Número de Funcionário
  - Verificação automática antes de registros
  - Comando `/perfil` para visualizar dados

### 📊 Relatórios Avançados
- **Relatórios Textuais**:
  - `/semana` - Semana atual
  - `/mes` - Mês atual
  - Suporte a períodos customizados
- **Relatórios PDF**:
  - `/mes pdf` - PDF do mês atual
  - `/mes pdf <nome_mes>` - PDF de mês específico (ex: `novembro`)
  - Cabeçalho com nome e número do funcionário
  - Rodapé com timestamp de geração
  - Tabela detalhada: Data, Local, Entrada, Saída, Total de horas
- **Filtros Avançados** (via menu):
  - Mês anterior
  - Últimos 3 meses
  - Seletor interativo de mês

### 🗑 Gestão de Turnos
- **Comando `/remover`**: Delete turnos recentes via botões inline
- Visualização dos 5 turnos mais recentes
- Confirmação automática após exclusão

### 🔗 Integração CalDAV
- Sincronização automática com calendários (Nextcloud, Disroot, etc.)
- Criação/atualização de eventos ao registrar turnos
- Cálculo automático de duração (inclusive turnos que passam da meia-noite)

## 🚀 Instalação e Uso

### Pré-requisitos

- Python 3.13+ (se rodar fora do Docker)
- Conta no Telegram e bot criado via [@BotFather](https://t.me/BotFather)
- Calendário CalDAV (opcional - Nextcloud, Disroot, etc.)
- Docker e Docker Compose (recomendado)

### Configuração

1. Clone o repositório:
```bash
git clone <seu-repo>
cd gestao_turnos
```

2. Crie um arquivo `.env` baseado no exemplo:
```bash
cp .env.example .env
```

3. Configure as variáveis de ambiente:
```env
# Fuso horário
APP_TIMEZONE=Europe/Lisbon

# Banco de dados
SQLITE_PATH=data/gestao_turnos.db

# Telegram Bot
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_ALLOWED_USERS=123456789,987654321

# CalDAV (opcional)
CALDAV_URL=https://cloud.disroot.org/remote.php/dav
CALDAV_USERNAME=seu_usuario
CALDAV_PASSWORD=sua_senha
CALDAV_CALENDAR_PATH=personal
```

### Executar com Docker (Recomendado)

```bash
docker compose up -d --build
```

A API estará disponível em `http://localhost:8000`

### Executar Localmente

```bash
# Instalar dependências
pip install -r requirements.txt

# Executar
uvicorn app.main:app --reload
```

## 📱 Comandos do Bot

### Comandos Básicos
- `/start` - Iniciar cadastro (primeira vez)
- `/menu` - Menu interativo principal
- `/perfil` - Ver seus dados cadastrados

### Registro de Turnos
Envie mensagens como:
```
Hospital 08:00 as 16:00
Clínica 14:00 as 22:00
Dia 01/12/2025 - Urgências 00:00 as 08:00
```

### Relatórios
- `/semana` - Relatório semanal
- `/semana 2025-48` - Semana específica
- `/semana ultimos7` - Últimos 7 dias
- `/mes` - Relatório mensal
- `/mes 2025-12` - Mês específico
- `/mes pdf` - PDF do mês atual
- `/mes pdf novembro` - PDF de novembro

### Gestão
- `/remover` - Remover turnos recentes (via botões)

## 🔌 API Endpoints

### Turnos
- `POST /turnos` - Criar turno
- `GET /turnos?inicio=YYYY-MM-DD&fim=YYYY-MM-DD` - Listar turnos
- `DELETE /turnos/{id}` - Deletar turno
- `GET /turnos/recentes?limit=5` - Últimos turnos

### Usuários
- `GET /usuarios/{telegram_user_id}` - Buscar usuário
- `POST /usuarios` - Criar usuário
- `PUT /usuarios/{telegram_user_id}` - Atualizar usuário

### Relatórios
- `GET /relatorios/periodo?inicio=YYYY-MM-DD&fim=YYYY-MM-DD` - Período customizado
- `GET /relatorios/semana?ano=YYYY&semana=WW` - Relatório semanal
- `GET /relatorios/mes?ano=YYYY&mes=MM` - Relatório mensal
- `GET /relatorios/mes/pdf?ano=YYYY&mes=MM&telegram_user_id=ID` - PDF mensal

## 🗂️ Estrutura do Projeto

```
gestao_turnos/
├── app/
│   ├── caldav_client.py    # Integração CalDAV
│   ├── config.py           # Configurações
│   ├── crud.py             # Operações de banco de dados
│   ├── database.py         # Setup SQLAlchemy
│   ├── main.py             # API FastAPI
│   ├── models.py           # Modelos ORM
│   ├── reports.py          # Geração de PDF
│   ├── schemas.py          # Schemas Pydantic
│   └── telegram_bot.py     # Lógica do bot
├── data/                   # Banco de dados SQLite
├── docker-compose.yml      # Configuração Docker
├── Dockerfile              # Imagem Docker
├── requirements.txt        # Dependências Python
└── .env                    # Variáveis de ambiente
```

## 🛠️ Tecnologias Utilizadas

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Bot**: python-telegram-bot
- **Banco de Dados**: SQLite
- **PDF**: ReportLab
- **CalDAV**: caldav (Python library)
- **Containerização**: Docker, Docker Compose

## 📄 Licença

Este projeto é de uso pessoal. Sinta-se livre para adaptá-lo às suas necessidades.

## 👨‍💻 Autor

Desenvolvido para gestão pessoal de turnos de trabalho com integração completa ao Telegram.
