# Registro de desenvolvimento

## 2026-09-29 — Filtros musicais consistentes entre modo local e online

### Implementado
- Corrigidas consultas como `não quero instrumental` e `sem energia alta`; adicionados reconhecimento de energia média e aliases de voz/letras.
- Criado resolvedor compartilhado de filtros e predicado aplicado ao ranking local, à seleção da IA e ao fallback online.
- Adicionado `filters.excluded_energy`, com validação de níveis e conflitos. Filtros explícitos prevalecem por dimensão; conflitos textuais não resolvidos retornam 422 antes de chamadas externas.
- Energia desconhecida é descartada quando há exclusões; `parsed_query` reflete os filtros efetivos, sem manter a energia originalmente sugerida pela IA quando foi substituída.
- Atualizada versão do ranking local para `local-rules-v2`; documentado contrato atual separadamente dos exemplos planejados no roadmap.

### Arquivos principais alterados
- `api/app/services/music_filters.py`
- `api/app/services/recommendation_service.py`
- `api/app/services/online_recommendations.py`
- `api/app/schemas/recommendation.py`
- `api/app/routes/recommendations.py`
- `api/tests/test_music_filters.py`
- `api/tests/test_recommendations.py`
- `api/tests/test_online.py`
- `api/tests/test_books.py`
- `docs/05-API-Specification.md`
- `docs/eval-reports/2026-09-29-music-filters.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Excluir um nível de energia permite os outros níveis, sem inferir arbitrariamente um único valor oposto.
- `energy` explícito não nulo ou presença de `excluded_energy` substitui as restrições textuais dessa dimensão; lista vazia permite limpá-las. Voz é resolvida independentemente.
- Nenhuma nova dependência, migração ou serviço pago. Providers/IA foram testados com transporte simulado.
- As regras dos modos de leitura permanecem próprias. Comparativos, dupla negação e listas abreviadas não fazem parte do vocabulário garantido do novo parser.

### Estado atual
- 119 testes da API passaram, incluindo 46 novos casos. Ruff e formatação aprovados.
- Smoke/E2E com API real, SQLite e navegação offline passaram; build do frontend aprovado.
- Permanece um aviso de depreciação da integração Starlette/httpx. Qualidade das classificações reais da IA e PostgreSQL não foram avaliados nesta etapa.

### Próximos passos
- Avaliar referências por título: correspondência por palavras completas, títulos negados e diferenças entre seleção da IA e fallback em `api/app/services/online_recommendations.py`.
- Criar julgamentos independentes de relevância para pelo menos 15 consultas por módulo e medir Precision@K/nDCG e diversidade, incluindo os cinco modos de leitura.
- Reconciliar os demais exemplos planejados da especificação e ADRs com o modo online antes de ampliar integrações; manter o modo local gratuito.

## 2026-09-29 — Exclusões coordenadas no parser de recomendações

### Implementado
- Corrigida a interpretação de listas como `sem romance, terror e política`: todos os temas são excluídos.
- Pontuação forte, quebras de linha, adversativas e retomadas explícitas de preferência delimitam a propagação da exclusão.
- Adicionado corpus de 24 consultas e duas verificações de ranking/explicações sem rede; registrado relatório com escopo e limitações.
- Corrigida captura de variável de loop apontada pelo Ruff em um teste online existente.

### Arquivos principais alterados
- `api/app/services/recommendation_service.py`
- `api/tests/test_intent_rules.py`
- `api/tests/test_online.py`
- `docs/eval-reports/2026-09-29-local-intent.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Processar temas na ordem textual e preservar limites de frases antes de normalizar a consulta; propagar negação somente em listas coordenadas.
- Manter o parser determinístico compartilhado pelos modos local e online, sem dependências ou chamadas externas adicionais.
- Preservar a precedência de exclusões e a interpretação conservadora de `pouco`/`menos`; o corpus não equivale ao golden set completo do roadmap.

### Estado atual
- Corpus e ranking passaram; a suíte da API passou com 73 testes. Há um aviso de depreciação da integração Starlette/httpx.
- O código já contém integração online Groq/MusicBrainz/Open Library adicionada no commit `7916989`, posterior ao registro anterior. Esta etapa valida seus testes com fakes, sem chamadas reais ou revisão completa dessa integração.
- Não foram implementados histórico pessoal, feedback, salvos ou interface de conta nesta etapa.

### Próximos passos
- Ampliar o corpus em `api/tests/test_intent_rules.py` para referências e filtros de voz/energia; avaliar negações desses filtros separadamente dos temas.
- Criar julgamentos de relevância para pelo menos 15 consultas por módulo e medir Precision@K/nDCG e diversidade, conforme `docs/12-development-roadmap.md`.
- Reconciliar documentação e ADRs do modo online com `7916989` antes de ampliar essa integração; preservar o modo local gratuito.

