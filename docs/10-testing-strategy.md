# Testing Strategy

> **Implementação em 2026-10-01:** a [CI inicial](CI.md) está configurada em `.github/workflows/ci.yml` com Ruff, pytest/SQLite, gate de ranking local v7 em K=5/10 e build/E2E dos fluxos públicos. Validação local aprovada; execução hospedada ainda pendente. As ferramentas, suítes PostgreSQL e avaliações reais descritas abaixo incluem trabalho futuro; não considerar esses itens entregues pela CI inicial.

> **Documento:** 10 de 15 — Documentação Técnica
> **Projeto:** Plataforma Inteligente de Descoberta de Músicas e Livros
> **Status:** Rascunho v1.0
> **Relacionados:** Recommendation Engine Specification (07), Security Specification (09), Development Roadmap (12)

---

## 1. Objetivo

Definir **como**, **onde** e **com que critérios** o projeto será testado, garantindo que:

1. A qualidade das recomendações (prioridade nº 1 do projeto) seja **mensurável e regressível**, não apenas "parecer boa".
2. Componentes determinísticos (ranking, filtros, similaridade, autenticação) tenham cobertura alta e confiável.
3. Componentes não determinísticos (LLM, embeddings, APIs externas) sejam isolados de forma que a suíte de testes seja **rápida, gratuita e reproduzível**.
4. Os 12 critérios de sucesso do MVP (seção 77 do escopo) tenham cobertura de ponta a ponta.

---

## 2. Princípios

| Princípio | Aplicação prática |
|---|---|
| **Determinismo primeiro** | O backend decide o ranking; portanto, o núcleo do sistema deve ser 100% testável sem rede e sem LLM. |
| **Isolar o não determinístico** | LLM, embeddings e APIs externas são acessados por interfaces (`LLMClient`, `EmbeddingService`, `MusicProvider`, `BookProvider`) e substituídos por *fakes* nos testes. |
| **Nunca chamar serviços pagos/externos na CI** | Testes da suíte padrão não usam rede. Chamadas reais existem apenas em suítes opt-in (`live`, `ai_eval`). |
| **Teste o comportamento, não a implementação** | Testes validam entradas/saídas e contratos, evitando acoplamento com detalhes internos. |
| **Qualidade de recomendação é testável** | Um *golden set* de consultas e métricas offline (Precision@K, nDCG, diversidade) detecta regressões de qualidade. |
| **Falhas são cenários de primeira classe** | Timeout, resposta inválida do LLM, API indisponível e rate limit possuem testes explícitos (seção 61 do escopo). |
| **Testes rápidos rodam sempre** | Unitários < 1 min no total; integração < 5 min; E2E apenas em PRs para `main` e pré-deploy. |

---

## 3. Pirâmide de Testes

```
                    ▲
                   ╱ ╲        E2E (Playwright)         ~5%
                  ╱───╲       Fluxos críticos do MVP
                 ╱     ╲
                ╱───────╲     Integração                ~25%
               ╱         ╲    API + DB + pipeline (com fakes de IA/providers)
              ╱───────────╲
             ╱             ╲  Unitários                 ~70%
            ╱───────────────╲ Ranking, filtros, similaridade, parser, services
           ╱─────────────────╲
```

Em paralelo à pirâmide, existem duas suítes **fora do caminho crítico da CI**:

- **`ai_eval`** — avaliação de qualidade das recomendações e do parser com dados reais (manual/agendada).
- **`live`** — testes de contrato contra APIs externas reais (manual/agendada).

| Tipo | Escopo | Ferramentas | Roda em |
|---|---|---|---|
| Unitário | Funções/classes puras, sem I/O | `pytest`, `hypothesis` | Todo commit / PR |
| Integração | API + banco real (Postgres + pgvector) + fakes de IA/providers | `pytest`, `httpx.AsyncClient`, Docker/Testcontainers | Todo PR |
| Contrato de provider | Normalização das respostas de APIs externas usando fixtures gravadas | `respx` ou `pytest-recording` (VCR) | Todo PR |
| E2E | Frontend + backend + banco, com IA/providers fake | Playwright | PR para `main` / pré-deploy |
| `ai_eval` | Qualidade do parser e do ranking com LLM/embeddings reais | Script próprio + `pytest -m ai_eval` | Manual / semanal |
| `live` | Sanidade das APIs externas reais | `pytest -m live` | Manual / semanal |
| Segurança | Autenticação, autorização, validação | `pytest`, `bandit`, `pip-audit`, `npm audit` | Todo PR |
| Performance | Latência do pipeline e queries vetoriais | `pytest-benchmark`, `locust` (opcional) | Antes do deploy / Fase 10 |

