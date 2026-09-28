# API do Gandalf

FastAPI com busca de livros, recomenda??es locais e autentica??o persistente.

## Modo local gratuito

```powershell
cd api
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe local.py
```

`local.py` gera um segredo em `.local/jwt-secret`, aplica migra??es em `.local/gandalf.db` e inicia em `127.0.0.1:8000`. Banco, segredo e provider s?o isolados do `.env` e de `DATABASE_URL`. N?o h? chamada externa nesse modo. `GANDALF_PORT` permite outra porta e `GANDALF_LOCAL_DATA` outro diret?rio de dados. Na raiz, `start-local.ps1` inicia API e interface juntas.

Swagger: http://127.0.0.1:8000/docs. Frontend: `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`. CORS local permite `localhost:5173` e `127.0.0.1:5173`.

## Endpoints implementados

| M?todo | Rota | Comportamento |
|---|---|---|
| GET | `/health` | Processo ativo |
| GET | `/health/ready` | Banco e todas as tabelas; pgvector exigido apenas no PostgreSQL |
| GET | `/version` | Vers?o da aplica??o e `local-rules-v1` |
| GET | `/api/v1/books/search?q=Duna&limit=6` | T?tulo/autor local, ou Open Library se configurada |
| GET | `/api/v1/books/{id}` | Livro local ou catalogado pelo provider externo |
| POST | `/api/v1/recommendations/music` | Ranking musical local |
| POST | `/api/v1/recommendations/books` | Ranking de livros local |
| POST | `/api/v1/recommendations/read-with-music` | Sele??o musical por livro e modo |
| GET | `/api/v1/recommendations/{id}/items/{item_id}/explanation` | Crit?rios usados, por at? uma hora |
| POST | `/api/v1/auth/register` | Cadastro com Argon2id |
| POST | `/api/v1/auth/login` | JWT e refresh opaco |
| POST | `/api/v1/auth/refresh` | Rota??o; reuso revoga a fam?lia |
| POST | `/api/v1/auth/logout` | Revoga refresh da conta autenticada |
| GET | `/api/v1/auth/me` | Usu?rio do Bearer token |

## Recomenda??es

Descoberta recebe `query` (3?1.000 caracteres), `limit` (1?25, padr?o 10) e `filters` opcionais (`vocals`: `none`, `required`, `optional`; `energy`: `low`, `medium`, `high`, para m?sica).

```json
{"query":"M?sicas calmas para estudar","filters":{"vocals":"none","energy":"low"},"limit":10}
```

Leitura recebe `book_id`, `mode` (`FOCUS`, `IMMERSIVE`, `CINEMATIC`, `CALM`, `CUSTOM`), `context` (at? 500 caracteres, obrigat?rio em `CUSTOM`), `vocals` (`INSTRUMENTAL`, `MINIMAL`, `ANY`) e `target_duration_min` (15?120).

O ranking faz correspond?ncia de temas editoriais, exclus?es simples, filtros expl?citos, remove t?tulos usados como refer?ncia e limita dois itens por artista/autor. Empates s?o ordenados por t?tulo. `scores.context` ? a fra??o de temas correspondentes, n?o similaridade de embeddings. Pedidos n?o reconhecidos retornam vazio com orienta??o.

`meta.mode=local` e `meta.hint` identificam os limites. S?o 18 livros e 25 m?sicas; links musicais abrem buscas, sem ?udio hospedado. A trilha estima cinco minutos por faixa (`playlist.duration_estimated=true`), sem atribuir dura??o real ?s grava??es. Pode haver menos itens que a dura??o ou limite pedidos.

Resultados an?nimos ficam em mem?ria por at? uma hora, no m?ximo 256 buscas por processo. Explica??es expiram no rein?cio. Hist?rico pessoal, feedback e playlists persistentes n?o est?o implementados.

## Provider externo opcional e PostgreSQL

O caminho anterior continua dispon?vel:

```powershell
Copy-Item .env.example .env
# Ajuste DATABASE_URL, POSTGRES_PASSWORD, JWT_SECRET e BOOK_PROVIDER=open_library
# O Docker Engine precisa estar dispon?vel
docker compose up -d db
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Compose usa PostgreSQL/pgvector na porta 5433. `BOOK_PROVIDER=local` ? o padr?o; `open_library` habilita busca externa de livros e requer internet. Recomenda??es continuam locais. Configure `OPEN_LIBRARY_CONTACT_EMAIL` para identificar chamadas. Essa integra??o n?o ? necess?ria para usar o sistema.

A busca externa tem intervalo m?nimo de um segundo, timeout de cinco segundos e cache em mem?ria; com banco, persiste cat?logo/cache (`BOOK_SEARCH_CACHE_TTL_SECONDS`, padr?o 300, zero desabilita). IDs s?o UUIDs determin?sticos, descri??es limitadas a 2.000 caracteres e assuntos a 12 entradas de 120 caracteres. Falhas externas retornam erros padronizados. `provider`, se informado na busca, precisa corresponder ao provider ativo.

Fora do iniciador local, auth exige banco migrado e `JWT_SECRET` de pelo menos 32 bytes; sem segredo responde 503. Registro exige e-mail v?lido, username de 3?32 caracteres e senha de 10?128. Access token dura 15 minutos e refresh sete dias. Mantenha tokens apenas em mem?ria no cliente. Rate limiting de auth ? por processo e n?o serve para m?ltiplas inst?ncias p?blicas.

## Verifica??o

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app local.py alembic tests
.\.venv\Scripts\python.exe -m ruff format --check app local.py alembic tests
```

Testes cobrem migra??es SQLite, auth, cat?logo/cache externo com fakes, recomenda??es sem rede e rein?cio local com persist?ncia. `frontend/tests/live.mjs` sobe a API com banco tempor?rio. PostgreSQL/pgvector e concorr?ncia de refresh entre processos precisam de valida??o real antes de deploy.
