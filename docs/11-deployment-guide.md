# Deployment Guide

> **Documento:** 11 de 15 — Documentação Técnica
> **Projeto:** Plataforma Inteligente de Descoberta de Músicas e Livros
> **Status:** Rascunho v1.0
> **Relacionados:** Arquitetura do Sistema (03), Security Specification (09), Testing Strategy (10), Development Roadmap (12)

> **Receita executável atual — 2026-10-03:** consulte [Integração de deploy com PostgreSQL](deployment-integration.md) para `compose.yaml` + `compose.postgres.yaml`, entrypoint `api/deploy.py`, nomes de variáveis realmente implementados e gate de Nginx/API/PostgreSQL descartável. As seções abaixo continuam sendo o desenho mais amplo de produção, incluindo opções e componentes ainda não implementados. O Compose base usa SQLite; PostgreSQL exige o overlay explícito. HTTPS, backups e publicação não são fornecidos pela receita local.

---

## 1. Objetivo

Descrever como executar, configurar e publicar a aplicação em cada ambiente (local, staging e produção), cobrindo a **Fase 11 — Deploy** do escopo: frontend, backend, banco, variáveis de ambiente e logs.

> **Nota sobre provedores de hospedagem.** O escopo não fixa provedores de infraestrutura. Este guia usa **Docker** como base portável e apresenta **opções de hospedagem** com critérios de escolha. Planos gratuitos, limites e preços mudam com frequência — **confirme nas páginas oficiais de cada provedor antes de decidir**.

---

## 2. Visão Geral da Arquitetura de Deploy

```
                  ┌────────────────────────────┐
   Usuário ─────► │  Frontend (React + Vite)   │   Build estático (CDN)
                  └─────────────┬──────────────┘
                                │ HTTPS (REST/JSON, JWT)
                  ┌─────────────▼──────────────┐
                  │  Backend (FastAPI)         │   Container Docker
                  │  - API REST                │
                  │  - Recommendation Engine   │
                  │  - AI Services             │
                  └───┬─────────┬───────────┬──┘
                      │         │           │
          ┌───────────▼──┐  ┌───▼────────┐  ┌▼──────────────────────┐
          │ PostgreSQL   │  │ LLM /      │  │ APIs externas          │
          │ + pgvector   │  │ Embeddings │  │ (Open Library, Google  │
          │ (gerenciado) │  │ (API)      │  │  Books, provider música)│
          └──────────────┘  └────────────┘  └────────────────────────┘
```

**Componentes a publicar:**

| Componente | Tipo | Requisitos |
|---|---|---|
| Frontend | Site estático (build do Vite) | CDN/hosting estático com HTTPS e *fallback* para `index.html` (SPA) |
| Backend | Container (processo Uvicorn) | Python 3.12+, HTTPS, variáveis de ambiente, *health check* |
| Banco | PostgreSQL com extensão `pgvector` | Versão com suporte a pgvector; backups |
| Segredos | Chave JWT, chave do LLM, chaves de APIs | Gerenciados pelo provedor (nunca no repositório) |

Conforme a seção 74 do escopo, a arquitetura é **monolítica modular**: um único serviço de backend, sem microservices.

---

## 3. Ambientes

| Ambiente | Finalidade | Banco | IA / Providers | Deploy |
|---|---|---|---|---|
| **local** | Desenvolvimento diário | Postgres em Docker | Chaves de desenvolvimento ou fakes | Manual (`docker compose up`) |
| **ci** | Testes automatizados | Postgres *service container* | Fakes (sem rede) | Automático |
| **staging** *(opcional)* | Validar antes de produção | Banco separado | Chaves separadas, com limite de gasto | Automático a partir de `main` |
| **production** | Demonstração pública / portfólio | Banco gerenciado com backup | Chaves de produção com limite de gasto | Manual/aprovado ou por *tag* |

> Para um projeto de portfólio, **staging é opcional**. Se houver apenas produção, use *feature branches* + CI forte + *smoke tests* pós-deploy.

---

## 4. Pré-requisitos

### Máquina de desenvolvimento

- Git
- Docker e Docker Compose
- Python 3.12+ (para rodar fora do Docker)
- Node.js LTS + npm (para o frontend)
- Chaves de API: LLM, embeddings e provedores externos (conforme seção 5)

### Contas (para produção)

