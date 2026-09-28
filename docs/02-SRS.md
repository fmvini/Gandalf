# Software Requirements Specification (SRS)

**Projeto:** {{PROJECT_NAME}}
**Versão:** 1.0
**Status:** Draft
**Baseado em:** [`01-PRD.md`](01-PRD.md)
**Padrão de referência:** estrutura inspirada em ISO/IEC/IEEE 29148

---

## 1. Introdução

### 1.1 Propósito
Este documento especifica os requisitos funcionais e não funcionais do sistema {{PROJECT_NAME}}, servindo como contrato técnico entre a visão de produto (PRD) e a implementação.

### 1.2 Escopo
Plataforma web para descoberta personalizada de músicas e livros por linguagem natural, com módulo de recomendação de músicas para leitura (*Read With Music*), perfil de preferências e aprendizado por feedback.

### 1.3 Definições, Acrônimos e Abreviações

| Termo | Definição |
|---|---|
| **LLM** | Large Language Model |
| **Embedding** | Representação vetorial de um texto/entidade para cálculo de similaridade |
| **pgvector** | Extensão do PostgreSQL para armazenamento e busca de vetores |
| **Intent Parser** | Componente que converte linguagem natural em critérios estruturados |
| **Candidate Retrieval** | Etapa de obtenção de itens reais candidatos à recomendação |
| **Provider** | Adaptador para uma fonte externa de dados (música ou livros) |
| **Structured Output** | Resposta do LLM validada contra um schema tipado |
| **MVP** | Minimum Viable Product |
| **RWM** | Read With Music |
| **JWT** | JSON Web Token |

### 1.4 Convenções
- **DEVE / DEVERÁ**: requisito obrigatório.
- **DEVERIA**: recomendado; pode ser adiado com justificativa.
- **PODE**: opcional.
- Prioridade: **P0** (MVP obrigatório), **P1** (MVP desejável), **P2** (pós-MVP).
- IDs: `RF-xxx` (funcional), `RNF-xxx` (não funcional), `RN-xxx` (regra de negócio).

---

## 2. Descrição Geral

### 2.1 Perspectiva do Produto
Sistema web autocontido (monolito modular) composto por SPA em React, API REST em FastAPI, PostgreSQL com pgvector e integrações externas (provedores de conteúdo e LLM).

### 2.2 Classes de Usuário

| Classe | Descrição | Acesso |
|---|---|---|
| **Visitante** | Sem conta | Busca básica, exploração (sem persistência) |
| **Usuário autenticado** | Conta registrada | Todas as funcionalidades personalizadas |

### 2.3 Ambiente de Operação
- Navegadores modernos (Chrome, Firefox, Safari, Edge — últimas 2 versões).
- Backend Python 3.11+ em contêiner.
- PostgreSQL 15+ com extensão `pgvector`.

### 2.4 Restrições
- **RC-01** Utilizar somente APIs gratuitas ou com plano gratuito adequado.
- **RC-02** Arquitetura monolítica modular (sem microservices).
- **RC-03** Sem armazenamento ou reprodução de áudio.
- **RC-04** Sem treinamento de modelo de ML próprio.
- **RC-05** Provedores externos acessados exclusivamente via camada de abstração.

### 2.5 Premissas e Dependências
Ver [`01-PRD.md` §14](01-PRD.md).

---

## 3. Regras de Negócio

| ID | Regra |
|---|---|
| **RN-001** | O LLM **nunca** é fonte de itens recomendados; apenas itens obtidos de provedores externos podem ser recomendados. |
| **RN-002** | O score final de cada item DEVE ser calculado pelo backend, não pelo LLM. |
| **RN-003** | Itens com `DISLIKE` ou `NOT_INTERESTED` do usuário NÃO DEVEM reaparecer em recomendações futuras (salvo pedido explícito). |
| **RN-004** | Itens com `ALREADY_KNOW` DEVEM ser rebaixados, mas não excluídos, em descoberta de músicas; em livros, excluídos. |
| **RN-005** | O resultado final NÃO DEVE conter mais de 2 itens do mesmo artista/autor em uma mesma lista (configurável). |
| **RN-006** | Candidatos NÃO DEVEM ser enviados em massa ao LLM (limite: apenas a etapa de parsing e explicação). |
| **RN-007** | Explicações só são geradas sob demanda do usuário. |
| **RN-008** | Usuário não autenticado NÃO PODE persistir preferências, histórico, favoritos ou feedback. |
| **RN-009** | Dados armazenados DEVEM ser limitados ao necessário para personalização. |
| **RN-010** | Mudança de provedor externo NÃO DEVE exigir alteração no Recommendation Engine. |

