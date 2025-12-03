# Gestão de Turnos 🕒

![Python](https://img.shields.io/badge/python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)

**Sistema SaaS multi-tenant** para gestão de turnos de trabalho via **Bot do Telegram** com API FastAPI, PostgreSQL, integração Stripe para assinaturas, CalDAV e geração de relatórios em PDF.

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
  - 💳 Gerenciar assinatura
  - ℹ️ Ajuda
- **Sistema de Perfil Obrigatório**: 
  - Cadastro de Nome e Número de Funcionário
  - Verificação automática antes de registros
  - Comando `/perfil` para visualizar dados

### 💳 Sistema de Assinaturas (Stripe)
- **Planos**:
  - **Free**: Acesso básico
  - **Pro**: Funcionalidades avançadas (via `/assinar`)
- **Pagamentos**:
  - Checkout Stripe integrado
  - Webhooks para atualização automática de status
  - Portal do cliente para gerenciar assinatura
- **Controle de Acesso**:
  - Recursos premium protegidos por decorator
  - Verificação de assinatura em tempo real

### 📊 Relatórios Avançados
- **Relatórios Textuais**:
  - `/semana` - Semana atual
  - `/mes` - Mês atual
  - Suporte a períodos customizados
- **Relatórios PDF**:
  - `/mes pdf` - PDF do mês atual
  - `/mes pdf <nome_mes>` - PDF de mês específico
  - Cabeçalho com nome e número do funcionário
  - Rodapé com timestamp de geração
  - Tabela detalhada: Data, Local, Entrada, Saída, Total de horas

### 🔐 Segurança
- **Multi-Tenancy**: Isolamento total de dados via Row-Level Security (RLS)
- **Rate Limiting**: 5 mensagens por minuto por usuário
- **Health Check**: Endpoint `/health` para monitoramento
- **Logging Estruturado**: Logs em formato JSON

### 🔗 Integração CalDAV
- Sincronização automática com calendários (Nextcloud, Disroot, etc.)
- Criação/atualização de eventos ao registrar turnos
- Cálculo automático de duração

## 🚀 Instalação e Uso

### Pré-requisitos

- Docker e Docker Compose
- Conta no Telegram e bot criado via [@BotFather](https://t.me/BotFather)
- Conta Stripe (para assinaturas - opcional)
- Calendário CalDAV (opcional)

### Setup Rápido

1. **Clone o repositório:**
```bash
git clone <seu-repo>
cd gestao_turnos_migration
```

2. **Configure variáveis de ambiente:**
```bash
cp .env.example .env
```

Edite `.env` com suas credenciais:
```env
# ===== OBRIGATÓRIO =====
# Database (PostgreSQL - gerenciado pelo docker-compose)
DATABASE_URL=postgresql+psycopg://postgres:postgres@postgres:5432/gestao_turnos

# Telegram
TELEGRAM_BOT_TOKEN=seu_token_aqui
TELEGRAM_ALLOWED_USERS=123456789

# Timezone
APP_TIMEZONE=America/Sao_Paulo

# ===== OPCIONAL (Stripe) =====
STRIPE_API_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_PRO=price_...
BASE_URL=http://localhost:8000

# ===== OPCIONAL (CalDAV) =====
CALDAV_URL=https://cloud.disroot.org/remote.php/dav
CALDAV_USERNAME=seu_usuario
CALDAV_PASSWORD=sua_senha
CALDAV_CALENDAR_PATH=personal
```

3. **Suba os containers:**
```bash
docker compose up -d
```

4. **Aplicar migrations** (primeira vez):
```bash
docker compose exec gestao-turnos uv run alembic upgrade head
```

5. **Verificar logs:**
```bash
docker compose logs -f gestao-turnos
```

A API estará disponível em `http://localhost:8000`

### Comandos Úteis

```bash
# Parar containers
docker compose down

# Ver logs
docker compose logs -f

# Rebuildar após mudanças
docker compose up -d --build

# Entrar no container
docker compose exec gestao-turnos bash

# Rodar migrations
docker compose exec gestao-turnos uv run alembic upgrade head

# Criar nova migration
docker compose exec gestao-turnos uv run alembic revision --autogenerate -m "descrição"

# Rodar testes
docker compose exec gestao-turnos uv run pytest -v
```

## 📱 Comandos do Bot

### Comandos Básicos
- `/start` - Iniciar cadastro (primeira vez)
- `/menu` - Menu interativo principal
- `/perfil` - Ver seus dados cadastrados
- `/assinar` - Assinar Plano Pro (Stripe)
- `/ajuda` - Lista de comandos

### Registro de Turnos
Envie mensagens como:
```
Hospital 08:00 as 16:00
Clínica 14:00 as 22:00
Dia 01/12/2025 - Urgências 00:00 as 08:00
```

### Relatórios
- `/semana` - Relatório semanal
- `/mes` - Relatório mensal
- `/mes pdf` - PDF do mês atual
- `/mes pdf novembro` - PDF de novembro

### Gestão
- `/remover` - Remover turnos recentes (via botões)

## 🔌 API Endpoints

### Health & Monitoring
- `GET /health` - Health check (DB status)
- `GET /docs` - Documentação interativa Swagger

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

### Stripe (Assinaturas)
- `POST /webhook/stripe` - Webhook Stripe (checkout, subscription updates)

## 🗂️ Arquitetura

```
app/
├── api/                          # FastAPI routes
│   ├── health.py                # Health check
│   └── webhook.py               # Stripe webhooks
├── infrastructure/              # Adapters
│   ├── logger.py               # Structured logging (JSON)
│   ├── middleware.py           # RLS middleware
│   └── subscription_middleware.py  # Subscription check
├── services/
│   └── stripe_service.py       # Stripe integration
├── domain/                      # Domain layer (Clean Architecture)
│   ├── entities/
│   ├── value_objects/
│   └── repositories/
├── application/                 # Use cases
│   └── use_cases/
├── models.py                    # SQLAlchemy models
├── schemas.py                   # Pydantic schemas
├── config.py                    # Settings (pydantic-settings)
├── database.py                  # DB session + RLS
├── telegram_bot.py              # Bot handlers + decorators
└── main.py                      # FastAPI app
```

### Multi-Tenancy via Row-Level Security (RLS)

O sistema usa **PostgreSQL Row-Level Security** para isolamento total de dados entre usuários:

- Cada usuário só vê seus próprios turnos
- Políticas RLS em todas as tabelas (`usuarios`, `turnos`, `tipos_turno`, `assinaturas`)
- Middleware injeta `telegram_user_id` no contexto PostgreSQL
- Testes garantem isolamento (8/8 passando)

## 🛠️ Tecnologias

- **Backend**: FastAPI, SQLAlchemy, Pydantic
- **Database**: PostgreSQL 17 (com RLS)
- **Migrations**: Alembic
- **Bot**: python-telegram-bot
- **Pagamentos**: Stripe
- **PDF**: ReportLab
- **CalDAV**: caldav (Python library)
- **Containerização**: Docker, Docker Compose
- **Package Manager**: uv (ultrafast Python package manager)

## 🧪 Testes

```bash
# Rodar todos os testes
docker compose exec gestao-turnos uv run pytest -v

# Com coverage
docker compose exec gestao-turnos uv run pytest --cov=app --cov-report=html

# Testes específicos
docker compose exec gestao-turnos uv run pytest tests/test_rls_isolation.py -v
```

**Cobertura de Testes:**
- ✅ RLS Isolation (3 testes)
- ✅ Stripe Integration (2 testes)
- ✅ Health & Logging (2 testes)
- ✅ Rate Limiting (1 teste)

## 📝 Desenvolvimento

### Estrutura de Branches
- `main` - Produção estável
- `feature/*` - Novas funcionalidades
- `fix/*` - Correções

### Workflow
1. Criar branch: `git checkout -b feature/nova-funcionalidade`
2. Desenvolver e testar
3. Commit: `git commit -m "feat: descrição"`
4. Push: `git push origin feature/nova-funcionalidade`
5. Merge após validação

### Migrations
```bash
# Criar nova migration
docker compose exec gestao-turnos uv run alembic revision --autogenerate -m "descrição"

# Aplicar
docker compose exec gestao-turnos uv run alembic upgrade head

# Reverter última
docker compose exec gestao-turnos uv run alembic downgrade -1
```

## 🔒 Segurança

- **RLS**: Isolamento de dados garantido no nível do banco
- **Stripe Webhooks**: Verificação de assinatura obrigatória
- **Rate Limiting**: Proteção contra spam (5 msgs/min)
- **Environment Variables**: Credenciais nunca commitadas
- **Health Checks**: Monitoramento contínuo da aplicação

## 📄 Licença

Este projeto é de uso pessoal. Sinta-se livre para adaptá-lo às suas necessidades.

## 👨‍💻 Autor

Desenvolvido para gestão pessoal de turnos de trabalho com arquitetura SaaS multi-tenant.

---

**Status:** ✅ Pronto para produção  
**Testes:** 8/8 passando  
**Warnings:** 0
