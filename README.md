# Gestão de Turnos 🕒

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-17-blue.svg)
![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)

**Sistema SaaS Multi-Tenant** para gestão de turnos de trabalho via **Bot do Telegram** com backend em FastAPI e PostgreSQL. Inclui sistema completo de assinaturas (Stripe), integração com CalDAV e segurança robusta com Row-Level Security (RLS).

---

## ✨ Funcionalidades Principais

### 🤖 Bot do Telegram Inteligente
- **Registro Natural**: Suporta mensagens como `"Hospital 08:00 as 16:00"` ou `"Dia 25/12 - Plantão 19:00 as 07:00"`.
- **Fluxo de Onboarding**: Registro guiado de novos usuários com validação.
- **Perfil do Usuário**: Comando `/perfil` exibe dados cadastrais e **status da assinatura**.
- **Gestão Facilitada**:
  - `/remover`: Remove turnos recentes via botões interativos.
  - `/menu`: Painel de controle completo.

### 💳 Sistema de Assinaturas (SaaS)
- **Trial Gratuito Automatizado**: Novos usuários recebem automaticamente **14 dias de teste grátis** do plano Pro.
- **Planos**:
  - **Free**: Funcionalidades essenciais.
  - **Pro**: Relatórios avançados, PDF e backup CalDAV.
- **Integração Stripe**:
  - Checkout seguro.
  - Webhooks para processamento em tempo real de pagamentos, upgrades e cancelamentos.
  - Portal do cliente para gestão de faturas.

### 📊 Relatórios Poderosos
- **Formatos Flexíveis**:
  - Texto simples: Para visualização rápida no chat (`/semana`, `/mes`).
  - **PDF Profissional**: Relatórios mensais detalhados com totalização de horas e agrupamento por local (`/mes pdf`).
- **Filtros**: Por semana, mês ou período personalizado.

### 🔐 Segurança e Arquitetura
- **Multi-Tenancy Real**: Isolamento de dados garantido no nível do banco de dados via **PostgreSQL Row-Level Security (RLS)**.
- **Middleware de Segurança**: Contexto de usuário injetado automaticamente em cada transação.
- **Clean Architecture**: Separação clara de responsabilidades (Domain, Application, Infrastructure).
- **Testes Abrangentes**: Cobertura de testes de integração, RLS e lógica de negócios.

### 📅 Sincronização CalDAV
- Integração unidirecional com calendários (Nextcloud, Google, etc.).
- Eventos criados/atualizados automaticamente no calendário do usuário ao registrar turnos.

---

## 🚀 Instalação e Execução

### Pré-requisitos
- Docker e Docker Compose
- Token de Bot do Telegram (@BotFather)
- Chaves de API Stripe (Opcional, para assinaturas)

### Passo a Passo

1. **Clone o repositório:**
   ```bash
   git clone <seu-repo>
   cd gestao_turnos
   ```

2. **Configure o ambiente:**
   ```bash
   cp .env.example .env
   ```
   Edite o arquivo `.env` com suas credenciais (Telegram, Database, Stripe).

3. **Inicie os serviços:**
   ```bash
   docker compose up -d
   ```

4. **Aplique as migrações do banco:**
   ```bash
   docker compose exec backend uv run alembic upgrade head
   ```

5. **Acesse:**
   - API: `http://localhost:8000/docs`
   - Bot: No Telegram, busque pelo seu bot e envie `/start`.

---

## 🧪 Testes e Qualidade

O projeto mantém uma suíte de testes robusta utilizando `pytest`.

```bash
# Testes do Backend
docker compose exec backend uv run pytest tests/ -v

# Testes do Bot
docker compose exec bot uv run pytest tests/ -v
```

**Estatísticas Atuais:**
- ✅ **43+ Testes Backend** passando.
- ✅ **Testes Bot** passando.

---

## 📂 Estrutura do Projeto

```
backend/                  # API Rest (FastAPI)
├── app/
│   ├── api/              # Endpoints
│   ├── services/         # Regras de Negócio (Stripe, Relatórios)
│   └── main.py           # Entrypoint API
├── tests/                # Testes de Integração Backend
└── Dockerfile

bot/                      # Frontend Telegram
├── src/
│   ├── handlers/         # Comandos e Callbacks
│   ├── api_client.py     # Cliente HTTP para Backend
│   └── main.py           # Entrypoint Bot
├── tests/                # Testes Unitários Bot
└── Dockerfile
```

## 🛠️ Stack Tecnológico

- **Linguagem**: Python 3.13
- **Framework Web**: FastAPI
- **Banco de Dados**: PostgreSQL 17 (Async + RLS)
- **Gerenciador de Pacotes**: uv
- **ORM**: SQLAlchemy 2.0 (AsyncSession)
- **Containerização**: Docker
- **Testes**: Pytest

---

**Desenvolvido com ❤️ e Python.**