---

## 4. Requisitos Funcionais

### 4.1 Autenticação e Sessão (AUTH)

| ID | Requisito | Prioridade |
|---|---|:---:|
| RF-001 | O sistema DEVERÁ permitir registro com e-mail, username e senha. | P0 |
| RF-002 | O sistema DEVERÁ validar unicidade de e-mail e username. | P0 |
| RF-003 | O sistema DEVERÁ autenticar por e-mail/senha e emitir access token e refresh token JWT. | P0 |
| RF-004 | O sistema DEVERÁ permitir renovar o access token via refresh token. | P0 |
| RF-005 | O sistema DEVERÁ permitir logout com invalidação do refresh token. | P0 |
| RF-006 | O sistema DEVERÁ expor endpoint para recuperar os dados do usuário autenticado. | P0 |
| RF-007 | O sistema DEVERÁ proteger endpoints personalizados com autenticação. | P0 |
| RF-008 | O sistema PODERÁ suportar login OAuth (Google/Spotify). | P2 |

### 4.2 Interpretação de Linguagem Natural (NLU)

| ID | Requisito | Prioridade |
|---|---|:---:|
| RF-010 | O sistema DEVERÁ converter o pedido do usuário em objeto estruturado validado por schema. | P0 |
| RF-011 | O sistema DEVERÁ extrair, para música: mood, energia, atmosfera, gênero, instrumentação, vocais, intensidade, contexto de uso, período/estilo e referências. | P0 |
| RF-012 | O sistema DEVERÁ extrair, para livros: gênero, subgênero, atmosfera, temática, ritmo, complexidade, presença/ausência de romance, foco (personagem/mundo) e tom emocional. | P0 |
| RF-013 | O sistema DEVERÁ classificar a intenção (`music_discovery`, `book_discovery`, `read_with_music`) quando não informada explicitamente. | P1 |
| RF-014 | O sistema DEVERÁ extrair modificadores relativos à referência ("mais pesado", "menos intenso"). | P1 |
| RF-015 | O sistema DEVERÁ validar a saída do LLM e aplicar retry/fallback em caso de resposta inválida. | P0 |
| RF-016 | O sistema DEVERÁ funcionar com pedidos em português e inglês. | P1 |

### 4.3 Descoberta de Músicas (MUS)

| ID | Requisito | Prioridade |
|---|---|:---:|
| RF-020 | O sistema DEVERÁ aceitar um pedido em linguagem natural para música. | P0 |
| RF-021 | O sistema DEVERÁ aceitar música(s) e/ou artista(s) de referência. | P0 |
| RF-022 | O sistema DEVERÁ recuperar candidatos reais via `MusicProvider`. | P0 |
| RF-023 | O sistema DEVERÁ combinar a referência com modificadores solicitados. | P1 |
| RF-024 | O sistema DEVERÁ retornar lista ranqueada com título, artista, álbum, imagem, score e links externos. | P0 |
| RF-025 | O sistema DEVERÁ permitir filtros opcionais (gênero, energia, vocal). | P1 |
| RF-026 | O sistema DEVERÁ oferecer busca textual simples de músicas (`/music/search`). | P1 |

### 4.4 Descoberta de Livros (BOOK)