## 2026-09-28 — Fluxos públicos funcionais em modo local gratuito

### Implementado
- Implementados os três endpoints usados pela interface: descoberta de músicas, descoberta de livros e trilha de leitura, com explicações dos critérios reais.
- Catálogo de 18 livros e 25 músicas, busca de título/autor, ranking por temas, referências, exclusões simples, filtros de voz/energia e diversidade por criador. Nenhuma chamada a LLM ou serviço pago.
- `api/local.py` aplica migrações SQLite e mantém banco/segredo em `api/.local`; `start-local.ps1` inicia API e frontend, verifica portas/prontidão e oferece instalação explícita de dependências gratuitas.
- Readiness valida todas as tabelas e aceita SQLite sem pgvector. Open Library/PostgreSQL continuam opcionais.
- Interface informa catálogo local e duração estimada. Links musicais são buscas externas, sem áudio ou duração de gravação inventados.
- Testes de recomendações sem rede, filtros, exclusões, expiração, validação e persistência após reinício; E2E com API real, SQLite temporário e recursos externos do navegador bloqueados.

### Arquivos principais alterados
- `api/app/providers/local_catalog.py`
- `api/app/services/recommendation_service.py`
- `api/app/schemas/recommendation.py`
- `api/app/routes/recommendations.py`
- `api/app/services/book_service.py`
- `api/app/routes/books.py`
- `api/app/core/config.py`
- `api/app/main.py`
- `api/local.py`
- `api/.env.example`
- `api/.gitignore`
- `api/tests/test_recommendations.py`
- `api/tests/test_local.py`
- `api/tests/test_books.py`
- `api/tests/test_migrations.py`
- `frontend/src/lib/api.ts`
- `frontend/src/pages/Discovery.tsx`
- `frontend/src/pages/ReadWithMusic.tsx`
- `frontend/tests/live.mjs`
- `frontend/package.json`
- `start-local.ps1`
- `README.md`
- `api/README.md`
- `docs/adr/0013-free-local-mode.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Modalidade local sem Docker, chaves externas, embeddings ou LLM, conforme a restrição de custo. Catálogo editorial limitado, sem prometer interpretação semântica avançada.
- Iniciador isola banco/provider de configurações externas; dados/segredo são ignorados pelo Git. Migrações usam conexão explícita para não atingir `DATABASE_URL` externo.
- Resultados anônimos ficam em memória por uma hora, até 256 buscas por processo; explicações usam o resultado armazenado.
- Trilhas estimam cinco minutos por faixa, não repetem itens para completar duração e avisam quando a seleção fica curta. “Poucos vocais” usa instrumentais conservadoramente.

### Estado atual
- 34 testes de backend, smoke/E2E do frontend com API real e build passaram. Verificação visual desktop/celular sem overflow; detector da skill de interface sem achados nas alterações.
- Iniciador completo verificado: frontend em `127.0.0.1:5173`, API em `127.0.0.1:8000`, readiness 200 e CORS correto. A checagem de portas respeita uma instância existente em IPv6 sem bloqueá-la ou encerrá-la.
- Os três fluxos públicos funcionam sem rede após instalação. Auth funciona na API com persistência, sem tela de conta. Histórico pessoal, feedback, salvos, reprodução/exportação de playlists e deploy público continuam pendentes.
- PostgreSQL/pgvector e concorrência de refresh entre processos permanecem sem validação real. Links de terceiros exigem conexão, mas não são necessários para gerar sugestões.

### Próximos passos
- Expandir `api/app/providers/local_catalog.py` e criar consultas de avaliação de relevância, exclusões e cobertura do parser antes de prometer compreensão mais ampla.
- Para ampliar catálogo pela rede, concluir ADR-0012 e validar provider sem contratar serviços; preservar modo offline e testes sem rede.
- Para personalização, integrar auth à interface e persistir recomendações/feedback com isolamento por usuário, migrações e testes antes de expor histórico ou salvos.
- Antes de deploy, validar PostgreSQL real, migrações reversas, concorrência de refresh e rate limiting compartilhado; configuração local não é destinada a múltiplas instâncias públicas.

## 2026-09-28 — Cache persistente de busca externa de livros

### Implementado
- Criada a migração `0004_external_search_cache` com chave por tipo, provider, consulta normalizada e limite, resposta JSON e expiração em milissegundos Unix.
- A busca de livros reutiliza respostas válidas entre reinícios da API quando há banco configurado. Novas buscas persistem catálogo e cache na mesma transação; entradas vencidas são removidas nas gravações. Sem banco, o cache em memória continua ativo.
- Testes cobrem reutilização após reinício, separação por limite, resposta vazia, expiração, upgrade/downgrade SQLite e geração SQL PostgreSQL.
- Iniciada a avaliação do provider musical no ADR-0012 com documentação oficial e uma pequena amostra real da API MusicBrainz.

### Arquivos principais alterados
- `api/alembic/versions/0004_external_search_cache.py`
- `api/app/models/external_search_cache.py`
- `api/app/models/__init__.py`
- `api/app/providers/base.py`
- `api/app/services/book_service.py`
- `api/tests/test_books.py`
- `api/tests/test_migrations.py`
- `api/README.md`
- `docs/04-Data-Model.md`
- `docs/05-API-Specification.md`
- `docs/12-development-roadmap.md`
- `docs/adr/0012-music-provider-selection.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- A tabela suporta múltiplos tipos de entidade, mas a integração atual é só de livros. O TTL é o mesmo do cache em memória (`BOOK_SEARCH_CACHE_TTL_SECONDS`); valor zero desabilita ambos.
- Respostas normalizadas são armazenadas após o upsert do catálogo na mesma transação. O cache persistente evita novas chamadas ao provider e não prolonga sua validade ao ser lido.
- O MusicBrainz ainda não foi escolhido como fonte definitiva: a amostra mostrou campos de duração e tags incompletos, e falta comparar Last.fm com chave e avaliar licenças e cobertura para G1.