- Provedor de hospedagem do backend
- Provedor de hospedagem do frontend
- Provedor de PostgreSQL gerenciado com suporte a pgvector
- Conta do provedor de LLM/embeddings, **com limite de gasto configurado**
- (Opcional) serviço de monitoramento de erros/logs

---

## 5. Variáveis de Ambiente

### 5.1. Backend

| Variável | Obrigatória | Exemplo | Descrição |
|---|---|---|---|
| `APP_ENV` | Sim | `production` | `local`, `test`, `staging`, `production` |
| `APP_DEBUG` | Não | `false` | **Sempre `false` em produção** |
| `DATABASE_URL` | Sim | `postgresql+psycopg://user:pass@host:5432/db` | String de conexão SQLAlchemy |
| `JWT_SECRET_KEY` | Sim | *(64+ caracteres aleatórios)* | Assinatura dos JWT |
| `JWT_ALGORITHM` | Não | `HS256` | Algoritmo de assinatura |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Não | `15` | Expiração do access token |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Não | `7` | Expiração do refresh token |
| `CORS_ORIGINS` | Sim | `https://app.exemplo.com` | Origens permitidas (lista separada por vírgula). **Nunca `*` em produção** |
| `LLM_PROVIDER` | Sim | *(definido no ADR)* | Identificador do provedor de LLM |
| `LLM_API_KEY` | Sim* | `***` | *Exceto em testes/fakes |
| `LLM_MODEL` | Sim | *(nome do modelo)* | Modelo usado no parser e explainer |
| `LLM_TIMEOUT_SECONDS` | Não | `20` | Timeout de chamadas ao LLM |
| `EMBEDDING_PROVIDER` | Sim | *(definido no ADR)* | Provedor de embeddings |
| `EMBEDDING_MODEL` | Sim | *(nome do modelo)* | Modelo de embeddings |
| `EMBEDDING_DIMENSIONS` | Sim | *(dimensão do modelo)* | **Deve coincidir com a coluna `vector(N)` do banco** |
| `BOOK_PROVIDER` | Sim | `open_library` | Provider de livros ativo |
| `MUSIC_PROVIDER` | Sim | *(definido no ADR)* | Provider de música ativo |
| `MUSIC_PROVIDER_API_KEY` | Depende | `***` | Se o provider exigir chave |
| `GOOGLE_BOOKS_API_KEY` | Não | `***` | Se `BOOK_PROVIDER=google_books` |
| `CACHE_TTL_SECONDS` | Não | `86400` | TTL do cache de APIs externas |
| `RATE_LIMIT_DEFAULT` | Não | `60/minute` | Limite geral por cliente |
| `RATE_LIMIT_AUTH` | Não | `5/minute` | Limite para login/registro |
| `LOG_LEVEL` | Não | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |
| `LOG_FORMAT` | Não | `json` | `json` em produção, `console` em local |

> ⚠️ **`EMBEDDING_DIMENSIONS` e a coluna `vector(N)`:** trocar de modelo de embeddings com dimensão diferente exige **migração e reindexação** dos vetores existentes. Ver seção 8.4.

### 5.2. Frontend

| Variável | Exemplo | Descrição |
|---|---|---|
| `VITE_API_BASE_URL` | `https://api.exemplo.com` | URL base da API |

> ⚠️ Variáveis `VITE_*` são **embutidas no bundle e públicas**. **Nunca** coloque chaves secretas no frontend.

### 5.3. Arquivos `.env`

- O repositório contém apenas `.env.example` (sem valores reais).
- `.env` e `.env.*` reais estão no `.gitignore`.
- Em produção, use o **gerenciador de segredos do provedor**, não arquivos.

```dotenv
# .env.example (backend)
APP_ENV=local
APP_DEBUG=true
DATABASE_URL=postgresql+psycopg://app:app@localhost:5432/app
JWT_SECRET_KEY=change-me
CORS_ORIGINS=http://localhost:5173
LLM_PROVIDER=
LLM_API_KEY=
LLM_MODEL=
EMBEDDING_PROVIDER=
EMBEDDING_MODEL=
EMBEDDING_DIMENSIONS=
BOOK_PROVIDER=open_library
MUSIC_PROVIDER=
LOG_LEVEL=DEBUG
LOG_FORMAT=console
```

Gerar um segredo JWT seguro:

```bash
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

---

## 6. Ambiente Local com Docker Compose

### 6.1. `docker-compose.yml` (ilustrativo)

```yaml
services:
  db:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: app
      POSTGRES_PASSWORD: app
      POSTGRES_DB: app
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U app -d app"]
      interval: 5s
      timeout: 5s
      retries: 10

  backend:
    build: ./backend
    env_file: ./backend/.env
    environment:
      DATABASE_URL: postgresql+psycopg://app:app@db:5432/app
    depends_on:
      db:
        condition: service_healthy
    ports:
      - "8000:8000"
    volumes:
      - ./backend/app:/srv/app/app     # hot reload em desenvolvimento
    command: >
      sh -c "alembic upgrade head &&
             uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

  frontend:
    build: ./frontend
    environment:
      VITE_API_BASE_URL: http://localhost:8000
    ports:
      - "5173:5173"
    depends_on:
      - backend

volumes:
  pgdata:
```

### 6.2. Comandos

```bash
# 1. Configurar variáveis
cp backend/.env.example backend/.env       # preencher chaves

# 2. Subir tudo
docker compose up --build

# 3. Acessar
#   Frontend:      http://localhost:5173
#   API:           http://localhost:8000
#   Swagger/OpenAPI: http://localhost:8000/docs

# 4. Rodar testes dentro do container
docker compose exec backend pytest -m "unit or integration"

# 5. Resetar o banco (destrutivo!)
docker compose down -v
```

---

## 7. Containerização do Backend

### 7.1. `backend/Dockerfile` (ilustrativo, produção)

```dockerfile
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /srv/app

# Dependências (camada cacheável)
COPY requirements.txt .
RUN pip install -r requirements.txt

# Código
COPY . .

# Usuário sem privilégios
RUN useradd --create-home --shell /usr/sbin/nologin appuser \
    && chown -R appuser:appuser /srv/app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

# Nº de workers conforme CPU/memória disponíveis
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
```

Boas práticas:

- Imagem base `slim`; **não** rodar como `root`.
- Dependências fixadas (`requirements.txt` com versões travadas ou lockfile).
- Migrações **não** ficam no `CMD` em produção (ver seção 8.2).
- `.dockerignore` excluindo `.env`, `.git`, `tests/`, `__pycache__`.

### 7.2. Endpoints de saúde (requisito de deploy)

O backend deve expor:

| Endpoint | Finalidade | Verifica |
|---|---|---|
| `GET /health` | *Liveness* | Processo respondendo (sem dependências externas) |
| `GET /health/ready` | *Readiness* | Conexão com o banco e migração aplicada |

Usados pelo provedor para reiniciar instâncias e pelos *smoke tests* pós-deploy.

---

## 8. Banco de Dados

### 8.1. Requisitos

- **PostgreSQL 15+** (recomendado 16) com extensão **`pgvector`**.
- Provedor gerenciado deve permitir `CREATE EXTENSION vector`. **Verifique isso antes de escolher o provedor.**
- Conexão via TLS em produção.
- Usuário da aplicação com privilégios mínimos (sem `SUPERUSER`).

### 8.2. Migrações (Alembic)

- A **primeira migração** habilita a extensão:

```python
# alembic/versions/0001_enable_pgvector.py
from alembic import op