| ID | Requisito | Prioridade |
|---|---|:---:|
| RF-030 | O sistema DEVERÁ aceitar um pedido em linguagem natural para livros. | P0 |
| RF-031 | O sistema DEVERÁ aceitar livros de referência e/ou livros favoritos. | P0 |
| RF-032 | O sistema DEVERÁ recuperar candidatos reais via `BookProvider`. | P0 |
| RF-033 | O sistema DEVERÁ excluir livros já lidos/rejeitados pelo usuário. | P0 |
| RF-034 | O sistema DEVERÁ retornar título, autores, capa, descrição, ano, score e link externo. | P0 |
| RF-035 | O sistema DEVERÁ oferecer busca textual simples de livros (`/books/search`). | P1 |

### 4.5 Read With Music (RWM)

| ID | Requisito | Prioridade |
|---|---|:---:|
| RF-040 | O sistema DEVERÁ permitir buscar e selecionar um livro. | P0 |
| RF-041 | O sistema DEVERÁ inferir características musicais a partir de gênero, temas, descrição e atmosfera do livro. | P0 |
| RF-042 | O sistema DEVERÁ aceitar contexto adicional (ex.: "antes de dormir"). | P0 |
| RF-043 | O sistema DEVERÁ suportar os modos **Focus, Immersive, Cinematic, Calm e Custom**. | P0 (Focus/Calm/Custom), P1 (Immersive/Cinematic) |
| RF-044 | O sistema DEVERÁ aceitar preferência por instrumental/vocal. | P0 |
| RF-045 | O sistema DEVERÁ aceitar duração-alvo da playlist. | P1 |
| RF-046 | O sistema DEVERÁ gerar lista de faixas coerente com o livro, o modo e o contexto. | P0 |
| RF-047 | O sistema DEVERÁ aplicar restrições de diversidade (repetição de artistas). | P0 |
| RF-048 | O sistema DEVERÁ suportar progressão (início/meio/fim). | P2 |

### 4.6 Ranking e Recomendação (REC)

| ID | Requisito | Prioridade |
|---|---|:---:|
| RF-050 | O sistema DEVERÁ executar o pipeline: parsing → retrieval → filtering → similarity → personalization → ranking. | P0 |
| RF-051 | O sistema DEVERÁ calcular `semantic_score` via similaridade de embeddings. | P0 |
| RF-052 | O sistema DEVERÁ calcular `preference_score` com base no perfil do usuário. | P0 (básico) / P2 (vetorial avançado) |
| RF-053 | O sistema DEVERÁ calcular `reference_score` quando houver referência. | P1 |
| RF-054 | O sistema DEVERÁ calcular `context_score` com base no contexto informado. | P1 |
| RF-055 | O sistema DEVERÁ aplicar `popularity_factor` e `disliked_penalty`. | P1 |
| RF-056 | Os pesos do ranking DEVERÃO ser configuráveis sem alteração de código. | P1 |
| RF-057 | O sistema DEVERÁ persistir a recomendação e os scores por item. | P0 |
| RF-058 | O sistema DEVERÁ aplicar re-ranking de diversidade (MMR ou equivalente). | P1 |

### 4.7 Explicação (EXP)

| ID | Requisito | Prioridade |
|---|---|:---:|
| RF-060 | O sistema DEVERÁ oferecer "Por que isso foi recomendado?" por item. | P1 |
| RF-061 | A explicação DEVERÁ ser baseada nos fatores reais do ranking (não inventados). | P1 |
| RF-062 | A explicação NÃO DEVERÁ ser gerada automaticamente para todos os itens. | P0 |

### 4.8 Feedback e Personalização (FBK)

| ID | Requisito | Prioridade |
|---|---|:---:|
| RF-070 | O sistema DEVERÁ registrar `LIKE` e `DISLIKE` em músicas e livros. | P0 |
| RF-071 | O sistema DEVERÁ registrar `SAVE`, `MORE_LIKE_THIS`, `LESS_LIKE_THIS`, `ALREADY_KNOW`, `NOT_INTERESTED`. | P1 |
| RF-072 | O feedback DEVERÁ influenciar recomendações posteriores do mesmo usuário. | P0 |
| RF-073 | O sistema DEVERÁ atualizar o perfil de preferências a partir das interações. | P0 |
| RF-074 | O sistema DEVERÁ manter um perfil vetorial do usuário atualizado incrementalmente. | P2 |