---

## 4. Ferramentas

### Backend

| Ferramenta | Uso |
|---|---|
| `pytest` | Runner principal |
| `pytest-asyncio` | Testes de código assíncrono |
| `pytest-cov` | Cobertura |
| `httpx` (`AsyncClient`) | Chamadas à API FastAPI nos testes de integração |
| `respx` | Mock de chamadas HTTP feitas por `httpx` (providers externos) |
| `factory-boy` (ou factories próprias) | Criação de dados de teste |
| `hypothesis` | Testes baseados em propriedades (ranking, similaridade) |
| `freezegun` / `time-machine` | Controle de tempo (expiração de JWT, TTL de cache) |
| `testcontainers-python` ou Docker Compose | Postgres com pgvector em testes de integração |
| `ruff`, `mypy` | Lint e tipagem estática (pré-requisito para os testes na CI) |
| `bandit`, `pip-audit` | Análise estática de segurança e dependências |

### Frontend

| Ferramenta | Uso |
|---|---|
| `Vitest` | Runner de testes unitários |
| `React Testing Library` | Testes de componentes centrados no usuário |
| `MSW` (Mock Service Worker) | Mock da API nos testes de componentes |
| `Playwright` | E2E |
| `ESLint`, `Prettier`, `tsc --noEmit` | Lint, formatação e tipagem |

---

## 5. Estrutura de Diretórios

```text
backend/
└── tests/
    ├── conftest.py                  # fixtures globais (db, client, fakes)
    ├── factories/                   # factories de User, Music, Book, Interaction...
    ├── fakes/
    │   ├── fake_llm_client.py
    │   ├── fake_embedding_service.py
    │   ├── fake_music_provider.py
    │   └── fake_book_provider.py
    ├── fixtures/
    │   ├── providers/               # respostas gravadas de APIs externas (JSON)
    │   └── llm/                     # respostas estruturadas de exemplo
    ├── unit/
    │   ├── ai/
    │   │   ├── test_intent_parser.py
    │   │   └── test_recommendation_explainer.py
    │   ├── recommendation/
    │   │   ├── test_ranking.py
    │   │   ├── test_similarity.py
    │   │   ├── test_filters.py
    │   │   └── test_user_profile.py
    │   ├── core/
    │   │   └── test_security.py
    │   └── services/
    ├── integration/
    │   ├── api/
    │   │   ├── test_auth_endpoints.py
    │   │   ├── test_music_endpoints.py
    │   │   ├── test_books_endpoints.py
    │   │   ├── test_recommendations_endpoints.py
    │   │   ├── test_feedback_endpoints.py
    │   │   └── test_preferences_endpoints.py
    │   ├── pipeline/
    │   │   └── test_recommendation_pipeline.py
    │   ├── providers/
    │   │   └── test_provider_contracts.py
    │   └── db/
    │       └── test_vector_search.py
    ├── ai_eval/
    │   ├── golden_sets/
    │   │   ├── music_queries.yaml
    │   │   ├── book_queries.yaml
    │   │   └── read_with_music_queries.yaml
    │   ├── test_intent_parser_eval.py
    │   └── test_recommendation_quality_eval.py
    └── live/
        └── test_live_providers.py

frontend/
├── src/**/*.test.tsx                # testes de componentes ao lado do código
└── e2e/
    └── *.spec.ts                    # Playwright
```

---

## 6. Áreas Prioritárias de Teste

Baseado na seção 58 do escopo. A ordem abaixo reflete a prioridade.

### 6.1. Recommendation — Ranking (`ranking.py`)

O ranking é o coração do produto e deve ter a maior cobertura (**≥ 90%**).

**Fórmula alvo:**

```
score = semantic_similarity * w_sem
      + user_preference_similarity * w_pref
      + reference_similarity * w_ref
      + context_match * w_ctx
      + popularity_factor * w_pop
      - disliked_characteristics_penalty
```

**Casos de teste obrigatórios:**

| # | Cenário | Resultado esperado |
|---|---|---|
| R1 | Candidatos com apenas `semantic_similarity` diferente | Ordem decrescente pela similaridade |
| R2 | Dois candidatos idênticos, um com penalidade de "dislike" | O penalizado fica abaixo |
| R3 | Pesos alterados via configuração | Ordem muda de forma coerente com os pesos |
| R4 | Todos os pesos zerados exceto um | Ranking depende só daquele fator |
| R5 | Empate de score | Desempate determinístico e estável (ex.: por `id`) |
| R6 | Lista vazia de candidatos | Retorna lista vazia, sem exceção |
| R7 | Usuário sem perfil (anônimo) | `user_preference_similarity` ignorado/neutro, sem quebrar |
| R8 | Diversidade: mesmo artista repetido N vezes | Reordenação/limite respeita a regra de diversidade (seção 66) |
| R9 | Item "Already know"/"Dislike" | Excluído ou fortemente penalizado conforme regra definida |
| R10 | Score final | Sempre dentro do intervalo/normalização definido na spec |

