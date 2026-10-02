# API Specification

**Projeto:** {{PROJECT_NAME}}
**Versão da API:** v1
**Status:** Draft
**Base URL:** `/api/v1`
**Formato:** REST · JSON (UTF-8)
**Documentação interativa:** OpenAPI 3.1 gerada pelo FastAPI (`/docs`, `/redoc`, `/openapi.json`)
**Relacionado:** [`02-SRS`](02-SRS.md) · [`04-Data-Model`](04-Data-Model.md) · [`09-Security-Specification`](09-Security-Specification.md)

---

## 1. Convenções Gerais

### 1.1 Autenticação

| Modo | Cabeçalho | Uso |
|---|---|---|
| **Bearer JWT** | `Authorization: Bearer <access_token>` | Endpoints protegidos |
| **Opcional** | idem (pode ser omitido) | Endpoints que aceitam visitante |

Legenda de acesso nas tabelas: 🔒 obrigatório · 🔓 público · 🔓➕ opcional (personaliza se autenticado).

### 1.2 Headers Padrão

| Header | Direção | Descrição |
|---|---|---|
| `Content-Type: application/json` | Request | |
| `Accept: application/json` | Request | |
| `X-Request-ID` | Req/Resp | Correlação; gerado se ausente |
| `X-RateLimit-Limit` / `-Remaining` / `-Reset` | Response | Rate limiting |
| `Retry-After` | Response (429/503) | Segundos |

### 1.3 Convenções de Dados

- IDs: `uuid` (string).
- Datas: ISO 8601 UTC (`2026-01-31T14:20:00Z`).
- Nomes de campos: `snake_case`.
- Scores: `float` em `[0, 1]`.
- Duração: milissegundos (`duration_ms`).
- Enums: `UPPER_SNAKE_CASE` para tipos persistidos; `lower_snake_case` para atributos semânticos (ex.: `mood: ["melancholic"]`).

### 1.4 Paginação

Cursor ou offset conforme o recurso:

```
GET /recommendations/history?limit=20&cursor=<opaque>
```

Resposta:

```json
{
  "items": [ ... ],
  "next_cursor": "eyJjIjoiMjAyNi0wMS0zMSJ9",
  "has_more": true
}
```

- `limit`: padrão 20, máximo 100.