### 4.9 Perfil, Histórico e Favoritos (PRF)

| ID | Requisito | Prioridade |
|---|---|:---:|
| RF-080 | O usuário DEVERÁ poder visualizar e editar preferências explícitas (artistas, gêneros, livros, autores). | P0 |
| RF-081 | O sistema DEVERÁ exibir preferências aprendidas (somente leitura ou editáveis). | P1 |
| RF-082 | O sistema DEVERÁ manter histórico de buscas e recomendações. | P0 |
| RF-083 | O usuário DEVERÁ poder reabrir uma recomendação anterior. | P0 |
| RF-084 | O usuário DEVERÁ poder manter coleções de favoritos (músicas, livros). | P1 |
| RF-085 | O usuário DEVERÁ poder criar, listar, visualizar e excluir playlists. | P2 |
| RF-086 | O usuário DEVERÁ poder limpar histórico, apagar preferências e excluir conta. | P2 |

### 4.10 Links Externos (EXT)

| ID | Requisito | Prioridade |
|---|---|:---:|
| RF-090 | Cada música DEVERÁ exibir link(s) para serviço externo (Spotify, YouTube). | P0 |
| RF-091 | Cada livro DEVERÁ exibir link para página externa (Open Library / Google Books). | P0 |
| RF-092 | O sistema PODERÁ exportar playlist para Spotify via OAuth. | P2 |

### 4.11 Modo sem Login (GUEST)

| ID | Requisito | Prioridade |
|---|---|:---:|
| RF-095 | Visitantes PODERÃO realizar buscas e ver recomendações sem persistência. | P1 |
| RF-096 | Ações personalizadas DEVERÃO solicitar autenticação. | P1 |

---

## 5. Requisitos Não Funcionais

### 5.1 Desempenho

| ID | Requisito | Meta |
|---|---|---|
| RNF-001 | Latência p95 de uma recomendação completa (sem cache) | ≤ 8 s |
| RNF-002 | Latência p95 com resultados de provider em cache | ≤ 3 s |
| RNF-003 | Latência p95 de endpoints não-IA (CRUD, auth) | ≤ 300 ms |
| RNF-004 | Nº de candidatos avaliados por pedido | 50–300 (configurável) |
| RNF-005 | Nº de itens retornados por pedido | 10–20 (configurável) |
| RNF-006 | Consulta vetorial (pgvector) com índice | ≤ 100 ms para 100 mil vetores |

### 5.2 Confiabilidade e Resiliência

| ID | Requisito |
|---|---|
| RNF-010 | Falha de um provider NÃO DEVE derrubar a requisição se houver provider alternativo ou cache. |
| RNF-011 | Chamadas externas DEVERÃO ter timeout, retry com backoff exponencial e circuit breaker simples. |
| RNF-012 | Falha do LLM DEVERÁ acionar fallback determinístico (parser por regras/keywords) quando possível. |
| RNF-013 | Erros DEVERÃO ser retornados em formato padronizado (ver API Spec). |

### 5.3 Segurança
Detalhado em [`09-Security-Specification.md`](09-Security-Specification.md).

| ID | Requisito |
|---|---|
| RNF-020 | Senhas armazenadas com hash forte (Argon2id ou bcrypt). |
| RNF-021 | Access token com expiração curta (≤ 30 min); refresh token rotativo. |
| RNF-022 | Validação de todas as entradas via Pydantic. |
| RNF-023 | Rate limiting por IP e por usuário. |
| RNF-024 | CORS restrito a origens configuradas. |
| RNF-025 | Segredos exclusivamente via variáveis de ambiente. |
| RNF-026 | Proteção contra SQL Injection via ORM/parâmetros. |
| RNF-027 | Mitigação de *prompt injection* nas entradas enviadas ao LLM. |

### 5.4 Usabilidade