**Testes baseados em propriedades (`hypothesis`):**

- Aumentar `semantic_similarity` de um candidato **nunca** reduz sua posição (*monotonicidade*).
- Aumentar a penalidade **nunca** melhora a posição.
- O ranking é **idempotente**: rodar duas vezes com a mesma entrada gera a mesma saída.
- A saída é uma **permutação** da entrada (nenhum candidato criado ou perdido, exceto os filtrados).

### 6.2. Recommendation — Filtros (`filters.py`)

| Cenário | Esperado |
|---|---|
| Remover itens rejeitados pelo usuário | Nenhum item com `DISLIKE`/`NOT_INTERESTED` aparece |
| Remover itens marcados como `ALREADY_KNOW` | Excluídos quando a busca pedir descoberta |
| `vocals = instrumental` | Faixas com vocais são descartadas |
| Duração alvo de playlist | Conjunto respeita a duração aproximada (± tolerância) |
| Filtros combinados | Aplicação em qualquer ordem gera o mesmo conjunto |
| Filtro sem candidatos restantes | Retorna vazio e o pipeline aciona fallback (relaxar filtros) |

### 6.3. Recommendation — Similaridade (`similarity.py`)

- Similaridade de cosseno entre vetores idênticos = 1; ortogonais = 0; opostos = -1 (ou valor normalizado documentado).
- Vetor nulo (norma zero) → tratado sem `ZeroDivisionError`.
- Dimensões incompatíveis → erro explícito e tipado.
- Simetria: `sim(a, b) == sim(b, a)`.
- Consistência entre a similaridade calculada em Python e a distância retornada pelo pgvector (teste de integração, tolerância numérica).

### 6.4. AI — Intent Parser (`intent_parser.py`)

O parser transforma linguagem natural em JSON estruturado (seção 28). O LLM é **sempre mockado** nos testes unitários.

**O que testar:**

1. **Contrato de saída:** a resposta do LLM é validada por um schema Pydantic; campos obrigatórios, enums e defaults.
2. **Resiliência a respostas ruins** (cenários de erro):
   - JSON inválido → retry (limitado) e depois erro tratado.
   - Campo desconhecido → ignorado ou rejeitado conforme política.
   - Valor fora do enum (`energy: "super-high"`) → falha de validação, sem propagar dado inválido.
   - Timeout do LLM → exceção de domínio (`LLMUnavailableError`) e fallback previsto.
3. **Classificação de intenção** (`music_discovery`, `book_discovery`, `read_with_music`) a partir de respostas fake.
4. **Prompt construction:** o prompt enviado contém a consulta do usuário e o schema esperado (teste de snapshot do prompt).
5. **Sanitização:** entradas muito longas, vazias ou com tentativa de *prompt injection* não quebram o pipeline e não vazam instruções internas.

**Avaliação real (`ai_eval`):** as consultas do *golden set* rodam contra o LLM real e comparam campos-chave (intent, mood, energy, referências). Ver seção 8.

### 6.5. AI — Explainer (`recommendation_explainer.py`)

- Só é acionado sob demanda (seção 21).
- O prompt inclui **apenas** os fatores do ranking (scores e características), nunca dados sensíveis do usuário.
- Falha do LLM devolve uma explicação **de fallback baseada em template** a partir dos fatores do ranking.

### 6.6. Autenticação e Segurança (`security.py`, `auth_service.py`)

| Cenário | Esperado |
|---|---|
| Registro com e-mail novo | 201, senha armazenada como hash (nunca em texto puro) |
| Registro com e-mail duplicado | 409 |
| Senha fraca / e-mail inválido | 422 |
| Login correto | Access token + refresh token |
| Login incorreto | 401, mensagem genérica (sem revelar se o e-mail existe) |
| Access token expirado | 401 (usar `freezegun`) |
| Refresh com token válido | Novo access token |
| Refresh com token inválido/expirado/revogado | 401 |
| Token adulterado (assinatura inválida) | 401 |
| Endpoint protegido sem token | 401 |
| Usuário A acessa recurso do usuário B | 403/404 (teste de autorização por dono) |
| Hash de senha | Verificação correta; *salt* diferente para a mesma senha |
| Rate limiting em `/auth/login` | 429 após exceder o limite |

