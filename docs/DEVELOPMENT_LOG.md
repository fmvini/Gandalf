# Registro de desenvolvimento

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