| ID | Requisito |
|---|---|
| RNF-030 | Interface moderna, minimalista e responsiva (≥ 360 px). |
| RNF-031 | Estados de loading, vazio e erro em todas as telas de dados. |
| RNF-032 | Mensagens de erro compreensíveis, sem detalhes técnicos. |
| RNF-033 | Acessibilidade: navegação por teclado, contraste WCAG AA, labels em formulários. |

### 5.5 Manutenibilidade e Qualidade

| ID | Requisito |
|---|---|
| RNF-040 | Código Python 100% tipado e verificado (mypy/pyright). |
| RNF-041 | Lint e formatação automáticos (ruff, black ou equivalente). |
| RNF-042 | Cobertura de testes ≥ 80% nos módulos `recommendation/`, `ai/` e `services/`. |
| RNF-043 | Migrações versionadas (Alembic). |
| RNF-044 | Separação clara de camadas (api → services → engine/ai → providers → repositories). |
| RNF-045 | Recommendation Engine testável de forma isolada (sem rede/DB). |
| RNF-046 | Decisões arquiteturais relevantes registradas como ADR. |

### 5.6 Portabilidade
| ID | Requisito |
|---|---|
| RNF-050 | Execução local reproduzível via Docker Compose. |
| RNF-051 | Configuração 12-factor (variáveis de ambiente). |

### 5.7 Observabilidade

| ID | Requisito |
|---|---|
| RNF-060 | Logs estruturados (JSON) com `request_id`. |
| RNF-061 | Registrar: tempo total, tempo por etapa, provider utilizado, nº de candidatos, falhas, tempo/tokens de LLM. |
| RNF-062 | NÃO registrar senhas, tokens, e-mails em claro ou conteúdo sensível. |

### 5.8 Privacidade e Conformidade

| ID | Requisito |
|---|---|
| RNF-070 | Coletar apenas dados necessários (minimização). |
| RNF-071 | Suporte futuro a exclusão de conta e dados (LGPD). |
| RNF-072 | Respeitar termos de uso e limites de cada API externa. |

---

## 6. Requisitos de Interface Externa

### 6.1 Interface de Usuário
Ver [`08-UX-UI-Specification.md`](08-UX-UI-Specification.md).

### 6.2 Interface de Software (Provedores)

| Interface | Contrato | Implementação inicial |
|---|---|---|
| `BookProvider` | `search`, `get_by_id`, `find_similar` | `OpenLibraryProvider`, `GoogleBooksProvider` |
| `MusicProvider` | `search`, `get_by_id`, `find_similar`, `get_tags` | `MusicBrainzProvider`, `LastFmProvider` |
| `LLMClient` | `complete_structured`, `complete_text` | A definir (ADR-0005) |
| `EmbeddingService` | `embed`, `embed_batch` | A definir (ADR-0005) |

### 6.3 Interface de API
REST/JSON, versionada em `/api/v1`. Ver [`05-API-Specification.md`](05-API-Specification.md).

---

## 7. Casos de Uso

### UC-01 — Descobrir músicas por linguagem natural
- **Ator:** Usuário (autenticado ou visitante)
- **Pré-condição:** nenhuma (visitante: sem persistência).
- **Fluxo principal:**
  1. Usuário informa o pedido.
  2. Sistema interpreta a intenção (RF-010/011).
  3. Sistema recupera candidatos reais (RF-022).
  4. Sistema filtra, calcula similaridade e ranqueia (RF-050…055).
  5. Sistema persiste a recomendação (se autenticado) e retorna a lista.
- **Fluxos alternativos:**
  - **A1** LLM indisponível → fallback determinístico (RNF-012).
  - **A2** Nenhum candidato → mensagem "nenhum resultado" com sugestão de reformulação.
  - **A3** Provider indisponível → uso de cache/alternativo (RNF-010).
- **Pós-condição:** recomendação disponível no histórico (autenticado).

### UC-02 — Descobrir livros
Análogo ao UC-01, usando `BookProvider`, exclusão de livros lidos/rejeitados (RF-033) e critérios literários (RF-012).