### 6.7. Endpoints Principais (integração)

Cada endpoint da seção 46 do escopo deve ter, no mínimo:

1. **Caminho feliz** (status e corpo conforme schema).
2. **Validação de entrada** (422 com payload inválido).
3. **Autenticação/autorização** (quando aplicável).
4. **Erro esperado de domínio** (ex.: item não encontrado → 404).

Cobertura por grupo:

| Grupo | Endpoints | Observações |
|---|---|---|
| Auth | `register`, `login`, `refresh`, `me` | Ver 6.6 |
| Music | `search`, `{id}`, `discover` | `discover` funciona sem login (modo anônimo, seção 26) |
| Books | `search`, `{id}`, `discover` | Idem |
| Recommendations | `music`, `books`, `read-with-music`, `history`, `{id}` | Histórico exige autenticação |
| Feedback | `POST /recommendations/{id}/feedback` | Todos os tipos de interação; idempotência; item inexistente |
| Playlists | CRUD | Dono da playlist; `DELETE` de playlist alheia falha |
| Preferences | `GET/POST/PATCH` | Validação de `weight` e `preference_type` |

### 6.8. Services

Testes unitários com repositórios e providers substituídos por fakes/mocks, validando regras de negócio isoladamente (ex.: `recommendation_service` persiste `Recommendation` e `RecommendationItem`, registra `SearchHistory`, aplica feedback ao perfil).

### 6.9. Recommendation Pipeline

**Integração** com banco real e fakes de IA/providers. É o teste mais importante do fluxo (seção 19):

```
User Query → Intent Parsing → Candidate Retrieval → Filtering
          → Semantic Similarity → User Preference Matching → Ranking → Result
```

| Cenário | Esperado |
|---|---|
| Consulta de música (caminho feliz) | Lista ranqueada de músicas **reais** (existentes no provider/DB fake) |
| Consulta de livro (caminho feliz) | Idem para livros |
| Read With Music — cada modo (`focus`, `immersive`, `cinematic`, `calm`, `custom`) | Pesos/filtros diferentes produzem resultados diferentes e coerentes |
| Usuário com histórico de dislikes | Itens rejeitados não aparecem |
| Usuário anônimo | Pipeline funciona sem componentes de personalização |
| Provider principal indisponível | Fallback para cache/DB local ou erro tratado com mensagem clara |
| LLM indisponível | Fallback definido (ex.: busca por palavras-chave) ou erro tratado |
| Zero candidatos | Resposta vazia amigável; nenhuma exceção não tratada |
| **Anti-hallucination** | Todo item retornado tem `external_id` presente no provider/DB — **nunca** vem do LLM (seção 29) |
| Limite de candidatos enviados ao LLM | Nunca envia listas grandes de candidatos ao LLM (seção 64) |
| Observabilidade | Logs registram tempo, provider usado e nº de candidatos, **sem dados sensíveis** |

### 6.10. Providers Externos

- **Testes de contrato com fixtures gravadas:** garantem que a normalização (`MusicProvider`/`BookProvider` → modelo interno) funciona com respostas reais salvas em `tests/fixtures/providers/`.
- Cenários: resposta completa, campos ausentes/nulos, resposta vazia, HTTP 429, HTTP 5xx, timeout, JSON malformado.
- **Cache:** segunda busca idêntica não gera nova requisição HTTP (contador do `respx`); TTL expirado gera nova requisição.
- **Provider Pattern:** um teste garante que qualquer implementação passa pela mesma suíte de contrato (teste parametrizado sobre `[FakeProvider, OpenLibraryProvider, GoogleBooksProvider, ...]`).
- **Suíte `live`:** verifica periodicamente se o formato real das APIs não mudou.

### 6.11. Personalização e Aprendizado

| Cenário | Esperado |
|---|---|
| `LIKE` em item | Pesos do perfil aumentam nas características do item |
| `DISLIKE` | Pesos diminuem/penalidade registrada |
| `MORE_LIKE_THIS` / `LESS_LIKE_THIS` | Efeito mais forte que like/dislike (conforme spec) |
| `ALREADY_KNOW` | Item não é recomendado novamente, sem penalizar as características |
| Sequência de feedbacks | Perfil converge de forma previsível (teste com sequência determinística) |
| Recomendação posterior | Ranking muda em relação à linha de base sem feedback (critério 10 do MVP) |
| Atualização do perfil vetorial | Vetor permanece normalizado e com dimensão correta |

### 6.12. Banco de Dados e Busca Vetorial

