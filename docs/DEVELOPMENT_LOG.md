# Registro de desenvolvimento

## 2026-09-28 — Base relacional e migrações

### Implementado
- Adicionado Compose de PostgreSQL 18 com pgvector e configuração de conexão em `api/.env.example`.
- Criados modelos SQLAlchemy para usuários, refresh tokens, preferências, interações e histórico de busca, com Alembic para extensões e tabelas.
- `GET /health/ready` agora verifica conexão, schema e extensão pgvector.

### Arquivos principais alterados
- `api/compose.yaml`
- `api/alembic.ini`
- `api/alembic/env.py`
- `api/alembic/versions/0001_extensions.py`
- `api/alembic/versions/0002_accounts.py`
- `api/app/models/account.py`
- `api/app/database/session.py`
- `api/app/main.py`
- `api/app/core/config.py`
- `api/tests/test_migrations.py`
- `api/pyproject.toml`
- `api/README.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- As extensões `citext` e `vector` são habilitadas apenas em PostgreSQL; os mesmos scripts migram SQLite para testes locais.
- `recommendation_id` fica sem chave estrangeira até a tabela de recomendações existir. A integridade será adicionada na migração dessa etapa.
- O Compose usa uma imagem versionada do pgvector e porta local 5433 para não conflitar com o PostgreSQL já instalado nesta máquina.

### Estado atual
- Upgrade e downgrade do Alembic passam em SQLite; o Compose passa na validação de configuração.
- O Docker Engine não está disponível nesta máquina; o PostgreSQL local pede credenciais e não tem pgvector. A migração PostgreSQL ainda não foi executada aqui.
- A API de livros continua funcional sem banco. Readiness só responderá 200 após PostgreSQL, pgvector e schema estarem disponíveis.

### Próximos passos
- Implementar registro, login, refresh rotativo, logout e `GET /auth/me` sobre os novos modelos, com Argon2id e JWT HS256; testar expiração, reuso e revogação de família.
- Validar `alembic upgrade head` e `downgrade base` em um PostgreSQL com pgvector, por exemplo com `cd api; docker compose up -d db` onde o Docker Engine estiver disponível.
- Depois da autenticação, implementar rate limiting de auth e persistir cache/catálogo de livros.

## 2026-09-28 — Primeira fatia da API e busca de livros

### Implementado
- Criada a aplicação FastAPI em `api/`, com configuração tipada, CORS explícito, ID de requisição, erros padronizados e rotas de saúde e versão.
- Implementado `GET /api/v1/books/search` com provider Open Library, normalização de livros, limite de chamadas externas e cache curto em memória.
- Adicionados testes sem dependência de rede para rotas, validação, CORS, cache e contrato do provider.

### Arquivos principais alterados
- `api/app/main.py`
- `api/app/routes/books.py`
- `api/app/providers/open_library.py`
- `api/app/services/book_service.py`
- `api/app/schemas/book.py`
- `api/app/core/config.py`
- `api/tests/test_books.py`
- `api/pyproject.toml`
- `api/README.md`
- `frontend/README.md`
- `docs/03-System-Architecture.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- A raiz é `api/` por solicitação do projeto; a árvore de referência em `docs/03-System-Architecture.md` foi alinhada a esse caminho e às rotas em `app/routes/`.
- A busca usa o parâmetro `title` da Open Library porque o seletor do frontend recebe um título, e apenas obras válidas são normalizadas. IDs UUID são derivados de forma determinística do ID da obra; a persistência local virá depois.
- O cache e a limitação de uma chamada por segundo são locais ao processo e atendem apenas ao início do desenvolvimento. A Open Library recomenda identificação da aplicação e cache para uso frequente.
- `/health/ready` retorna 503 enquanto PostgreSQL/pgvector não estiver configurado, sem indicar prontidão inexistente.

### Estado atual
- A estrutura de API, os endpoints de saúde/versão e a busca de livros estão implementados. Os testes automatizados passaram com provider falso.
- Uma consulta real durante esta etapa excedeu o timeout de 5 segundos e retornou `504 UPSTREAM_TIMEOUT`; a disponibilidade da Open Library neste ambiente não foi confirmada.
- O frontend em `frontend/` já possui Home, descoberta e trilha de leitura com tema escuro padrão. A API ainda não oferece autenticação, recomendações nem geração de trilha; o seletor de livros é o único fluxo do frontend conectado a um endpoint implementado.

### Próximos passos
- Completar a Fase 1 de `docs/12-development-roadmap.md`: PostgreSQL + pgvector, Alembic/migração 0001, modelos iniciais, autenticação JWT com refresh rotativo e testes de migração/autenticação.
- Substituir o cache em memória por cache persistido com TTL e implementar `GET /books/{id}` sobre catálogo local. Verificar em ambiente com rede a latência e disponibilidade da Open Library e configurar contato no User-Agent.
- Seguir a Fase 2 com provider musical validado pelo ADR `docs/adr/0012-music-provider-selection.md`; depois implementar parser, ranking e os três endpoints `POST /recommendations/*` usados pelo frontend.
