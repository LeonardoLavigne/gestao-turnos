# Estrutura Clean Architecture

Este projeto segue os princípios de Clean Architecture com foco em separação de responsabilidades e testabilidade.

## Camadas

### 📝 Domain (Núcleo do Negócio)
- `entities/` - Entidades de negócio (Usuario, Turno, Assinatura)
- `value_objects/` - Value Objects (Plano, Periodo)
- `repositories/` - Interfaces de repositórios (Ports)
- `services/` - Serviços de domínio (lógica complexa)
- `exceptions/` - Exceções de domínio

**Regra:** Esta camada NÃO depende de nenhuma outra.

### 🎯 Application (Casos de Uso)
- `use_cases/` - Orquestração de lógica de negócio
  - `turnos/` - Criar, listar, deletar turnos
  - `assinaturas/` - Criar checkout, processar webhooks
  - `relatorios/` - Gerar PDF, Excel
- `dtos/` - Data Transfer Objects

**Regra:** Depende apenas de Domain.

### 🔌 Infrastructure (Adapters)
- `database/` - SQLAlchemy, repositories impl
- `stripe/` - Cliente Stripe, webhook handlers
- `caldav/` - Cliente CalDAV
- `telegram/` - Bot e handlers
- `logging/` - Logging estruturado

**Regra:** Implementa interfaces definidas em Domain.

### 🌐 Presentation (Interface Externa)
- `api/` - FastAPI routes (REST API)

**Regra:** Usa Application use cases.

## Fluxo de Dados

```
Request → Presentation → Application (Use Case) → Domain → Infrastructure
```

## Benefícios

- ✅ Testabilidade (mocks fáceis)
- ✅ Manutenibilidade (mudanças isoladas)
- ✅ Escalabilidade (trocar infraestrutura sem afetar lógica)