- Migrações: `alembic upgrade head` seguido de `alembic downgrade base` executam sem erro em um banco limpo.
- A extensão `vector` é criada pela migração.
- Busca por similaridade retorna vizinhos na ordem correta (fixtures com vetores conhecidos).
- Restrições de integridade: chave única de e-mail, FKs, `ON DELETE` (exclusão de conta remove dados do usuário — seção 63).

---

## 7. Estratégia para Componentes de IA e Não Determinísticos

### 7.1. Fakes e dublês

| Interface | Fake | Comportamento |
|---|---|---|
| `LLMClient` | `FakeLLMClient` | Retorna respostas pré-definidas por chave/consulta; pode simular timeout, JSON inválido, erro 5xx |
| `EmbeddingService` | `FakeEmbeddingService` | Embeddings **determinísticos** (ex.: hash da string → vetor de baixa dimensão) ou vetores manuais para cenários controlados |
| `MusicProvider` / `BookProvider` | `FakeMusicProvider` / `FakeBookProvider` | Catálogo pequeno em memória, com características conhecidas |

**Regra:** dados de teste devem ser pequenos e **construídos para provar um comportamento** (ex.: 5 músicas onde apenas uma é melancólica e instrumental).

### 7.2. Fixtures gravadas (record/replay)

- Respostas reais de LLM e APIs externas são gravadas **uma vez** (sem dados sensíveis/chaves) e reutilizadas.
- Regravação é manual e revisada em PR.

### 7.3. Testes de contrato do LLM

Além de mocks, existe um teste `ai_eval` que valida que o **LLM real** respeita o schema estruturado em uma amostra de consultas (taxa de conformidade esperada ≥ 95%). Isso detecta regressões quando o modelo ou o prompt mudam.

### 7.4. O que **não** testar de forma exata

Não escreva asserts de igualdade sobre texto livre gerado pelo LLM (explicações). Valide propriedades: não vazio, tamanho máximo, menciona pelo menos um fator do ranking, sem vazar dados sensíveis.

---

## 8. Avaliação Offline da Qualidade das Recomendações

Como a **qualidade das recomendações é a prioridade nº 1**, ela precisa de métricas próprias, executadas fora da CI padrão.

### 8.1. Golden set

Arquivo YAML versionado com consultas representativas e resultados esperados (ou aceitáveis).

```yaml
# tests/ai_eval/golden_sets/music_queries.yaml
- id: music-001
  query: "Quero músicas melancólicas e calmas para ouvir de madrugada, parecidas com No Surprises."
  expected_intent:
    intent: music_discovery
    mood_contains: [melancholic, calm]
    energy: low
    references:
      - { song: "No Surprises", artist: "Radiohead" }
  relevant_items:          # itens que consideramos bons resultados
    - { title: "Fake Plastic Trees", artist: "Radiohead" }
    - { title: "Motion Picture Soundtrack", artist: "Radiohead" }
  must_not_include_artists: []

- id: rwm-001
  query: "Estou lendo O Senhor dos Anéis e quero músicas instrumentais, medievais e calmas."
  expected_intent:
    intent: read_with_music
    book: "O Senhor dos Anéis"
    vocals: instrumental
    energy: low
  constraints:
    max_vocal_tracks: 0
```

**Tamanho inicial recomendado:** 15–20 consultas por módulo (música, livro, Read With Music), crescendo com o tempo.

### 8.2. Métricas

| Métrica | O que mede | Meta inicial (ajustável) |
|---|---|---|
| **Intent accuracy** | % de consultas com intenção classificada corretamente | ≥ 95% |
| **Schema conformity** | % de respostas do LLM válidas no primeiro try | ≥ 95% |
| **Precision@K** (K=5,10) | Fração dos top-K que está no conjunto relevante | Definir baseline e **não regredir** |
| **nDCG@K** | Qualidade da ordenação | Definir baseline e **não regredir** |
| **Constraint satisfaction** | % de resultados que respeitam restrições explícitas (ex.: instrumental) | ≥ 95% |
| **Artist diversity** | Nº médio de artistas distintos no top-10 | ≥ 7 de 10 |
| **Existence rate** | % de itens que existem de fato nas fontes | **100%** |
| **Latência p95 do pipeline** | Tempo total | Definir na Fase 10 |

### 8.3. Uso

1. Registrar o **baseline** ao concluir a Fase 4.
2. Toda mudança em prompts, pesos, embeddings ou filtros roda a suíte e compara com o baseline.
3. Regressões significativas bloqueiam a alteração (portão de qualidade).
4. Resultados são salvos em `docs/eval-reports/` para histórico e para citar no README/portfólio.

---

## 9. Banco de Dados nos Testes