### Estado atual
- A busca de livros funciona com cache persistente em banco migrado e com cache em memória sem banco. Os testes em SQLite, lint e formatação passam.
- O caminho PostgreSQL/pgvector e a concorrência entre processos não foram validados neste ambiente. O provider musical permanece em avaliação, sem endpoints musicais implementados.

### Próximos passos
- Em ambiente com Docker, rodar `alembic upgrade head` e `downgrade base` em PostgreSQL com pgvector descartável; testar reutilização e expiração do cache com duas instâncias da API.
- Completar a matriz do ADR-0012: obter chave de desenvolvimento Last.fm, medir amostra de estilos variados, cobertura de tags/gêneros/duração e latência, e confirmar obrigações de licença/atribuição para os campos usados.
- Após fechar G1, implementar `MusicProvider`, catálogo de músicas e `GET /music/search`/`GET /music/{id}` com normalização e testes de contrato.

## 2026-09-28 — Metadados de descrição e assuntos na busca de livros

### Implementado
- A busca Open Library solicita descrição e assuntos junto dos campos bibliográficos e normaliza esses dados no `BookItem`.
- Descrições são limitadas a 2.000 caracteres; até 12 assuntos únicos são mantidos, com até 120 caracteres cada. O catálogo existente persiste esses campos e o detalhe por ID os devolve.
- Testes cobrem o contrato do provider, limites de tamanho e leitura dos metadados persistidos.