### 1.5 Formato de Erro Padronizado

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Mensagem legível para o usuário.",
    "details": [
      { "field": "query", "issue": "min_length", "message": "Informe ao menos 3 caracteres." }
    ],
    "request_id": "b6f1c1d2-…"
  }
}
```

### 1.6 Catálogo de Códigos de Erro

| HTTP | `code` | Quando |
|:---:|---|---|
| 400 | `BAD_REQUEST` | Requisição malformada |
| 401 | `UNAUTHORIZED` | Token ausente, inválido ou expirado |
| 401 | `INVALID_CREDENTIALS` | Login incorreto |
| 403 | `FORBIDDEN` | Sem permissão sobre o recurso |
| 404 | `NOT_FOUND` | Recurso inexistente |
| 409 | `CONFLICT` | E-mail/username já existentes |
| 422 | `VALIDATION_ERROR` | Falha de validação Pydantic |
| 422 | `UNPARSEABLE_QUERY` | Pedido não interpretável |
| 429 | `RATE_LIMITED` | Excedeu limite |
| 502 | `UPSTREAM_ERROR` | Falha em API externa (sem fallback) |
| 503 | `SERVICE_UNAVAILABLE` | Dependência crítica indisponível |
| 504 | `UPSTREAM_TIMEOUT` | Timeout em API externa |
| 500 | `INTERNAL_ERROR` | Erro não tratado |

> Mensagens **nunca** expõem stack traces, SQL ou segredos.

### 1.7 Idempotência

- `POST /recommendations/{id}/feedback`: idempotente por (`usuário`, `entidade`, `tipo`).
- `POST /recommendations/*`: não idempotente (gera novo registro); opcionalmente aceita `Idempotency-Key`.

### 1.8 Rate Limiting (valores iniciais)

| Escopo | Limite |
|---|---|
| Global por IP | 120 req/min |
| `/auth/login`, `/auth/register` | 10 req/min por IP/rota e por e-mail normalizado |
| `/auth/refresh` | 10 req/min por IP/rota |
| `/recommendations/*` (geração) | 20 req/min por usuário; 5 req/min visitante |
| `/…/explanation` | 30 req/hora por usuário |

---

## 2. Schemas Compartilhados

### 2.1 `MusicItem`

```json
{
  "id": "0b6c…",
  "title": "No Surprises",
  "artist": "Radiohead",
  "album": "OK Computer",
  "genres": ["alternative rock"],
  "tags": ["melancholic", "calm"],
  "duration_ms": 228000,
  "image_url": "https://…",
  "links": {
    "spotify": "https://open.spotify.com/…",
    "youtube": "https://www.youtube.com/…",
    "provider": "https://musicbrainz.org/…"
  },
  "provider": "musicbrainz",
  "external_id": "…"
}
```

### 2.2 `BookItem`

```json
{
  "id": "9a12…",
  "title": "O Senhor dos Anéis",
  "authors": ["J. R. R. Tolkien"],
  "description": "…",
  "genres": ["fantasy"],
  "subjects": ["Middle Earth", "quest"],
  "publication_year": 1954,
  "cover_url": "https://…",
  "external_url": "https://openlibrary.org/works/…",
  "provider": "open_library",
  "external_id": "OL27448W"
}
```

### 2.3 `RankedItem<T>`

```json
{
  "position": 1,
  "score": 0.87,
  "scores": {
    "semantic": 0.91,
    "preference": 0.74,
    "reference": 0.88,
    "context": 0.80,
    "popularity": 0.35,
    "penalty": 0.0
  },
  "item": { "…": "MusicItem | BookItem" },
  "user_feedback": "LIKE"
}
```

> `scores` é exposto para transparência e depuração; o frontend pode ocultá-lo.

### 2.4 `ParsedMusicIntent`

```json
{
  "intent": "music_discovery",
  "mood": ["melancholic", "calm"],
  "energy": "low",
  "atmosphere": ["atmospheric"],
  "genres": [],
  "instrumentation": [],
  "vocals": "optional",
  "intensity": "low",
  "context": "studying",
  "era": null,
  "references": [
    { "song": "No Surprises", "artist": "Radiohead", "modifiers": ["more_atmospheric"] }
  ],
  "exclusions": [],
  "language": "pt"
}
```

### 2.5 `ParsedBookIntent`

```json
{
  "intent": "book_discovery",
  "genres": ["fantasy"],
  "subgenres": ["medieval", "epic"],
  "atmosphere": ["serious", "epic"],
  "themes": ["politics", "war", "exploration", "worldbuilding"],
  "pace": "slow",
  "complexity": "high",
  "romance": "minimal",
  "focus": "world",
  "emotional_tone": ["dark"],
  "references": [{ "title": "Duna", "author": "Frank Herbert" }],
  "exclusions": ["romance_focus"],
  "language": "pt"
}
```

### 2.6 `RecommendationSummary`

```json
{
  "id": "e1f2…",
  "recommendation_type": "MUSIC_DISCOVERY",
  "query": "Quero músicas melancólicas…",
  "created_at": "2026-01-31T14:20:00Z",
  "items_count": 15
}
```

---

## 3. Autenticação (`/auth`)

Respostas de `/api/v1/auth/*`, incluindo erros, enviam `Cache-Control: no-store` e `Pragma: no-cache`. Falhas SQL de leitura ou escrita recebem `503 SERVICE_UNAVAILABLE` com mensagem genérica após rollback; conflitos de registro continuam `409 CONFLICT`.

| Método | Rota | Acesso | Descrição |
|---|---|:---:|---|
| POST | `/auth/register` | 🔓 | Cria conta |
| POST | `/auth/login` | 🔓 | Emite tokens |
| POST | `/auth/refresh` | 🔓 | Rotaciona refresh, emite novo access |
| POST | `/auth/logout` | 🔒 | Revoga refresh token |
| GET | `/auth/me` | 🔒 | Dados do usuário autenticado |

### 3.1 `POST /auth/register`

**Request**
```json
{ "email": "ana@exemplo.com", "username": "ana", "password": "S3nh@Forte!" }
```

**Validações:** e-mail válido; `username` 3–32 caracteres ASCII `[A-Za-z0-9_.-]`; senha de 10–128 caracteres, preservando espaços e Unicode. E-mail/username são armazenados com `casefold`; a senha não é aparada nem normalizada.

**Response `201`**
```json
{
  "id": "5d3e…",
  "email": "ana@exemplo.com",
  "username": "ana",
  "created_at": "2026-01-31T14:20:00Z"
}
```

**Erros:** `409 CONFLICT`, `422 VALIDATION_ERROR`, `429 RATE_LIMITED`.

### 3.2 `POST /auth/login`

**Request**
```json
{ "email": "ana@exemplo.com", "password": "S3nh@Forte!" }
```

**Response `200`**
```json
{
  "access_token": "eyJhbGciOi…",
  "refresh_token": "d8f7…",
  "token_type": "bearer",
  "expires_in": 900
}
```

> Nesta implementação, os dois tokens são entregues no corpo JSON e devem ficar somente em memória no cliente. A sessão não persiste após recarregar a página; consulte o ADR-0006.

**Erros:** `401 INVALID_CREDENTIALS`, `429 RATE_LIMITED`.

### 3.3 `POST /auth/refresh`

**Request**
```json
{ "refresh_token": "d8f7…" }
```

**Response `200`** — mesmo formato do login (novo par; o anterior é invalidado).
**Erros:** `401 UNAUTHORIZED` (inválido/expirado/reutilizado — reuso revoga a família).

### 3.4 `POST /auth/logout`

**Request:** `{ "refresh_token": "d8f7…" }` · **Response:** `204 No Content`.

Revoga apenas o refresh informado pertencente ao usuário autenticado. Refresh antigo já rotacionado é no-op; não revoga seu descendente. O access JWT continua válido até expirar, pois não há denylist de access tokens.

### 3.5 `GET /auth/me`

**Response `200`**
```json
{ "id": "5d3e…", "email": "ana@exemplo.com", "username": "ana", "created_at": "…" }
```

---

## 4. Música (`/music`)

| Método | Rota | Acesso | Descrição |
|---|---|:---:|---|
| GET | `/music/search` | 🔓 | Busca textual simples |
| GET | `/music/{id}` | 🔓 | Detalhe de uma música do catálogo |
| POST | `/music/discover` | 🔓➕ | Atalho de descoberta (alias de `/recommendations/music`) |

### 4.1 `GET /music/search`

**Query params:** `q` (obrigatório, ≥ 2), `limit` (1–50, padrão 20), `provider` (opcional).

**Response `200`**
```json
{ "items": [ { "…": "MusicItem" } ], "total": 12 }
```

### 4.2 `GET /music/{id}`

**Response `200`** → `MusicItem`. **Erros:** `404 NOT_FOUND`.

### 4.3 `POST /music/discover`

Comportamento idêntico a `POST /recommendations/music` (§6.1). Mantido para compatibilidade com o escopo.

---

## 5. Livros (`/books`)

| Método | Rota | Acesso | Descrição |
|---|---|:---:|---|
| GET | `/books/search` | 🔓 | Busca textual (também usada no seletor do RWM) |
| GET | `/books/{id}` | 🔓 | Detalhe |
| POST | `/books/discover` | 🔓➕ | Alias de `/recommendations/books` |

### 5.1 `GET /books/search`

**Query params:** `q` (≥ 2), `limit` (1–50, padrão 20), `provider` (opcional).
**Response `200`:** `{ "items": [ BookItem ], "total": n }`.

Quando o banco está configurado, os itens retornados também são inseridos ou atualizados no catálogo local. Sem banco, a busca externa continua disponível, mas seus resultados não ficam persistidos.
Com o banco migrado, as respostas de busca também são guardadas em `external_search_cache` pelo TTL configurado (padrão: 300 segundos), sobrevivendo a reinícios da API. Sem banco, o cache permanece em memória por processo. `BOOK_SEARCH_CACHE_TTL_SECONDS=0` desabilita o cache.
Na implementação Open Library, `description` é opcional e limitado a 2.000 caracteres; `subjects` contém até 12 assuntos de até 120 caracteres cada. O provider atual não classifica `genres`, portanto esse campo permanece vazio.

Busca externa usa `q` para alcançar títulos de edições traduzidas e `lang=pt` como preferência; descoberta usa também `language=por`. `title`/`cover_url` preferem a edição portuguesa informada, conservando ID e URL da obra. Lacuna específica de “Quem é você, Alasca?” é resolvida por alias para “Looking for Alaska” com autor John Green, conforme a [editora brasileira](https://www.intrinseca.com.br/upload/livros/1%C2%BACAP%20QuemEVoceAlasca.pdf); não gera registros fictícios. Sem edição/alias verificado, mantém o título da fonte. Cache externo versionado por idioma evita reutilização de resultados anteriores em inglês. Referência: [busca e edições Open Library](https://openlibrary.org/dev/docs/api/search).

### 5.2 `GET /books/{id}`

Busca o UUID no catálogo local; não faz uma consulta externa por identificador. **Response `200`** → `BookItem`. **Erros:** `404 NOT_FOUND` (ID ausente), `503 SERVICE_UNAVAILABLE` (banco ou catálogo não configurado).

---

## 6. Recomendações (`/recommendations`)

| Método | Rota | Acesso | Descrição |
|---|---|:---:|---|
| POST | `/recommendations/music` | 🔓➕ | Descoberta de músicas |
| POST | `/recommendations/books` | 🔓➕ | Descoberta de livros |
| POST | `/recommendations/read-with-music` | 🔓➕ | Músicas para um livro |
| POST | `/recommendations/auto` | 🔓➕ | Classifica a intenção e roteia (P1) |
| GET | `/recommendations/history` | 🔒 | Histórico paginado |
| GET | `/recommendations/{id}` | 🔒 | Detalhe de uma recomendação |
| DELETE | `/recommendations/{id}` | 🔒 | Remove do histórico (P2) |
| POST | `/recommendations/{id}/feedback` | 🔒 | Registra feedback |
| DELETE | `/recommendations/{id}/feedback` | 🔒 | Remove feedback |
| GET | `/recommendations/{id}/items/{item_id}/explanation` | 🔒 | "Por que isso foi recomendado?" |

### 6.1 `POST /recommendations/music`

**Renovação implementada em 2026-10-02** (prefixo `/api/v1`): aceita `excluded_music_ids` (lista de até 200 UUIDs, padrão `[]`) e `offset` (0–300, padrão 0), além de `query`, `filters` e `limit` existentes. Query/filtros/limite devem vir do snapshot do pedido enviado; edições ainda não submetidas não alteram o re-roll. Exclusões cumulativas são aplicadas antes da seleção IA e do fallback, junto às referências/exclusões do pedido. UUIDs externos vêm das fontes reais e permanecem estáveis; o catálogo pode reconciliar IDs legados por identidade do provedor. Sem nova migração nem histórico persistente.

```json
{
  "query": "Músicas instrumentais sem energia alta",
  "filters": {"vocals": "none", "excluded_energy": ["high"]},
  "limit": 10,
  "excluded_music_ids": ["00000000-0000-0000-0000-000000000001"],
  "offset": 15
}
```

**Continuação comum a MUSIC/BOOK:** resposta mantém `recommendation_id`, `parsed_query`, `items` e `meta`. `meta.has_more` é booleano; `meta.next_offset` é inteiro ou `null`. Uma próxima página externa avança 15, somente até 300; se `null`, o cliente conserva o offset da última requisição e exclui todos os IDs vistos. No modo local, offset não fatia o catálogo: apenas as exclusões fazem avançar e `next_offset` é sempre `null`. Aos 200 IDs excluídos, `has_more=false`/`next_offset=null`; o cliente deve parar sem descartar IDs antigos. Entradas inválidas (UUID/campo/limite/offset) retornam `422 VALIDATION_ERROR`.

`has_more=true` significa próxima página dentro do orçamento ou ao menos um resultado extra aceito depois de filtros, relevância e limite de dois itens por artista/autor. Avisos de falha, candidatos rejeitados e páginas além de 300 não contam. `false` encerra a amostra disponível, não garante exaustão de todo o catálogo. Busca online consulta uma página de 15 por termo (até dois termos), deduplica UUID e título/autoria, e classifica até 25 candidatos; a IA recebe até `limit+1` (máximo 25) na mesma chamada para verificar o item extra. Não varre páginas automaticamente nem amplia cotas. Metadados incompletos/seleção IA podem resultar em lista curta ou vazia mesmo com próxima página.

Falha IA/provedor conserva fallback por metadados ou catálogo editorial real, com `meta.degraded=true`, fontes reais em `meta.sources` e aviso em `meta.hint`. Ausência de candidatos compatíveis retorna `200 items:[]`; falha do cache compartilhado/banco configurado continua `503 SERVICE_UNAVAILABLE`, sem fallback de memória. Interface conserva lista durante espera/cancelamento/erro/esgotamento; erro degradado pode oferecer retry do mesmo pedido. Nenhuma resposta upstream, chave ou SQL é exposta. Groq mantém provider/modelo/chave/cota e cache de Intent/Selection por 24 horas; esse cache é distinto dos vistos efêmeros e da origem sem consulta/intenção. [ADR-0017](adr/0017-ephemeral-discovery-reroll.md).

**Contrato implementado em 2026-09-29** (prefixo `/api/v1`):

```json
{
  "query": "Músicas instrumentais sem energia alta",
  "filters": { "vocals": "none", "excluded_energy": ["high"] },
  "limit": 10
}
```

- `query`: 3–1000 caracteres; `limit`: 1–25, padrão 10. `references` e `exclude_ids` estruturados ainda não são aceitos.
- `filters.vocals`: `none`, `required`, `optional` ou `null`; `filters.energy`: `low`, `medium`, `high` ou `null`.
- `filters.excluded_energy`: lista de até três níveis (`low`, `medium`, `high`), padrão `[]`. Não pode conter o mesmo nível de `energy`.
- O texto reconhece voz/vocais/letras/instrumental e energia baixa/média/alta, incluindo exclusões simples. `não quero instrumental` pede voz; `sem energia alta` aceita baixa ou média, sem escolher arbitrariamente uma delas.
- Filtro explícito de voz prevalece sobre o texto. `energy` não nulo ou presença de `excluded_energy` substitui as restrições textuais de energia; `excluded_energy: []` limpa essas restrições. Cada dimensão é independente.
- Pedidos textuais contraditórios retornam `422 VALIDATION_ERROR` com orientação; um filtro explícito pode resolver a dimensão conflitante. A validação ocorre antes de chamadas externas.
- As restrições são reaplicadas no backend tanto à seleção da IA quanto ao fallback. Energia desconhecida não satisfaz exclusões. No modo online, classificações podem ser estimadas pela IA e são identificadas como tal; não são medições.
- `parsed_query` informa os filtros efetivamente usados. No modo local, `meta.ranking_version` é `local-rules-v7`; no online, energia sem valor único é `any`. Resultados têm UUID temporário, inclusive anônimos, e não constituem histórico persistente. Na leitura local em `CALM`, `scores.reading_mode` registra desempate por atmosfera ambiental (+1) e classificação cinematográfica (−1), subordinado ao score de contexto; explicações indicam esse critério. Em `CINEMATIC`, empates de contexto priorizam artistas menos repetidos e depois a etiqueta cinematográfica (`scores.reading_mode`: 1 com a etiqueta, 0 sem); mantém-se o limite de duas faixas por artista. Exclusões explícitas prevalecem sobre preferências de modo.
- Na descoberta local de livros, empates de contexto favorecem gêneros pedidos explicitamente antes do título. `parsed_query.preferred_genres` lista os gêneros reconhecidos e `scores.genre` informa a fração deles presente no resultado (0–1); os campos só aparecem quando há essa preferência. Gêneros apenas herdados de referências não ganham prioridade extra. É desempate, não filtro obrigatório, e não altera música, leitura ou ranking online experimental.
- `piano` e `detetive` são temas distintos reconhecidos pelo parser por regras. Detetive também integra os gêneros explícitos de livros; mistério continua uma categoria mais ampla. Sete músicas e O Cão dos Baskervilles têm as novas etiquetas, sustentadas em [fontes por obra](catalog-metadata.md). Piano indica uma obra/edição com esse instrumento, sem garantir piano solo nem a gravação aberta pelos links. Inclusão por múltiplos temas pode retornar correspondência parcial; exclusões prevalecem sobre temas herdados de referências. Metadados incompletos limitam a garantia das exclusões. Sem IA disponível, o caminho online traduz os termos para `piano`/`detective fiction` e classifica candidatos pelos metadados conhecidos, sem inferir instrumentação pelo artista.
- Referências por título usam palavras completas, ignorando caixa e acentos. Aliases de livros locais também são aceitos. `references` contém títulos positivos reconhecidos; `excluded_references` contém títulos negados. Ambas as listas removem a própria obra dos resultados; somente referências positivas acrescentam temas. A resolução online depende do catálogo local e dos candidatos recuperados, e referências inventadas pela IA não removem candidatos. Artistas/autores e inferências sobre obras ausentes do catálogo não fazem parte dessa resolução.
- O parser é limitado: não promete interpretação de comparativos, dupla negação ou todas as construções em português. Esta mudança cobre descoberta musical; os modos de leitura mantêm suas próprias regras.

**Contrato alvo do roadmap (exemplos abaixo ainda não implementados integralmente)**

**Request**
```json
{
  "query": "Quero músicas melancólicas e calmas para madrugada, parecidas com No Surprises.",
  "references": [
    { "song": "No Surprises", "artist": "Radiohead" }
  ],
  "filters": {
    "vocals": "optional",
    "energy": "low",
    "genres": []
  },
  "limit": 15,
  "exclude_ids": []
}
```

| Campo | Tipo | Obrig. | Descrição |
|---|---|:---:|---|
| `query` | string (3–1000) | ✓ | Pedido em linguagem natural |
| `references` | array | – | Referências explícitas (complementam o parse) |
| `filters` | objeto | – | Filtros opcionais; **sobrescrevem** o parse quando conflitam |
| `limit` | int (5–30) | – | Padrão 15 |
| `exclude_ids` | uuid[] | – | Itens a ignorar (ex.: "mostrar mais") |

**Response `200`**
```json
{
  "recommendation_id": "e1f2…",
  "persisted": true,
  "intent": "MUSIC_DISCOVERY",
  "parsed_query": { "…": "ParsedMusicIntent" },
  "items": [ { "…": "RankedItem<MusicItem>" } ],
  "meta": {
    "candidates_evaluated": 142,
    "providers_used": ["musicbrainz", "lastfm"],
    "degraded": false,
    "warnings": [],
    "timings_ms": { "parse": 620, "retrieval": 1450, "embedding": 380, "ranking": 45, "total": 2540 }
  }
}
```

- `persisted: false` para visitantes (RN-008); `recommendation_id` é `null` nesse caso.
- `meta.degraded: true` indica uso de fallback (ex.: parser determinístico) — o frontend pode informar discretamente.
- Lista vazia retorna `200` com `items: []` e `meta.hint`.

**Erros:** `422 VALIDATION_ERROR`, `422 UNPARSEABLE_QUERY`, `429`, `502/503/504`.

### 6.2 `POST /recommendations/books`

**Renovação implementada em 2026-10-01 e auditada em 2026-10-02** (prefixo `/api/v1`): mantém `query` e `limit` da descoberta; aceita `excluded_book_ids` (até 200 UUIDs já exibidos, padrão `[]`) e `offset` (0–300, padrão 0). Os IDs são excluídos antes da seleção por IA e também do fallback local/por regras. `meta.has_more` e `meta.next_offset` seguem o contrato comum da seção 6.1, inclusive limites/esgotamento: avisos e rejeições não indicam mais resultados. Filtros musicais em livros continuam retornando 422. A interface “Ver outros livros” substitui a lista para o mesmo pedido enviado, acumula exclusões enquanto a página está aberta e conserva a lista em espera/erro/cancelamento/esgotamento. Uma busca nova reinicia essas exclusões. Não é histórico persistente nem feedback.

```json
{
  "query": "Ficção científica sobre exploração espacial",
  "limit": 10,
  "excluded_book_ids": ["UUID de um livro já mostrado"],
  "offset": 15
}
```

Paginação por `offset/limit` segue o [contrato Open Library](https://openlibrary.org/dev/docs/api/search); cache inclui a página. Os exemplos seguintes descrevem o contrato alvo do roadmap.

**Request**
```json
{
  "query": "Quero uma fantasia medieval séria, com exploração, guerras e construção de mundo complexa.",
  "references": [
    { "title": "Duna", "author": "Frank Herbert" },
    { "title": "O Senhor dos Anéis", "author": "J. R. R. Tolkien" }
  ],
  "filters": { "language": "pt", "min_year": null, "max_year": null },
  "limit": 10,
  "exclude_ids": []
}
```

**Response `200`** — mesma estrutura de §6.1 com `items: RankedItem<BookItem>[]` e `parsed_query: ParsedBookIntent`.

> Livros já lidos, `DISLIKE`, `NOT_INTERESTED` e `ALREADY_KNOW` do usuário são **excluídos** (RN-003/004).

### 6.3 `POST /recommendations/read-with-music`

**Contrato implementado em 2026-10-01**: `book_id` UUID conhecido, `mode` (`FOCUS`, `IMMERSIVE`, `CINEMATIC`, `CALM`, `CUSTOM`), `context` até 500 caracteres (obrigatório em `CUSTOM`), `vocals` (`INSTRUMENTAL`, `MINIMAL`, `ANY`) e `target_duration_min` de 15 a 120, padrão 60. `limit`, `progression` e `book_ref` abaixo continuam sendo planejamento.

No modo online, a descrição musical precede o título do livro e define a atmosfera; assuntos literários não substituem o pedido musical. Recupera somente gravações MusicBrainz de lançamentos oficiais, com duração conhecida entre 90 segundos e 10 minutos; exclui spokenword, audiobook e dj-mix na consulta. Instrumental exige identificação pela fonte. Busca até três termos, com páginas de 50 candidatos e máximo de oito páginas por termo, 60 faixas e quatro por artista. Deduplica por ID e por título/artista. Groq interpreta uma vez e ordena uma amostra de até 25 candidatos uma vez; escolhas omitidas não descartam outros candidatos compatíveis. Indisponibilidade/cota da IA mantém a busca e ordenação por metadados. Não usa músicas locais ou durações estimadas para completar a sessão online. Paginação e durações seguem o [contrato MusicBrainz](https://musicbrainz.org/doc/MusicBrainz_API/Search).

`playlist` retorna `tracks_count`, `total_duration_ms`, `duration_estimated`, `target_duration_ms`, `target_met` e `shortfall_ms`. Sucesso online exige soma real maior ou igual à meta (`target_met=true`, `shortfall_ms=0`, `duration_estimated=false`); a última faixa inteira pode ultrapassá-la. Insuficiência da fonte/filtros/limites retorna `503 SOUNDTRACK_INCOMPLETE`, com contagem/minutos compatíveis e orientação de nova tentativa, sem uma playlist parcial apresentada como sucesso. Interface limpa o resultado anterior e exibe o erro. O modo local offline conserva seu catálogo limitado e estimativa sinalizada de cinco minutos por faixa.

Groq `429` com `Retry-After` numérico finito de até 30 segundos recebe uma espera e uma única nova tentativa; cada tentativa consome o limite local já configurado. Cabeçalho ausente/inválido ou espera maior retorna fallback imediatamente. Cota persistente não é repetida em cada lote da mesma trilha. Cache continua por 24 horas; nenhum limite/chave/modelo foi aumentado ou alterado. Referência: [limites Groq](https://console.groq.com/docs/rate-limits).

**Contrato alvo do roadmap abaixo (ainda não implementado integralmente)**

**Request**
```json
{
  "book_id": "9a12…",
  "mode": "CALM",
  "context": "Quero músicas para ler antes de dormir.",
  "vocals": "INSTRUMENTAL",
  "target_duration_min": 60,
  "limit": 20,
  "progression": null
}
```

| Campo | Tipo | Obrig. | Valores / Descrição |
|---|---|:---:|---|
| `book_id` | uuid | ✓* | ID do catálogo local |
| `book_ref` | `{provider, external_id}` | ✓* | Alternativa quando o livro ainda não está no catálogo (\*um dos dois) |
| `mode` | enum | ✓ | `FOCUS`, `IMMERSIVE`, `CINEMATIC`, `CALM`, `CUSTOM` |
| `context` | string (≤ 500) | – | Contexto livre; obrigatório se `mode = CUSTOM` |
| `vocals` | enum | – | `INSTRUMENTAL`, `MINIMAL`, `ANY` (padrão `ANY`; `FOCUS` força `INSTRUMENTAL`/`MINIMAL`) |
| `target_duration_min` | int (10–240) | – | Se informado, a lista é montada até atingir a duração |
| `limit` | int (5–50) | – | Usado se não houver duração-alvo |
| `progression` | objeto\|null | – | P2: `{ "start": "calm", "middle": "adventure", "end": "epic" }` |

**Response `200`**
```json
{
  "recommendation_id": "a7c9…",
  "persisted": true,
  "intent": "READ_WITH_MUSIC",
  "book": { "…": "BookItem" },
  "book_music_profile": {
    "moods": ["adventurous", "nostalgic", "epic"],
    "atmosphere": ["pastoral", "medieval", "mystical"],
    "genres": ["fantasy soundtrack", "folk", "orchestral"],
    "energy": "medium",
    "instrumentation": ["strings", "flute", "harp"]
  },
  "parsed_context": { "…": "ParsedMusicIntent" },
  "items": [ { "…": "RankedItem<MusicItem>" } ],
  "playlist": {
    "total_duration_ms": 3612000,
    "tracks_count": 17
  },
  "meta": { "…": "…" }
}
```

**Erros:** `404 NOT_FOUND` (livro), `422 VALIDATION_ERROR` (`CUSTOM` sem `context`), demais padrão.

### 6.4 `POST /recommendations/auto` (P1)

**Request:** `{ "query": "…" }` → sistema classifica a intenção e delega.
**Response:** mesma estrutura do endpoint delegado + `"routed_to": "music" | "books" | "read-with-music"`.
Se a intenção for ambígua: `200` com `"clarification": { "question": "…", "options": ["music","books"] }` e sem itens.

### 6.5 `GET /recommendations/history`

**Query params:** `type` (opcional: `MUSIC_DISCOVERY|BOOK_DISCOVERY|READ_WITH_MUSIC`), `limit`, `cursor`.
**Response `200`:** `{ "items": [ RecommendationSummary ], "next_cursor": "…", "has_more": true }`.

### 6.6 `GET /recommendations/{id}`

**Response `200`** — mesma estrutura das respostas de geração, com `user_feedback` atual em cada item.
**Erros:** `404` (também para recomendação de outro usuário, evitando enumeração).

### 6.7 `POST /recommendations/{id}/feedback`

**Request**
```json
{
  "entity_type": "MUSIC",
  "entity_id": "0b6c…",
  "interaction_type": "LIKE"
}
```

| `interaction_type` | Prioridade | Efeito |
|---|:---:|---|
| `LIKE` | P0 | + preferência; remove `DISLIKE` |
| `DISLIKE` | P0 | − preferência; remove `LIKE`; exclui de futuras |
| `SAVE` | P1 | Adiciona aos favoritos |
| `MORE_LIKE_THIS` | P1 | + forte; pode disparar nova busca |
| `LESS_LIKE_THIS` | P1 | − forte |
| `ALREADY_KNOW` | P1 | Rebaixa (música) / exclui (livro) |
| `NOT_INTERESTED` | P1 | Exclui de futuras |

**Response `200`**
```json
{
  "interaction": {
    "entity_type": "MUSIC",
    "entity_id": "0b6c…",
    "interaction_type": "LIKE",
    "created_at": "2026-01-31T14:25:00Z"
  },
  "profile_updated": true
}
```

**Validação:** `entity_id` deve pertencer aos itens da recomendação (`404` caso contrário).

### 6.8 `DELETE /recommendations/{id}/feedback`

**Query:** `entity_type`, `entity_id`, `interaction_type` → `204`.

### 6.9 `GET /recommendations/{id}/items/{item_id}/explanation`

**Response `200`**
```json
{
  "item_id": "77aa…",
  "text": "Esta música foi recomendada porque possui uma atmosfera melancólica e lenta, semelhante às músicas que você costuma curtir, além de ter baixa intensidade, característica presente na sua busca atual.",
  "factors": [
    { "factor": "semantic", "score": 0.91, "matched": ["melancholic", "calm"] },
    { "factor": "preference", "score": 0.74, "matched": ["atmospheric"] },
    { "factor": "context", "score": 0.80, "matched": ["studying"] }
  ],
  "generated_by": "llm",
  "cached": false
}
```

- `generated_by`: `"llm"` ou `"template"` (fallback).
- Geração sob demanda apenas (RN-007).

---

## 7. Playlists (`/playlists`)

**Implementado em 2026-10-01:** persistência básica na API, com prefixo `/api/v1`, autenticação Bearer e isolamento por conta. Integração na interface e edição de playlists ainda pendentes. [ADR-0014](adr/0014-owner-scoped-playlists.md).

| Método | Rota | Acesso | Descrição |
|---|---|:---:|---|
| POST | `/playlists` | 🔒 | Implementado: cria manualmente ou salva trilha de leitura |
| GET | `/playlists` | 🔒 | Implementado: lista paginada da conta |
| GET | `/playlists/{id}` | 🔒 | Implementado: detalhe com faixas em ordem |
| PATCH | `/playlists/{id}` | 🔒 | Futuro: renomear / reordenar |
| DELETE | `/playlists/{id}` | 🔒 | Implementado: exclui playlist e suas faixas |
| POST | `/playlists/{id}/tracks` | 🔒 | Futuro: adiciona faixa |
| DELETE | `/playlists/{id}/tracks/{music_id}` | 🔒 | Futuro: remove faixa |

### 7.1 `POST /playlists`

```json
{
  "name": "Terra Média — Noite",
  "description": "Para ler O Hobbit",
  "source_recommendation_id": "UUID retornado por /recommendations/read-with-music"
}
```

`name` é obrigatório (1–120 caracteres após trim); `description` é opcional/nula (até 1.000). Campos extras são rejeitados; a conta vem exclusivamente do Bearer, nunca do corpo.

- **Manual:** omitir `source_recommendation_id` e enviar `music_ids` (1–25 UUIDs únicos). Só aceita itens do catálogo local ou já persistidos em `music_catalog`; não consulta provedores externos.
- **Trilha:** enviar o UUID de um resultado público de `/recommendations/read-with-music` ainda válido no cache compartilhado (`0007_recommendation_results`, até uma hora/256 resultados no banco inteiro). Funciona entre instâncias/reinícios usando o mesmo banco; consultas não renovam TTL e evicção pode ocorrer antes. Omitir `music_ids` salva toda a trilha, com até 60 faixas; informar uma lista salva um subconjunto de até 60 IDs na ordem enviada. Todos os IDs devem pertencer à trilha. Resultados de descoberta de livros/músicas não são aceitos como origem nesta etapa; músicas de descoberta podem ser salvas pelo fluxo manual, limitado a 25 faixas.
- Não aceita lista vazia nem repetições. Resultado desconhecido/expirado retorna `404 NOT_FOUND`; origem incompatível, trilha vazia ou seleção fora da origem retorna `422 VALIDATION_ERROR`. Música manual desconhecida retorna `404 NOT_FOUND`. Nenhuma dessas falhas grava parcialmente a playlist.

**Response `201`** com `Location: /api/v1/playlists/{id}`:

```text
{
  id, name, description,
  source: "MANUAL" | "READ_WITH_MUSIC",
  source_recommendation_id: UUID | null,
  tracks: [{ position: 1, item: <metadados musicais salvos> }, ...],
  tracks_count, total_duration_ms, duration_estimated,
  created_at, updated_at
}
```

Metadados e ordem são copiados no salvamento e permanecem disponíveis após expirar a recomendação, atualizar o catálogo ou reiniciar a API. A duração soma `duration_ms` quando conhecida; caso contrário usa `estimated_duration_ms` ou cinco minutos e marca `duration_estimated=true`. A estimativa não preenche uma duração real ausente nos metadados.

### 7.2 Listagem, detalhe e exclusão

`GET /playlists?limit=20&offset=0` retorna `{items: [<resumo sem tracks>], total, limit, offset}`. Limite 1–50; offset 0–100.000. Ordem: `created_at DESC, id DESC`, com desempate estável. Total e itens sempre filtrados pela conta; o resumo inclui `tracks_count`, duração e origem.

`GET /playlists/{id}` retorna o mesmo detalhe da criação. `DELETE /playlists/{id}` retorna `204` sem corpo e preserva os itens do catálogo compartilhado. IDs ausentes ou pertencentes a outra conta retornam o mesmo `404 NOT_FOUND`, tanto na consulta quanto na exclusão; repetir a exclusão também retorna 404.

Todas as operações exigem uma conta ativa e JWT válido (`401` quando inválido/expirado). Banco não configurado ou tabelas de playlists indisponíveis retornam `503 SERVICE_UNAVAILABLE`. Cache de origem indisponível/desatualizado também retorna 503, sem criar playlist parcial. O cache guarda só identidade, itens e resumo da trilha, sem consulta/intenção/conta; expirados são purgados durante acessos/gravações. Sem banco, explicações públicas usam memória por processo, mas playlists continuam exigindo banco. [ADR-0015](adr/0015-shared-recommendation-cache.md). PostgreSQL tem SQL de migração validado, mas execução real e concorrência entre processos nesse banco seguem pendentes.

---

## 8. Preferências do Usuário (`/users/me`)

| Método | Rota | Acesso | Descrição |
|---|---|:---:|---|
| GET | `/users/me/preferences` | 🔒 | Lista preferências (`?source=EXPLICIT\|LEARNED`) |
| POST | `/users/me/preferences` | 🔒 | Cria preferência(s) explícita(s) |
| PATCH | `/users/me/preferences/{id}` | 🔒 | Atualiza valor/peso |
| DELETE | `/users/me/preferences/{id}` | 🔒 | Remove |
| POST | `/users/me/favorites` | 🔒 | Salva um item de resultado válido na conta |
| GET | `/users/me/favorites` | 🔒 | Snapshots privados paginados (`?type=MUSIC\|BOOK`) |
| POST | `/users/me/favorites/status` | 🔒 | Consulta em lote os itens salvos da conta |
| DELETE | `/users/me/favorites/{id}` | 🔒 | Remove favorito da conta; operação idempotente |
| DELETE | `/users/me/history` | 🔒 | Limpa histórico (P2) |
| DELETE | `/users/me` | 🔒 | Exclui conta e dados (P2) |

> O escopo lista `PATCH /users/me/preferences`; esta especificação usa `PATCH …/{id}` para atualização granular. Um `PATCH` em lote pode ser adicionado se necessário.

### 8.1 `POST /users/me/preferences`

**Request**
```json
{
  "preferences": [
    { "preference_type": "MUSIC_ARTIST", "value": "Radiohead", "weight": 0.9 },
    { "preference_type": "BOOK_GENRE", "value": "fantasy", "weight": 0.8 },
    { "preference_type": "BOOK_TITLE", "value": "Duna", "weight": 1.0 }
  ]
}
```

**Response `201`**
```json
{
  "items": [
    { "id": "…", "preference_type": "MUSIC_ARTIST", "value": "Radiohead", "weight": 0.9, "source": "EXPLICIT" }
  ]
}
```

**Regras:** valores normalizados (trim, lowercase para gêneros); `weight ∈ [-1, 1]` (negativo = aversão); duplicatas atualizam o peso (upsert).

### 8.2 `GET /users/me/preferences`

**Response `200`**
```json
{
  "explicit": [ { "…": "Preference" } ],
  "learned":  [ { "id": "…", "preference_type": "MUSIC_MOOD", "value": "melancholic", "weight": 0.62, "source": "LEARNED" } ]
}
```

---

### 8.3 Favoritos individuais — contrato implementado

Base `/api/v1/users/me/favorites`. Todas as operações exigem Bearer válido de uma conta ativa. Preferências/histórico e `SAVE` no endpoint de feedback continuam roadmap; salvar nesta coleção não gera feedback, não altera ranking e não cria playlist nem histórico de consultas.

**Criação:** `POST` aceita somente IDs UUID, com campos adicionais proibidos:

```json
{"recommendation_id":"00000000-0000-0000-0000-000000000001","item_id":"00000000-0000-0000-0000-000000000002"}
```

O servidor busca a origem no cache compartilhado (uma hora, até 256 resultados), verifica que o item pertence aos resultados efetivamente devolvidos e deriva o tipo pelos metadados do provedor: `artist` para `MUSIC`, `authors` para `BOOK`. Copia somente o objeto `item`, sem score, explicação, consulta, intenção ou contexto. A origem é pública/temporária; o favorito criado pertence exclusivamente à conta autenticada.

Retorna `201` quando criado e `200` quando já salvo pela mesma conta/tipo/item. Corpo em ambos os casos:

```json
{
  "id":"00000000-0000-0000-0000-000000000003",
  "type":"MUSIC",
  "item_id":"00000000-0000-0000-0000-000000000002",
  "item":{"id":"00000000-0000-0000-0000-000000000002","title":"Título da fonte","artist":"Artista da fonte"},
  "created_at":"2026-10-01T12:00:00Z"
}
```

O exemplo abrevia o snapshot; todos os metadados originais do item são preservados, inclusive links/capas e duração real/estimada quando presentes. Deduplicação transacional por `(user_id, type, item_id)` conserva ID, snapshot, proveniência e data da primeira gravação; metadados novos não substituem os salvos. Mesmo uma repetição precisa de origem válida: expirada/removida/desconhecida ou item fora dela retorna `404 NOT_FOUND`. O favorito já salvo permanece acessível depois de expiração/evicção, alteração do catálogo ou reinício; remover e salvar novamente cria um novo snapshot.

**Listagem:** `GET ?type=MUSIC&limit=20&offset=0` retorna `{items: [<objeto acima>], total, limit, offset}`. Filtro `type` opcional (`MUSIC`/`BOOK`); limite 1–50 (padrão 20), offset 0–100.000 (padrão 0). Total e itens filtrados pela conta/tipo. Ordem `created_at DESC, id DESC`; paginação por offset pode mudar diante de novas gravações/exclusões.

**Estado em lote:** `POST /status` aceita somente `{type: "MUSIC"|"BOOK", item_ids: UUID[]}` com 1–60 IDs únicos. Retorna `200` com `{favorites: {"<item_id>": "<favorite_id>"}}`; omite IDs não salvos ou de outra conta/tipo. Não lê o cache de recomendações, não salva itens e permite atualizar botões sem carregar toda a coleção ou fazer uma chamada por item.

**Exclusão:** `DELETE /{favorite_id}` retorna sempre `204` sem corpo para uma requisição válida/autenticada, inclusive ID ausente, já excluído ou pertencente a outra conta. A escrita é filtrada por proprietário; não revela existência nem remove dados de terceiros. Catálogo, cache, playlists e favoritos de outras contas são preservados.

**Erros:** envelope comum `error.code/message/request_id`; `401 UNAUTHORIZED` para sessão ausente/inválida/expirada, `422 VALIDATION_ERROR` para UUID/campos/tipo/limites inválidos e `503 SERVICE_UNAVAILABLE` para banco não configurado/indisponível/schema desatualizado. Cache de origem indisponível impede a criação com 503, sem escrita parcial; listagem/status/exclusão são independentes do cache. Aplicar `0008_favorites` antes de iniciar (`local.py` migra automaticamente). [ADR-0016](adr/0016-owner-scoped-favorites.md). PostgreSQL real permanece pendente; não inferir validação desse banco a partir do suporte SQL.

## 9. Saúde e Metadados

| Método | Rota | Acesso | Descrição |
|---|---|:---:|---|
| GET | `/health` | 🔓 | Liveness (`{"status":"ok"}`) |
| GET | `/health/ready` | 🔓 | Readiness: DB, pgvector, providers (status agregado) |
| GET | `/version` | 🔓 | Versão do app e do ranking |

`/health/ready` **não** expõe detalhes sensíveis; retorna `200`/`503` e status por componente (`ok`/`degraded`/`down`).

---

## 10. Ciclo de Vida do Token

| Token | Validade | Armazenamento (cliente) | Observação |
|---|---|---|---|
| Access | 15 min | Memória | Enviado em `Authorization` |
| Refresh | 7 dias | Cookie `HttpOnly; Secure; SameSite` **ou** memória (ver ADR-0006) | Rotativo; reuso revoga a família |

Claims mínimos do access token: `sub`, `iat`, `exp`, `jti`, `type=access`.

---

## 11. CORS

- Origens permitidas: lista explícita via variável de ambiente (`CORS_ORIGINS`).
- Métodos: `GET, POST, PATCH, DELETE, OPTIONS`.
- Headers: `Authorization, Content-Type, X-Request-ID`.
- Credenciais habilitadas apenas se refresh via cookie.

---

## 12. Versionamento e Compatibilidade

- Versão na URL (`/api/v1`).
- Mudanças **aditivas** (novos campos opcionais) não incrementam versão.
- Mudanças quebrando contrato → `/api/v2`, com período de depreciação (`Deprecation` e `Sunset` headers).
- Os campos `scores` e `meta` são considerados **não estáveis** (podem evoluir sem aviso).

---

## 13. Mapa Rápido de Endpoints

| # | Método | Rota | Acesso | Prioridade |
|--:|---|---|:---:|:---:|
| 1 | POST | `/auth/register` | 🔓 | P0 |
| 2 | POST | `/auth/login` | 🔓 | P0 |
| 3 | POST | `/auth/refresh` | 🔓 | P0 |
| 4 | POST | `/auth/logout` | 🔒 | P0 |
| 5 | GET | `/auth/me` | 🔒 | P0 |
| 6 | GET | `/music/search` | 🔓 | P1 |
| 7 | GET | `/music/{id}` | 🔓 | P1 |
| 8 | POST | `/music/discover` | 🔓➕ | P0 |
| 9 | GET | `/books/search` | 🔓 | P0 |
| 10 | GET | `/books/{id}` | 🔓 | P1 |
| 11 | POST | `/books/discover` | 🔓➕ | P0 |
| 12 | POST | `/recommendations/music` | 🔓➕ | P0 |
| 13 | POST | `/recommendations/books` | 🔓➕ | P0 |
| 14 | POST | `/recommendations/read-with-music` | 🔓➕ | P0 |
| 15 | POST | `/recommendations/auto` | 🔓➕ | P1 |
| 16 | GET | `/recommendations/history` | 🔒 | P0 |
| 17 | GET | `/recommendations/{id}` | 🔒 | P0 |
| 18 | POST | `/recommendations/{id}/feedback` | 🔒 | P0 |
| 19 | DELETE | `/recommendations/{id}/feedback` | 🔒 | P1 |
| 20 | GET | `/recommendations/{id}/items/{item_id}/explanation` | 🔒 | P1 |
| 21 | GET/POST/PATCH/DELETE | `/users/me/preferences[/{id}]` | 🔒 | P0 |
| 22 | GET | `/users/me/favorites` | 🔒 | P1 |
| 23 | * | `/playlists[...]` | 🔒 | P2 |
| 24 | GET | `/health`, `/health/ready`, `/version` | 🔓 | P0 |

---

## 14. Exemplo de Fluxo Completo (cURL)

```bash
# 1. Registro e login
curl -X POST $API/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"ana@exemplo.com","username":"ana","password":"S3nh@Forte!"}'

TOKEN=$(curl -s -X POST $API/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"ana@exemplo.com","password":"S3nh@Forte!"}' | jq -r .access_token)

# 2. Descobrir músicas
curl -X POST $API/recommendations/music \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"query":"Algo melancólico e calmo para madrugada, parecido com No Surprises"}'

# 3. Dar feedback
curl -X POST $API/recommendations/$REC_ID/feedback \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"entity_type":"MUSIC","entity_id":"'$MUSIC_ID'","interaction_type":"LIKE"}'

# 4. Read With Music
curl -X POST $API/recommendations/read-with-music \
  -H "Authorization: Bearer $TOKEN" -H 'Content-Type: application/json' \
  -d '{"book_id":"'$BOOK_ID'","mode":"CALM","context":"antes de dormir","vocals":"INSTRUMENTAL","target_duration_min":60}'
```

---

## 15. Decisões em Aberto

| # | Questão | Destino |
|---|---|---|
| Q1 | Refresh token em cookie `HttpOnly` vs. corpo da resposta | ADR-0006 |
| Q2 | Streaming (SSE) para retornar resultados progressivamente | Pós-MVP |
| Q3 | Endpoint `PATCH /users/me/preferences` em lote | Avaliar na Fase 8 |
| Q4 | Expor `scores` publicamente ou apenas em modo debug | Fase 9 (UX) |