- **Integração usa Postgres real com pgvector** (não SQLite): comportamento de tipos vetoriais e índices precisa ser fiel.
- Estratégia de isolamento: cada teste roda em **transação com rollback** ou em *schema* isolado; o banco é criado uma vez por sessão de testes.
- Migrações são aplicadas via Alembic no *setup* (garante que as migrações funcionam).
- Imagem sugerida: `pgvector/pgvector:pg16` (mesma usada em desenvolvimento e CI).

```python
# tests/conftest.py (ilustrativo)
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.ai.llm_client import get_llm_client
from app.ai.embedding_service import get_embedding_service
from tests.fakes.fake_llm_client import FakeLLMClient
from tests.fakes.fake_embedding_service import FakeEmbeddingService


@pytest.fixture
def fake_llm() -> FakeLLMClient:
    return FakeLLMClient()


@pytest.fixture
async def client(db_session, fake_llm):
    app.dependency_overrides[get_llm_client] = lambda: fake_llm
    app.dependency_overrides[get_embedding_service] = lambda: FakeEmbeddingService(dim=8)
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        yield ac
    app.dependency_overrides.clear()
```

---

## 10. Testes de Frontend

| Nível | Foco | Exemplos |
|---|---|---|
| **Componentes** | Renderização, interação, estados | Card de recomendação, botões de feedback, formulário de Read With Music |
| **Estados de UI** | *Loading*, vazio, erro (seção 61) | Skeleton durante busca; mensagem amigável quando a API falha; "sem resultados" |
| **Formulários** | Validação | Login/registro, campos obrigatórios, mensagens de erro |
| **Rotas protegidas** | Redirecionamento | Dashboard e perfil exigem login; busca funciona sem login |
| **Integração com API (MSW)** | Contrato | Componentes tratam 401, 422, 429, 500 |
| **Acessibilidade** | Básico | `axe` em páginas principais; navegação por teclado nos botões de feedback |

Regra: testes de componentes usam **consultas por papel/texto** (`getByRole`, `getByText`), como o usuário enxerga a tela.

---

## 11. Testes E2E — Cobertura dos Critérios de Sucesso do MVP

Mapeamento direto com a seção 77 do escopo. Todos os fluxos rodam com **IA e providers fake** (determinísticos), exceto na suíte `live`.

| # | Critério do MVP | Teste E2E |
|---|---|---|
| 1 | Criar uma conta | `auth.spec.ts › registra novo usuário e é redirecionado ao dashboard` |
| 2 | Informar preferências | `profile.spec.ts › usuário salva artistas/gêneros favoritos` |
| 3 | Solicitar recomendação musical em linguagem natural | `music-discovery.spec.ts › busca por texto livre exibe resultados` |
| 4 | Receber músicas reais e relevantes | `music-discovery.spec.ts › resultados possuem título, artista e link externo` |
| 5 | Solicitar próximo livro | `book-discovery.spec.ts › busca por descrição` |
| 6 | Receber livros reais e relevantes | `book-discovery.spec.ts › resultados exibem capa, autor e descrição` |
| 7 | Informar um livro | `read-with-music.spec.ts › busca e seleciona livro` |
| 8 | Receber músicas adequadas à leitura | `read-with-music.spec.ts › gera lista com modo e contexto escolhidos` |
| 9 | Dar feedback | `feedback.spec.ts › like e dislike persistem` |
| 10 | Recomendações posteriores influenciadas | `personalization.spec.ts › item rejeitado não reaparece na busca seguinte` |
| 11 | Consultar recomendações anteriores | `history.spec.ts › histórico lista buscas e reabre resultado` |
| 12 | Acessar links externos | `external-links.spec.ts › link abre em nova aba com URL esperada` |

Cenários E2E adicionais: logout e sessão expirada (refresh de token), modo sem login (seção 26), erro de API exibindo mensagem compreensível.

---

## 12. Testes Não Funcionais

### 12.1. Segurança (alinhado à Security Specification)

- `bandit` (código Python) e `pip-audit` / `npm audit` (dependências) na CI.
- Testes de **validação de entrada**: payloads muito grandes, tipos incorretos, caracteres especiais/SQL (o ORM previne injection; o teste documenta isso).
- **Autorização por dono** em todos os recursos do usuário (playlists, histórico, preferências, interações).
- **CORS**: origem não permitida é rejeitada.
- **Logs**: teste garante que senhas, tokens e chaves de API **não aparecem** em logs (seção 59).
- **Prompt injection**: consultas maliciosas não alteram o schema de saída nem revelam prompts internos.

### 12.2. Performance