### Arquivos principais alterados
- `api/app/providers/open_library.py`
- `api/tests/test_books.py`
- `api/README.md`
- `docs/05-API-Specification.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Os campos são obtidos na mesma chamada de busca, evitando consultas adicionais por obra. Valores ausentes ou inválidos permanecem vazios; `genres` não é inferido a partir de assuntos.
- Os limites de tamanho controlam o volume de resposta e de dados armazenados. O cache de consultas externas continua em memória por processo.

### Estado atual
- Busca e detalhe retornam descrição e assuntos quando a Open Library os fornece. `pytest` passou com 19 testes; Ruff e formatação passaram.
- Docker Engine continua indisponível neste ambiente; a migração e a persistência em PostgreSQL com pgvector ainda não foram validadas.

### Próximos passos
- Em ambiente com Docker, subir `api/compose.yaml`, executar `alembic upgrade head` e `downgrade base` em banco descartável e validar busca e detalhe no PostgreSQL.
- Avaliar cache persistente com TTL para consultas externas e medir a latência da busca com os novos campos em uma consulta real.
- Prosseguir com o spike e a implementação do provider musical conforme `docs/adr/0012-music-provider-selection.md`, incluindo normalização, cache e endpoints de busca musical.

## 2026-09-28 — Catálogo persistente de livros

### Implementado
- Criada a migração Alembic `0003_books_catalog` e o modelo `Book`, com unicidade por provider/ID externo e índice por título.
- A busca Open Library persiste ou atualiza os itens no catálogo quando PostgreSQL/SQLite estiver configurado; sem banco, a busca continua disponível sem persistência.
- Implementado `GET /api/v1/books/{id}` para consultar livros já catalogados, com 404 para IDs ausentes e 503 quando o catálogo não está configurado ou acessível.

### Arquivos principais alterados
- `api/alembic/versions/0003_books_catalog.py`
- `api/app/models/book.py`
- `api/app/models/__init__.py`
- `api/app/models/account.py`
- `api/app/services/book_service.py`
- `api/app/routes/books.py`
- `api/app/main.py`
- `api/tests/test_books.py`
- `api/tests/test_migrations.py`
- `api/README.md`
- `docs/04-Data-Model.md`
- `docs/05-API-Specification.md`
- `docs/DEVELOPMENT_LOG.md`
- `docs/12-development-roadmap.md`

### Decisões técnicas
- A chave única é `(provider, external_id)`; upsert nativo de PostgreSQL/SQLite deixa as atualizações idempotentes e o ID público determinístico da Open Library é preservado.
- A persistência síncrona usa o pool de threads do Starlette para não bloquear o event loop da rota assíncrona.
- O detalhe lê somente do catálogo local. Não chama provider por ID porque essa operação ainda não faz parte do contrato de `BookProvider`.
- Descrição, gêneros e assuntos ficam preparados no schema para enriquecimento futuro; o provider atual ainda não preenche esses campos.

### Estado atual
- Busca e detalhe são cobertos com migração e SQLite; `pytest` passou com 18 testes e Ruff/formatação passaram.
- PostgreSQL com pgvector ainda não foi executado neste ambiente por indisponibilidade do Docker Engine. A busca textual do catálogo e os índices GIN permanecem pendentes.

### Próximos passos
- Validar upgrade/downgrade da migração `0003` e persistência no PostgreSQL com pgvector em ambiente com Docker.
- Enriquecer o provider Open Library com descrição e assuntos de forma limitada, e avaliar cache persistente de consultas externas.
- Continuar Fase 2 do roadmap com provider musical, normalização e os endpoints de busca musical; em seguida avançar ao parser e ranking previstos nas Fases 3 e 4.

## 2026-09-28 — Autenticação da API com refresh rotativo

### Implementado
- Criadas as rotas `POST /api/v1/auth/register`, `/login`, `/refresh`, `/logout` e `GET /api/v1/auth/me` com validação de entrada e erros padronizados.
- Senhas usam Argon2id; access tokens usam JWT HS256 de 15 minutos; refresh tokens opacos de 7 dias são armazenados como hash SHA-256, rotacionados a cada uso e revogados por família quando há reuso.
- Adicionado limite em memória por IP/rota e por e-mail em login/registro. Testes cobrem cadastro, login genérico, expiração e adulteração do JWT, rotação, reuso, logout, ownership e `429`.
- Alinhados contrato de entrega dos tokens e decisões de segurança no ADR-0006 e nas especificações de API e segurança.

### Arquivos principais alterados
- `api/app/routes/auth.py`
- `api/app/services/auth_service.py`
- `api/app/core/security.py`
- `api/app/core/rate_limit.py`
- `api/app/core/config.py`
- `api/app/schemas/auth.py`
- `api/app/main.py`
- `api/tests/test_auth.py`
- `api/pyproject.toml`
- `api/.env.example`
- `api/README.md`
- `docs/adr/0006-jwt-authentication-strategy.md`
- `docs/05-API-Specification.md`
- `docs/09-security-specification.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- O cliente recebe access e refresh tokens em JSON e os mantém somente em memória. Cookie `HttpOnly` exige definição futura de domínios e CSRF; recarregar a página encerra a sessão atual.
- `JWT_SECRET` de pelo menos 32 bytes é exigido ao usar auth. Sem ele, essas rotas respondem `503`, preservando a busca pública de livros.
- A rotação bloqueia a linha do token no banco; o limitador atual é local ao processo. Ambos precisam de validação ou substituição adequada antes de escalar a API.

### Estado atual
- Os testes de API passam em SQLite com migrações Alembic e transporte HTTP local. Registro, login, refresh, logout e consulta ao usuário estão implementados.
- O Docker Engine segue indisponível nesta máquina. Migrações, auth e concorrência de refresh ainda não foram testadas em PostgreSQL com pgvector. O frontend ainda não consome as rotas de auth e não mantém sessão.

### Próximos passos
- Em ambiente com Docker, iniciar `api/compose.yaml`, executar `alembic upgrade head` e validar fluxos de auth e refresh concorrente em PostgreSQL; testar `downgrade base` em banco descartável.
- Integrar registro/login/refresh/logout no frontend mantendo tokens em memória, incluindo estados de sessão expirada e uso de `/auth/me`.
- Prosseguir no backend com catálogo local persistido e `GET /books/{id}`; depois implementar os providers e endpoints de recomendações previstos no roadmap. Antes de escalar horizontalmente, migrar o rate limit de auth para armazenamento compartilhado.

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