def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS vector")
```

- Em produção, execute as migrações como **etapa separada de release** (antes de iniciar a nova versão), não dentro do `CMD` do container:

```bash
alembic upgrade head
```

- **Estratégia para migrações seguras (expand/contract):** adicionar colunas/tabelas primeiro; migrar dados; remover colunas antigas só em um deploy posterior. Evita *downtime* e permite *rollback* de aplicação.
- Sempre testar `upgrade` e `downgrade` em banco limpo na CI.

### 8.3. Índices vetoriais

- Criar índice **HNSW** (ou IVFFlat) nas colunas `embedding` de `Music` e `Book` com o operador adequado (`vector_cosine_ops` para similaridade de cosseno).
- Para o volume do MVP (milhares de itens), a busca exata pode ser suficiente; adicione o índice quando a latência justificar (medir com `EXPLAIN ANALYZE`).

### 8.4. Troca de modelo de embeddings

1. Criar nova coluna `embedding_v2 vector(N_novo)`.
2. Reprocessar embeddings em *batch* (job/script).
3. Alternar leitura para a nova coluna (flag de configuração).
4. Remover a coluna antiga em deploy posterior.

### 8.5. Backups

| Item | Recomendação |
|---|---|
| Frequência | Diária (mínimo) — verificar o que o provedor oferece |
| Retenção | 7–14 dias para o portfólio |
| Teste de restauração | Ao menos uma vez antes do go-live |
| Exportação manual | `pg_dump` antes de migrações destrutivas |

```bash
pg_dump --format=custom --no-owner "$DATABASE_URL" > backup_$(date +%F).dump
pg_restore --no-owner --dbname "$DATABASE_URL_TARGET" backup_YYYY-MM-DD.dump
```

---

## 9. Deploy do Backend

### 9.1. Critérios para escolher a hospedagem

| Critério | Por que importa |
|---|---|
| Suporte a containers Docker | Portabilidade |
| Variáveis/segredos gerenciados | Segurança |
| HTTPS automático + domínio próprio | Requisito de produção |
| *Health checks* e reinício automático | Disponibilidade |
| Logs acessíveis | Observabilidade (seção 59 do escopo) |
| Comportamento em *idle* (planos gratuitos costumam "adormecer" instâncias) | Afeta a primeira requisição (*cold start*) na demo |
| Região próxima ao banco | Latência |
| Possibilidade de *release command* para migrações | Fluxo de migração seguro |

### 9.2. Opções a avaliar

Plataformas comuns para este tipo de projeto (avaliar planos vigentes): **Render**, **Railway**, **Fly.io**, **Google Cloud Run**, **Azure Container Apps**, **AWS App Runner**, ou uma VPS própria com Docker + Caddy/Nginx.

Para banco com pgvector, opções comuns: **Neon**, **Supabase**, **Railway (Postgres)**, **Render (Postgres)**, ou Postgres próprio em VPS. **Confirme suporte atual a pgvector e limites do plano.**

### 9.3. Fluxo genérico de deploy

```
1. Build da imagem Docker (CI)
2. Push para registry (ou build pelo provedor)
3. Executar migrações (release command)
4. Iniciar nova versão
5. Health check /health/ready
6. Smoke tests pós-deploy
7. Tráfego direcionado à nova versão
```

### 9.4. Configuração de produção do backend

- `APP_ENV=production`, `APP_DEBUG=false`.
- **Docs OpenAPI (`/docs`)**: manter habilitado para o portfólio (a spec de API é um entregável), mas sem expor endpoints administrativos.
- CORS restrito ao domínio do frontend.
- *Rate limiting* ativo (seção 62).
- Timeout do servidor e das chamadas externas configurados.
- Nº de *workers* ajustado ao plano (memória!). Modelos de embedding **locais** consomem muita RAM — se usar API de embeddings, o consumo é baixo.

---

## 10. Deploy do Frontend

### 10.1. Build

```bash
cd frontend
npm ci
VITE_API_BASE_URL=https://api.exemplo.com npm run build
# saída em frontend/dist
```

### 10.2. Hospedagem

Qualquer hosting estático com HTTPS serve: **Vercel**, **Netlify**, **Cloudflare Pages**, **GitHub Pages**, ou servir `dist/` pelo próprio Nginx/Caddy.

Requisitos:

- **Fallback de SPA:** todas as rotas (`/*`) devem servir `index.html` (necessário para React Router).
- **Cache:** assets com *hash* no nome → cache longo; `index.html` → sem cache longo.
- **Cabeçalhos de segurança** (quando o hosting permitir): `Content-Security-Policy`, `X-Content-Type-Options`, `Referrer-Policy`.

### 10.3. Domínios

| Recurso | Exemplo |
|---|---|
| Frontend | `https://app.exemplo.com` |
| API | `https://api.exemplo.com` |

Domínios em subdomínios do mesmo site simplificam CORS e cookies (se *refresh tokens* forem usados via cookie `HttpOnly`). Se a decisão do ADR sobre armazenamento de refresh token mudar, revise esta seção.

---

## 11. CI/CD (GitHub Actions)

O workflow inicial implementado está em [`.github/workflows/ci.yml`](../.github/workflows/ci.yml), com escopo e validação registrados em [CI.md](CI.md). Ele verifica API/ranking local e build/E2E, sem deploy. O exemplo abaixo descreve etapas futuras, incluindo PostgreSQL, mypy e auditorias ainda não integradas.

### 11.1. Workflow de integração (ilustrativo)

```yaml
# .github/workflows/ci.yml
name: CI

on:
  pull_request:
  push:
    branches: [main]

jobs:
  backend:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env:
          POSTGRES_USER: app
          POSTGRES_PASSWORD: app
          POSTGRES_DB: app_test
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U app -d app_test"
          --health-interval 5s --health-timeout 5s --health-retries 10
    env:
      APP_ENV: test
      DATABASE_URL: postgresql+psycopg://app:app@localhost:5432/app_test
    defaults:
      run:
        working-directory: backend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
          cache: pip
      - run: pip install -r requirements.txt -r requirements-dev.txt
      - run: ruff check . && ruff format --check .
      - run: mypy app
      - run: alembic upgrade head
      - run: pytest -m "unit or integration" --cov=app --cov-report=xml
      - run: bandit -r app -q
      - run: pip-audit

  frontend:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: frontend
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "lts/*"
          cache: npm
          cache-dependency-path: frontend/package-lock.json
      - run: npm ci
      - run: npm run lint
      - run: npx tsc --noEmit
      - run: npm test -- --run
      - run: npm run build
```

> Versões das *actions* mudam: confirme as versões atuais ao configurar.

### 11.2. Workflow de deploy

Estrutura recomendada (varia conforme o provedor):

1. **Gatilho:** *push* na `main` (staging) e *tag* `vX.Y.Z` ou aprovação manual (produção).
2. **Depende de:** CI verde.
3. **Passos:** build da imagem → *push* → migrações → deploy → *smoke tests*.
4. **Segredos:** armazenados em *GitHub Secrets/Environments*; produção com **aprovação obrigatória**.

### 11.3. Versionamento e releases

- **SemVer** (`v0.1.0`, `v0.2.0`, ..., `v1.0.0` para o MVP público).
- Tags anotadas + *release notes* geradas a partir dos commits (Conventional Commits, ver CONTRIBUTING).
- Manter `CHANGELOG.md`.

---

## 12. Logs, Monitoramento e Observabilidade

Alinhado à seção 59 do escopo.

### 12.1. Logs estruturados

- Formato **JSON** em produção; um evento por linha; saída em `stdout` (o provedor coleta).
- Campos mínimos: `timestamp`, `level`, `message`, `request_id`, `path`, `method`, `status_code`, `duration_ms`.
- **Correlation ID** (`X-Request-ID`) gerado por requisição e propagado aos logs.

### 12.2. Eventos de domínio a registrar

| Evento | Campos |
|---|---|
| Recomendação gerada | `recommendation_type`, `duration_ms`, `candidates_count`, `results_count` |
| Chamada a provider externo | `provider`, `operation`, `duration_ms`, `status`, `cache_hit` |
| Falha de provider | `provider`, `error_type`, `status_code` |
| Chamada ao LLM | `model`, `duration_ms`, `tokens_in`, `tokens_out` (quando disponível), `retries` |
| Chamada de embeddings | `model`, `batch_size`, `duration_ms` |
| Falha de validação do structured output | `error_type` (sem o conteúdo do usuário) |

### 12.3. O que **nunca** registrar

Senhas, hashes, tokens (JWT/refresh), chaves de API, `Authorization` headers, e-mails completos em logs de erro, conteúdo integral de consultas do usuário em nível `INFO` (avaliar hash/truncamento).

### 12.4. Monitoramento (opcional, recomendável)

| Necessidade | Opções |
|---|---|
| Erros e exceções | Sentry (plano gratuito) ou similar |
| Disponibilidade | UptimeRobot, Better Stack ou similar chamando `/health` |
| Métricas | Endpoint Prometheus (`/metrics`) + Grafana (pós-MVP) |
| Custo de IA | Painel do provedor de LLM + alerta de gasto |

---

## 13. Segurança em Produção

Checklist complementar à Security Specification:

- [ ] `APP_DEBUG=false`; *stack traces* nunca retornados ao cliente.
- [ ] HTTPS obrigatório (redirecionamento HTTP → HTTPS); HSTS.
- [ ] `JWT_SECRET_KEY` único por ambiente, ≥ 64 caracteres aleatórios; rotação planejada.
- [ ] CORS restrito ao(s) domínio(s) do frontend.
- [ ] Rate limiting em `/auth/*` e em endpoints que acionam LLM (custo!).
- [ ] **Limite de gasto** e alertas configurados no provedor de LLM/embeddings.
- [ ] Quota/limite por usuário e por IP em buscas anônimas (evita abuso do endpoint público que consome LLM).
- [ ] Banco acessível apenas pelo backend (rede privada/allow-list, TLS).
- [ ] Segredos apenas em gerenciador de segredos; nenhum no repositório (verificar histórico com `gitleaks`/`trufflehog`).
- [ ] Dependências auditadas (`pip-audit`, `npm audit`); atualizações automáticas (Dependabot/Renovate).
- [ ] Imagem Docker executando como usuário não-root.
- [ ] Backups ativos e restauração testada.

---

## 14. Rollback e Recuperação

### 14.1. Rollback de aplicação

1. Reimplantar a **imagem/versão anterior** (mantenha as últimas N imagens no registry).
2. Confirmar `/health/ready` e *smoke tests*.
3. Registrar o incidente e a causa.

### 14.2. Rollback de banco

- Preferir migrações **compatíveis com versão anterior** (expand/contract) para que o rollback de aplicação não exija rollback de banco.
- Se necessário: `alembic downgrade -1` **somente** após avaliar perda de dados; em último caso, restaurar backup.

### 14.3. Incidentes comuns

| Sintoma | Causa provável | Ação |
|---|---|---|
| Recomendações vazias | Provider externo fora / rate limit | Ver logs de `provider`; conferir cache e fallback |
| 500 em buscas | Falha do LLM / schema inválido | Ver logs do LLM; conferir chave, timeout e modelo |
| Latência alta | Cold start, LLM lento, busca vetorial sem índice | Medir por etapa (logs de duração); criar índice |
| 401 em massa | `JWT_SECRET_KEY` alterada | Restaurar segredo ou forçar novo login |
| Erro de CORS no navegador | `CORS_ORIGINS` incorreta | Ajustar variável e reiniciar |
| Erro de dimensão de vetor | `EMBEDDING_DIMENSIONS` ≠ coluna `vector(N)` | Ver seção 8.4 |
| Custo de IA disparou | Abuso ou laço de retry | Rate limit, limites por usuário, revisar retries |

---

## 15. Checklist de Go-Live (MVP Público)

### Infraestrutura

- [ ] Banco criado com pgvector; extensão habilitada; backups ativos.
- [ ] Migrações aplicadas (`alembic upgrade head`) sem erro.
- [ ] Backend publicado com HTTPS e domínio próprio.
- [ ] Frontend publicado com fallback de SPA e HTTPS.
- [ ] Variáveis de ambiente de produção configuradas (seção 5).

### Qualidade

- [ ] CI verde na `main` (lint, tipos, testes, segurança).
- [ ] E2E do MVP passando (Testing Strategy, seção 11).
- [ ] Baseline de qualidade das recomendações registrado.
- [ ] *Smoke tests* pós-deploy passando.

### Segurança e custos

- [ ] Checklist da seção 13 concluído.
- [ ] Limites de gasto e alertas de LLM configurados.
- [ ] Rate limiting validado em produção.

### Dados

- [ ] Base inicial de músicas/livros e embeddings carregada (se o desenho usar pré-carga).
- [ ] Cache de providers funcionando.

### Observabilidade

- [ ] Logs estruturados visíveis no provedor.
- [ ] Monitor de uptime apontando para `/health`.
- [ ] Alerta de erros configurado.

### Documentação e portfólio

- [ ] README com *screenshots*, link da demo e instruções atualizadas.
- [ ] Documentos 1–15 revisados.
- [ ] Usuário de demonstração criado (sem dados pessoais reais) e/ou modo sem login funcional.
- [ ] Tag `v1.0.0` criada e *release notes* publicadas.

---

## 16. Considerações de Custo e Limites

| Fator | Risco | Mitigação |
|---|---|---|
| LLM (por token) | Custo imprevisível com uso público | Limite de gasto; rate limit; explicação sob demanda; nunca enviar listas grandes (seção 64) |
| Embeddings | Custo por volume | Cache de embeddings; gerar uma vez por item e persistir |
| APIs externas | Rate limits | Cache (seção 60), *backoff* exponencial, fallback |
| Hospedagem gratuita | *Cold start*, limites de CPU/RAM/armazenamento | Documentar no README; *warm-up* antes de demonstrações |
| Banco gerenciado | Limites de armazenamento/conexões | Pool de conexões dimensionado; monitorar tamanho |

---

## 17. Evolução do Deploy (Pós-MVP)

- Redis para cache e rate limiting distribuído (seção 60 do escopo).
- Fila/worker para tarefas pesadas (geração de embeddings em lote, jobs de reprocessamento).
- Ambiente de staging dedicado com dados sintéticos.
- Métricas com Prometheus/Grafana e *tracing* (OpenTelemetry).
- Infraestrutura como código (Terraform/Pulumi) se migrar para nuvem pública.
- Deploy *blue/green* ou *canary* se o tráfego justificar.