| Alvo | Como medir |
|---|---|
| Busca vetorial com N itens | `pytest-benchmark` em teste de integração (ex.: 10k vetores) |
| Pipeline completo (com fakes) | Tempo do código próprio, isolado de latência de rede |
| Pipeline real (LLM + providers) | Medição manual na suíte `live`/`ai_eval`, registrando p50/p95 |
| Carga leve na API | `locust` com poucos usuários simultâneos (Fase 10) |

Índice vetorial (HNSW/IVFFlat) deve ser validado com `EXPLAIN ANALYZE` quando o volume justificar.

### 12.3. Resiliência (seção 61)

Testes explícitos, um por cenário: API externa indisponível, timeout, resposta inválida, erro do LLM, rate limit, banco indisponível, conteúdo não encontrado. Cada um valida **(a)** código HTTP correto, **(b)** mensagem compreensível, **(c)** log adequado e **(d)** ausência de *stack trace* na resposta ao cliente.

---

## 13. Integração Contínua (CI)

Pipeline sugerido (GitHub Actions):

| Estágio | Conteúdo | Falha bloqueia merge? |
|---|---|---|
| 1. Lint & tipos | `ruff check`, `ruff format --check`, `mypy`, `eslint`, `tsc --noEmit` | Sim |
| 2. Unitários (backend) | `pytest -m unit --cov` | Sim |
| 3. Integração (backend) | Postgres+pgvector via *service container*; `pytest -m integration` | Sim |
| 4. Frontend | `vitest run` | Sim |
| 5. Segurança | `bandit`, `pip-audit`, `npm audit --omit=dev` | Sim (severidade alta) |
| 6. E2E | Playwright (apenas PR para `main`) | Sim |
| 7. Build | Build de imagem Docker e do frontend | Sim |
| Agendado (semanal) | `pytest -m "ai_eval or live"` | Não (gera relatório/alerta) |

Cobertura é publicada como artefato/comentário no PR.

---

## 14. Metas de Cobertura

| Módulo | Meta de linhas | Observação |
|---|---|---|
| `app/recommendation/*` | **≥ 90%** | Núcleo do produto |
| `app/ai/intent_parser.py` | **≥ 90%** | Incluindo caminhos de erro |
| `app/core/security.py`, `auth_service.py` | **≥ 90%** | Segurança |
| `app/services/*` | ≥ 80% | |
| `app/api/routes/*` | ≥ 80% | Via integração |
| `app/providers/*` | ≥ 80% | Contratos + erros |
| **Backend total** | **≥ 80%** | |
| Frontend (componentes críticos) | ≥ 70% | Priorizar fluxos, não % cega |

> **Cobertura é um piso, não um objetivo.** Um teste que executa código sem afirmar comportamento não conta como qualidade.

---

## 15. Convenções

- **Nomenclatura:** `test_<unidade>_<cenário>_<resultado_esperado>` — ex.: `test_ranking_dislike_penalty_lowers_score`.
- **Padrão AAA:** *Arrange – Act – Assert*, separados visualmente.
- **Um comportamento por teste** (evitar testes gigantes).
- **Markers `pytest`:** `unit`, `integration`, `e2e`, `ai_eval`, `live`, `slow`. Configurar `--strict-markers`.
- **Sem dependência de ordem** entre testes; sem estado compartilhado mutável.
- **Sem `sleep`**: usar controle de tempo (`freezegun`) e *awaits* explícitos.
- **Sem segredos** em fixtures; nada de chaves reais em testes.
- **Dados de teste em inglês/português** refletindo o uso real (consultas em português são obrigatórias no golden set).

```ini
# pytest.ini (ilustrativo)
[pytest]
asyncio_mode = auto
addopts = --strict-markers -ra
markers =
    unit: testes unitários rápidos, sem I/O
    integration: testes com banco real e fakes de IA/providers
    e2e: testes de ponta a ponta
    ai_eval: avaliação de qualidade com LLM/embeddings reais (manual)
    live: testes contra APIs externas reais (manual)
    slow: testes lentos
```

---

## 16. Exemplos de Testes

### 16.1. Ranking — propriedade

```python
import pytest
from hypothesis import given, strategies as st

from app.recommendation.ranking import RankingEngine, RankingWeights
from tests.factories import make_scored_candidate


@pytest.mark.unit
@given(sim_a=st.floats(0, 1), sim_b=st.floats(0, 1))
def test_ranking_higher_semantic_similarity_ranks_first(sim_a, sim_b):
    engine = RankingEngine(RankingWeights(semantic=1.0, preference=0, reference=0,
                                          context=0, popularity=0))
    a = make_scored_candidate(id="a", semantic_similarity=sim_a)
    b = make_scored_candidate(id="b", semantic_similarity=sim_b)

    ranked = engine.rank([a, b])

    if sim_a > sim_b:
        assert ranked[0].id == "a"
    elif sim_b > sim_a:
        assert ranked[0].id == "b"
```

