# API do Gandalf

Primeira fatia do backend FastAPI descrito em [Arquitetura do Sistema](../docs/03-System-Architecture.md). A raiz do backend é `api/`, conforme a organização atual do projeto; as camadas internas seguem a separação entre rotas, serviços, schemas e providers.

## Executar no Windows

```powershell
cd api
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item .env.example .env
docker compose up -d db
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

O Compose expõe PostgreSQL com pgvector em `127.0.0.1:5433`. Troque a senha de exemplo em `.env` e mantenha `POSTGRES_PASSWORD` e `DATABASE_URL` coerentes. A busca de livros pode rodar sem banco; as rotas que dependem de persistência exigem a migração. Swagger: `http://127.0.0.1:8000/docs`. Para o frontend, use `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`. Configure `OPEN_LIBRARY_CONTACT_EMAIL` em `.env` para identificar as chamadas à Open Library. As origens CORS permitidas estão em `CORS_ORIGINS` (lista JSON).

## Endpoints implementados

| Método | Rota | Estado |
|---|---|---|
| GET | `/health` | Liveness local |
| GET | `/health/ready` | Verifica conexão, schema e extensão pgvector |
| GET | `/version` | Versão da API; ranking ainda não implementado |
| GET | `/api/v1/books/search?q=Duna&limit=6` | Busca textual de título na Open Library |

A busca usa uma chamada por vez por processo, intervalo mínimo de 1 segundo e cache em memória por 5 minutos. O ID de cada livro é um UUID determinístico derivado do ID da obra na Open Library; ainda não existe catálogo local persistido. Timeouts e falhas do catálogo retornam erros padronizados, sem resultados inventados.

## Verificar

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app alembic tests
```

Os testes usam um provider falso, transporte HTTP simulado e SQLite para subir e reverter as migrações. O caminho PostgreSQL/pgvector da migração ainda precisa ser validado com um banco real. Uma busca real precisa de acesso à Open Library e pode responder `504 UPSTREAM_TIMEOUT` quando ela exceder o timeout de 5 segundos. Autenticação, recomendações e trilhas de leitura ainda serão implementadas.