### UC-03 — Read With Music
- **Pré-condição:** livro localizado via `BookProvider`.
- **Fluxo principal:**
  1. Usuário busca e seleciona o livro.
  2. Sistema obtém metadados e infere o **perfil musical do livro** (RF-041).
  3. Usuário informa contexto, modo, duração e preferência vocal.
  4. Sistema adapta o perfil musical ao modo/contexto.
  5. Pipeline de recomendação musical é executado com restrições de diversidade e duração.
  6. Sistema retorna a lista/playlist.
- **Alternativos:** livro sem descrição suficiente → usar gênero/assuntos; falha do LLM → mapeamento por gênero/assuntos.

### UC-04 — Registrar feedback
- **Ator:** Usuário autenticado
- **Fluxo:** clica em Like/Dislike → sistema persiste interação → atualiza preferências → confirma.
- **Regra:** interação é idempotente por (`user`, `entidade`, `tipo`).

### UC-05 — Solicitar explicação
- **Ator:** Usuário autenticado
- **Fluxo:** clica em "Por que isso foi recomendado?" → sistema recupera fatores do ranking → LLM gera texto → exibe.
- **Alternativo:** LLM indisponível → explicação por template com os fatores.

### UC-06 — Consultar histórico
Usuário lista recomendações anteriores, abre uma e vê os itens e feedbacks associados.

### UC-07 — Gerenciar perfil
Usuário edita artistas/gêneros/livros favoritos e visualiza preferências aprendidas.

### UC-08 — Registrar / autenticar
Fluxo padrão de registro, login, refresh e logout com JWT.

---

## 8. Modelo de Dados (resumo)

Entidades principais: `User`, `UserPreference`, `Music`, `Book`, `Playlist`, `PlaylistTrack`, `Recommendation`, `RecommendationItem`, `Interaction`, `SearchHistory`, `Embedding`.

> Detalhes em [`04-Data-Model.md`](04-Data-Model.md).

---

## 9. Critérios de Aceitação do MVP

| # | Critério | Requisitos vinculados |
|---|---|---|
| CA-01 | Criar conta e autenticar | RF-001…007 |
| CA-02 | Informar preferências iniciais | RF-080 |
| CA-03 | Recomendação musical por NL com itens reais | RF-010, 020, 022, 024, 050 |
| CA-04 | Recomendação de livros por NL com itens reais | RF-030, 032, 034 |
| CA-05 | Read With Music funcional | RF-040…047 |
| CA-06 | Feedback Like/Dislike persistido | RF-070, 072, 073 |
| CA-07 | Feedback altera recomendações seguintes | RF-072, RN-003 |
| CA-08 | Histórico acessível | RF-082, 083 |
| CA-09 | Links externos funcionais | RF-090, 091 |
| CA-10 | Nenhuma recomendação inexistente | RN-001 |
| CA-11 | Deploy público + docs + testes fundamentais | RNF-040…046 |

---

## 10. Matriz de Rastreabilidade (resumo)

| Objetivo (PRD) | Requisitos (SRS) | Documento de design |
|---|---|---|
| O1 Compreender NL | RF-010…016 | 06-AI-Architecture |
| O2 Conteúdo real | RN-001, RF-022, RF-032 | 03-System-Architecture, 07-Recommendation-Engine |
| O3 Aprender com feedback | RF-070…074 | 07-Recommendation-Engine, 04-Data-Model |
| O4 Read With Music | RF-040…048 | 06-AI-Architecture, 07-Recommendation-Engine |
| O6 Qualidade profissional | RNF-040…046 | 10-Testing-Strategy |

---

## 11. Itens em Aberto

| # | Questão | Destino |
|---|---|---|
| Q1 | Provedor musical definitivo (metadados de mood/energia) | ADR-0004 |
| Q2 | Modelo de LLM e de embeddings | ADR-0005 |
| Q3 | Dimensão dos embeddings e índice (HNSW vs IVFFlat) | ADR-0003 |
| Q4 | Estratégia de armazenamento de refresh tokens | ADR-0006 |
| Q5 | Redis no MVP? (previsto como não obrigatório) | ADR futuro |