### 16.2. Intent Parser — resposta inválida do LLM

```python
import pytest

from app.ai.intent_parser import IntentParser, IntentParsingError


@pytest.mark.unit
async def test_intent_parser_invalid_enum_raises_after_retries(fake_llm):
    fake_llm.queue_response({"intent": "music_discovery", "energy": "super-high"})
    fake_llm.queue_response({"intent": "music_discovery", "energy": "super-high"})
    parser = IntentParser(llm=fake_llm, max_retries=1)

    with pytest.raises(IntentParsingError):
        await parser.parse("Quero algo bem agitado")

    assert fake_llm.call_count == 2  # tentativa inicial + 1 retry
```

### 16.3. Pipeline — anti-hallucination

```python
import pytest


@pytest.mark.integration
async def test_pipeline_returns_only_items_from_provider(client, fake_llm, fake_music_provider):
    fake_llm.set_intent({"intent": "music_discovery", "mood": ["melancholic"], "energy": "low"})
    known_ids = {t.external_id for t in fake_music_provider.catalog}

    resp = await client.post("/recommendations/music",
                             json={"query": "algo melancólico e calmo"})

    assert resp.status_code == 200
    returned_ids = {item["external_id"] for item in resp.json()["items"]}
    assert returned_ids
    assert returned_ids <= known_ids  # nada inventado pela IA
```

### 16.4. Feedback influencia recomendações futuras

```python
import pytest


@pytest.mark.integration
async def test_disliked_item_does_not_reappear(auth_client, seeded_catalog):
    first = await auth_client.post("/recommendations/music", json={"query": "rock calmo"})
    rec_id = first.json()["id"]
    disliked = first.json()["items"][0]

    await auth_client.post(f"/recommendations/{rec_id}/feedback",
                           json={"entity_id": disliked["id"], "type": "DISLIKE"})

    second = await auth_client.post("/recommendations/music", json={"query": "rock calmo"})
    ids = [i["id"] for i in second.json()["items"]]
    assert disliked["id"] not in ids
```

---

## 17. Definition of Done (Testes)

Uma funcionalidade só é considerada concluída quando:

- [ ] Testes unitários cobrem a lógica nova (incluindo caminhos de erro).
- [ ] Há teste de integração para o fluxo/endpoint afetado.
- [ ] Se houver chamada a LLM/API externa: existe fake + teste de falha (timeout/resposta inválida).
- [ ] Se afetar ranking/prompt/embeddings: `ai_eval` executado e comparado ao baseline.
- [ ] Nenhuma queda da cobertura abaixo das metas da seção 14.
- [ ] Lint, tipos e segurança passam na CI.
- [ ] Testes de UI/E2E atualizados quando o fluxo do usuário mudou.
- [ ] Documentação (spec/README/ADR) atualizada quando necessário.

---

## 18. Matriz de Testes por Fase do Roadmap

| Fase | Testes a entregar |
|---|---|
| 1 — Foundation | Setup de `pytest`, CI mínima, testes de migração e de autenticação |
| 2 — External Data | Testes de contrato dos providers (fixtures), cache, erros HTTP |
| 3 — AI Layer | Fakes de LLM/embeddings, testes do `intent_parser`, primeiro golden set |
| 4 — Recommendation Engine | Testes de ranking/filtros/similaridade + propriedades; **baseline de qualidade** |
| 5 — Music Discovery | Integração do pipeline de música; endpoint `/recommendations/music` |
| 6 — Book Discovery | Idem para livros |
| 7 — Read With Music | Testes por modo; restrições de vocal/energia; golden set específico |
| 8 — Personalização | Feedback → perfil → ranking; histórico |
| 9 — Frontend | Testes de componentes; MSW; primeiros E2E |
| 10 — Polish | E2E completos do MVP, performance, segurança, acessibilidade |
| 11 — Deploy | *Smoke tests* pós-deploy (`/health`, login, uma busca) |

---

## 19. Smoke Tests Pós-Deploy

Após cada deploy em produção/staging, executar automaticamente:

1. `GET /health` → 200 (API e banco acessíveis).
2. `POST /auth/login` com usuário de teste dedicado → 200.
3. `POST /recommendations/music` com consulta fixa → 200 e ≥ 1 item.
4. Frontend carrega a home e o bundle referencia a URL correta da API.

Falha em qualquer etapa dispara alerta e avalia *rollback* (ver Deployment Guide).
