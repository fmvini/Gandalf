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

Para habilitar autenticação, configure `JWT_SECRET` em `.env` com pelo menos 32 bytes aleatórios, por exemplo usando `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Sem o segredo, as rotas de autenticação respondem `503`; a busca pública de livros continua disponível. O registro exige e-mail válido, username de 3 a 32 caracteres (`A–Z`, `0–9`, `_`, `.` ou `-`) e senha de 10 a 128 caracteres.

## Endpoints implementados

| Método | Rota | Estado |
|---|---|---|
| GET | `/health` | Liveness local |
| GET | `/health/ready` | Verifica conexão, schema e extensão pgvector |
| GET | `/version` | Versão da API; ranking ainda não implementado |
| GET | `/api/v1/books/search?q=Duna&limit=6` | Busca textual de título na Open Library |
| POST | `/api/v1/auth/register` | Cria conta com senha Argon2id |
| POST | `/api/v1/auth/login` | Emite JWT HS256 e refresh token opaco |
| POST | `/api/v1/auth/refresh` | Rotaciona refresh; reuso revoga a família |
| POST | `/api/v1/auth/logout` | Revoga o refresh token da conta autenticada |
| GET | `/api/v1/auth/me` | Retorna usuário do Bearer token |

A busca usa uma chamada por vez por processo, intervalo mínimo de 1 segundo e cache em memória por 5 minutos. O ID de cada livro é um UUID determinístico derivado do ID da obra na Open Library; ainda não existe catálogo local persistido. Timeouts e falhas do catálogo retornam erros padronizados, sem resultados inventados.

Login e refresh retornam `access_token` (15 minutos) e `refresh_token` (7 dias) em JSON. O cliente deve manter ambos somente em memória e descartá-los no logout; o refresh anterior deixa de valer após a rotação. A sessão termina ao recarregar a página. O limite inicial de auth é de 10 requisições por minuto por IP/rota e, para login/registro, também por e-mail; ele fica em memória por processo e não substitui um limite compartilhado em produção.

## Verificar

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app alembic tests
```

Os testes usam um provider falso, transporte HTTP simulado e SQLite para subir e reverter as migrações e exercitar a autenticação. O caminho PostgreSQL/pgvector da migração e o bloqueio concorrente do refresh token ainda precisam ser validados com um banco real. Uma busca real precisa de acesso à Open Library e pode responder `504 UPSTREAM_TIMEOUT` quando ela exceder o timeout de 5 segundos. Recomendações e trilhas de leitura ainda serão implementadas.
