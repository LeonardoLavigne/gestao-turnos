# Gestão de Turnos 🕒

![Python](https://img.shields.io/badge/Python-3.13-blue.svg)
![FastAPI](https://img.shields.io/badge/FastAPI-0.115-green.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)

**Sistema SaaS Multi-Tenant** com backend robusto em FastAPI e PostgreSQL. Inclui sistema completo de assinaturas (Stripe), integração com CalDAV e segurança robusta com Row-Level Security (RLS).

---

## ✨ Funcionalidades do Backend

### 🔐 Segurança e Arquitetura
- **Multi-Tenancy Real**: Isolamento de dados garantido no nível do banco de dados via **PostgreSQL Row-Level Security (RLS)**.
- **Middleware de Segurança**: Contexto de usuário injetado automaticamente em cada transação.
- **Clean Architecture**: Separação clara de responsabilidades (Domain, Application, Infrastructure).
- **Testes Abrangentes**: Cobertura de testes de integração, RLS e lógica de negócios.

### 💳 Sistema de Assinaturas (SaaS)
- **Trial Gratuito Automatizado**: Novos usuários recebem automaticamente **14 dias de teste grátis** do plano Pro.
- **Integração Stripe**: Checkout seguro e Webhooks para processamento em tempo real.

### 📅 Sincronização CalDAV
- Integração unidirecional com calendários (Nextcloud, Google, etc.).
- Eventos criados/atualizados automaticamente no calendário do usuário ao registrar turnos.

---

## 🤖 Bot Telegram

*(Documentação e detalhes previstos para a próxima sprint)*

---

## 💻 Frontend Web (Next.js)

*(Documentação e detalhes previstos para a próxima sprint)*

---

## 🚀 Instalação e Execução

### Pré-requisitos
- Docker e Docker Compose
- Token de Bot do Telegram (Opcional para testes manuais apenas do backend)
- Chaves de API Stripe (Opcional)

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
   Edite o arquivo `.env` com suas credenciais.

3. **Inicie os serviços:**
   ```bash
   make up
   # ou
   docker compose up -d
   ```

4. **Aplique as migrações do banco:**
   ```bash
   make alembic-upgrade
   # ou
   docker compose exec backend uv run alembic upgrade head
   ```

5. **Acesse a API:**
   - Swagger Documentation: `http://localhost:8000/docs`
   - ReDoc: `http://localhost:8000/redoc`

---

## 🧪 Testes e Qualidade

O projeto mantém uma suíte de testes robusta utilizando `pytest`.

```bash
# Testes do Backend
make test-backend
```

**Estatísticas Atuais:**
- ✅ **48+ Testes Backend** passando (Cobertura de RLS, Casos de Uso e Repositórios).

---

## 📂 Estrutura do Backend

```
backend/                  # API Rest (FastAPI)
├── app/
│   ├── api/              # Endpoints (Routers)
│   ├── application/      # Use Cases (Regras de Aplicação)
│   ├── domain/           # Entidades e Interfaces (Core)
│   ├── infrastructure/   # Implementação de Banco e Serviços Externos
│   └── main.py           # Entrypoint API
├── tests/                # Testes de Integração Backend
└── Dockerfile
```

## 🛠️ Stack Tecnológico

- **Linguagem**: Python 3.13
- **Framework Web**: FastAPI
- **Banco de Dados**: PostgreSQL 15 (Async + RLS)
- **Gerenciador de Pacotes**: uv
- **ORM**: SQLAlchemy 2.0 (AsyncSession)
- **Containerização**: Docker
