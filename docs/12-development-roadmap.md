# Development Roadmap

> **MusicProvider inicial — 2026-10-02:** protocolo name/search tipado e injeção pela factory implementados, com MusicBrainz default/mode offline preservados;163 testes focados PASS. Fontes/proveniência da trilha deixam de exigir MusicBrainz; tags não sobrescrevem atributos conhecidos. [Contrato/limites](music-provider-contract.md). G1 permanece aberto: interface inicial não prova cobertura, termos/licenças ou qualidade musical. UI de links alternativos em validação. Checkpoints de 01/10 abaixo são históricos; estado atual em IMPLEMENTATION_STATUS/DEVELOPMENT_LOG.

> **Playlists básicas — 2026-10-01:** POST/GET/GET por ID/DELETE implementados na API com ownership, snapshots, migração reversível e testes SQLite. [Contrato efetivo](05-API-Specification.md#7-playlists-playlists), [ADR-0014](adr/0014-owner-scoped-playlists.md). Próxima fatia: integrar salvar trilha, listagem/detalhe/exclusão à conta mantendo renovação/cancelamento; favoritos/histórico e validação PostgreSQL seguem pendentes.

> **CI inicial — 2026-10-01:** `.github/workflows/ci.yml` configura Ruff, pytest/SQLite, gate estrito do ranking v7 e build/E2E dos fluxos públicos. [Escopo e validação](CI.md). Primeira execução no GitHub, mypy, PostgreSQL/pgvector e auditorias ainda pendentes; a Fase 1 composta e G6 permanecem abertos.

> **Reconciliação de 2026-09-29:** consulte [IMPLEMENTATION_STATUS](IMPLEMENTATION_STATUS.md) para o estado efetivo. O caminho local foi entregue por fatias verticais e possui [baseline de 45 consultas](eval-reports/2026-09-29-local-baseline.md). O modo online existe experimentalmente, sem fechar G1/G2; os gates completos não estão aprovados. Próxima etapa: diferenciar modos de leitura sem regredir os baselines, antes de expandir integrações/personalização. Checkboxes compostos permanecem abertos enquanto parte da entrega estiver pendente.

> **Documento:** 12 de 15 — Documentação Técnica
> **Projeto:** Plataforma Inteligente de Descoberta de Músicas e Livros
> **Status:** Rascunho v1.0
> **Relacionados:** PRD (01), Arquitetura (03), Recommendation Engine Specification (07), Testing Strategy (10), Deployment Guide (11)

---

## 1. Objetivo

Organizar o desenvolvimento em fases, marcos e critérios de conclusão verificáveis, respeitando a **ordem de prioridade** definida no escopo (seção 76):

1. Qualidade das recomendações
2. Funcionamento correto
3. Arquitetura
4. Experiência do usuário
5. Personalização
6. Quantidade de funcionalidades

> **Regra de ouro:** é preferível ter menos funcionalidades extremamente bem executadas do que muitas incompletas. Quando o tempo apertar, **corte escopo, não qualidade**.

---

## 2. Visão Geral das Fases

| Fase | Nome | Marco | Esforço estimado* | Depende de |
|---|---|---|---|---|
| 1 | Foundation | M1 | 1–2 semanas | — |
| 2 | External Data | M1 | 1–2 semanas | 1 |
| 3 | AI Layer | M2 | 1–2 semanas | 1 |
| 4 | Recommendation Engine | M2 | 2–3 semanas | 2, 3 |
| 5 | Music Discovery | M3 | 1–2 semanas | 4 |
| 6 | Book Discovery | M3 | 1 semana | 4 |
| 7 | Read With Music | M3 | 2 semanas | 5, 6 |
| 8 | Personalização | M4 | 1–2 semanas | 5, 6 |
| 9 | Frontend | M4 | 3–4 semanas | API estável (5–8) |
| 10 | Polish | M5 | 1–2 semanas | 9 |
| 11 | Deploy | M5 | 1 semana | 10 |
| | **Total** | | **≈ 15–22 semanas** | |

\* *Estimativas para um desenvolvedor solo em ritmo parcial (ex.: 10–15 h/semana), incluindo testes e documentação. São referências para planejamento, não compromissos; **recalibre após a Fase 2**, quando a velocidade real estiver conhecida.*

### Linha do tempo

```
Semana:  1   3   5   7   9   11  13  15  17  19  21
Fase 1   ██
Fase 2     ██
Fase 3     ██
Fase 4         ███
Fase 5              ██
Fase 6              █
Fase 7                ██
Fase 8                   ██
Fase 9                      ████
Fase 10                          ██
Fase 11                            █
Marcos:  M1     M2      M3     M4      M5 (MVP público)
```

> Fases 2 e 3 podem ocorrer **em paralelo** (dados externos vs. camada de IA), pois ambas dependem apenas da Fase 1.

---

## 3. Marcos (Milestones)

| Marco | Nome | Fases | Critério de saída |
|---|---|---|---|
| **M1** | Backend base + dados reais | 1, 2 | Usuário autentica via API; busca real em livros e música funciona com cache e normalização |
| **M2** | Cérebro do sistema | 3, 4 | Consulta em linguagem natural → intent estruturada → candidatos → ranking testado; **baseline de qualidade registrado** |
| **M3** | Funcionalidades principais via API | 5, 6, 7 | Três fluxos (música, livro, Read With Music) funcionando ponta a ponta via Swagger |
| **M4** | Produto utilizável | 8, 9 | Personalização ativa e frontend completo consumindo a API |
| **M5** | MVP público | 10, 11 | Deploy público, testes, documentação, README e demo |

---

## 4. Portões de Qualidade (Quality Gates)

Pontos de decisão em que **não se avança** sem cumprir critérios. Existem para proteger a prioridade nº 1 (qualidade das recomendações).

| Portão | Ao final de | Critério |
|---|---|---|
| **G1 — Provider musical** | Fase 2 | Provider musical escolhido (ADR-012) provê metadados suficientes (tags/gêneros/descrições) para gerar embeddings úteis; limites e termos de uso avaliados |
| **G2 — Structured output** | Fase 3 | Taxa de conformidade do schema ≥ 95% no golden set inicial |
| **G3 — Qualidade base** | Fase 4 | Métricas do golden set (Precision@K, nDCG, existence rate = 100%) registradas como **baseline**; pesos iniciais de ranking justificados |
| **G4 — Paridade de fluxos** | Fase 7 | Os 3 fluxos passam nos critérios 3–8 do MVP (seção 77) via API |
| **G5 — Personalização efetiva** | Fase 8 | Teste automatizado prova que feedback altera recomendações seguintes (critério 10) |
| **G6 — Pronto para publicar** | Fase 10 | CI verde, E2E do MVP passando, checklist de segurança concluído |

---

## 5. Detalhamento das Fases

### Fase 1 — Foundation

**Objetivo:** base técnica sólida sobre a qual todo o resto será construído.

**Entregas**

- [ ] Repositório Git (branch `main` protegida, templates de issue/PR)
- [ ] Estrutura do backend conforme seção 34 do escopo
- [x] Configuração tipada (`core/config.py`) com Pydantic Settings e `.env.example`
- [ ] Docker Compose com PostgreSQL + pgvector
- [ ] SQLAlchemy + Alembic; **migração 0001** habilitando `vector`
- [x] Modelos: `User`, `UserPreference`, `Interaction`, `SearchHistory` (esqueleto dos demais)
- [x] Autenticação: registro, login, refresh, `GET /auth/me`, proteção de endpoints, hash seguro — SQLite e quatro grupos auth PostgreSQL reais aprovados; HTTP duas apps/rollout/demais corridas e CI hospedada pendentes
- [x] Tratamento consistente de erros (`core/exceptions.py`) e formato de erro padronizado
- [x] `GET /health` e `GET /health/ready`
- [ ] Lint (`ruff`), tipos (`mypy`), `pytest` e CI mínima — Ruff/pytest/workflow inicial preparados; mypy e primeira execução hospedada pendentes
- [x] Logging estruturado com `request_id`

**Critério de conclusão:** usuário registra, faz login, acessa `/auth/me`; testes de autenticação e migração passam na CI.

**Riscos:** *over-engineering* da fundação. **Mitigação:** entregar somente o necessário para autenticação + banco; expandir por demanda.

---

### Fase 2 — External Data

**Objetivo:** obter conteúdos **reais** de forma desacoplada (Provider Pattern).

**Entregas**

- [x] Interfaces iniciais `MusicProvider` e `BookProvider` (seção 31) — MusicProvider name/search/flags/envelope tipado e injeção concluídos; métodos ampliados de lookup/similares são desenho futuro
- [x] `OpenLibraryProvider` inicial
- [ ] **Spike de provider musical** (comparar candidatos por disponibilidade, limites, metadados, estabilidade e termos de uso) → **ADR-012**
- [ ] Implementação do provider musical escolhido — MusicBrainz integrado experimentalmente; escolha final de G1 pendente
- [ ] Normalização para modelos internos (`Music`, `Book`) — livros e música normalizados; contrato unificado/enriquecimento completos pendentes
- [ ] Cache de respostas externas com TTL (tabela no Postgres no MVP) — livros, música e IA implementados/testados em SQLite; validação PostgreSQL pendente
- [ ] Tratamento de erros: indisponibilidade, timeout, rate limit, *backoff*
- [x] Endpoints `GET /music/search`, `GET /music/{id}`, `GET /books/search`, `GET /books/{id}` — caminho local e integrações experimentais disponíveis
- [ ] Fixtures gravadas + testes de contrato dos providers
- [x] Fake providers para testes

**Critério de conclusão (G1):** buscas reais retornam dados normalizados e cacheados; trocar de provider exige alterar somente configuração + a implementação do provider.

**Riscos:** o provider musical não oferece metadados suficientes (humor, energia, descrição). **Mitigação:** planejar enriquecimento via LLM/embeddings a partir de tags, gêneros e descrições disponíveis; considerar combinar mais de uma fonte.

---

### Fase 3 — AI Layer

**Objetivo:** interpretar linguagem natural em dados estruturados e gerar embeddings.

**Entregas**

- [ ] `LLMClient` (interface provider-agnóstica) com *timeout*, *retry* e registro de tokens/latência
- [ ] Schemas Pydantic de *intent* (música, livro, Read With Music) — seção 28
- [ ] `IntentParser` com *structured output* e validação; classificação automática de intenção (barra de busca inteligente, seção 49)
- [ ] `EmbeddingService` (interface + implementação) e colunas `embedding vector(N)`
- [ ] Geração e persistência de embeddings de itens (Music/Book) e de consultas
- [ ] Sanitização de entrada e defesa básica contra *prompt injection*
- [ ] `FakeLLMClient` e `FakeEmbeddingService`
- [ ] **Golden set inicial** (≥ 15 consultas por módulo) e script `ai_eval` — corpus editorial de 45 consultas e CLI offline concluídos; avaliação do LLM real pendente
- [ ] ADRs de LLM e embeddings (modelo, dimensão)

**Critério de conclusão (G2):** parser retorna JSON válido em ≥ 95% do golden set; falhas são tratadas sem exceções não capturadas.

**Riscos:** custo e latência de LLM; variação de saída. **Mitigação:** schema estrito, *retry* limitado, cache de intents idênticas, prompts versionados.

---

### Fase 4 — Recommendation Engine

**Objetivo:** construir o núcleo diferencial — recuperar, filtrar, pontuar e ranquear.

**Entregas**

- [ ] `CandidateRetriever` (providers + busca vetorial no banco)
- [ ] `filters.py` (rejeitados, já conhecidos, vocais, duração, etc.)
- [ ] `similarity.py` (cosseno; utilitários vetoriais)
- [ ] `SemanticMatcher`, `PreferenceMatcher`, `ContextMatcher`
- [ ] `RankingEngine` com pesos configuráveis e *score breakdown* (base para "Por que isso foi recomendado?")
- [x] Regras de **diversidade** (limite de repetição de artistas) — máximo de dois itens por criador
- [ ] `RecommendationPipeline` orquestrando o fluxo da seção 19
- [ ] Persistência de `Recommendation` e `RecommendationItem`
- [ ] Testes unitários + propriedades (`hypothesis`) + integração do pipeline
- [x] **Baseline de qualidade** (Precision@K, nDCG, diversidade, existence rate) — caminho local, 45 consultas, K=5/10; avaliação online permanece pendente
- [ ] Documento *Recommendation Engine Specification* consistente com a implementação

**Critério de conclusão (G3):** pipeline funciona com fakes e com dados reais; cobertura ≥ 90% em `recommendation/`; baseline registrado em `docs/eval-reports/`.

**Riscos:** ranking "plausível mas medíocre". **Mitigação:** golden set + métricas objetivas; iteração dos pesos com base em dados, não em impressão; registrar experimentos.

---

### Fase 5 — Music Discovery

**Objetivo:** primeira funcionalidade completa ponta a ponta (via API).

**Entregas**

- [ ] `POST /recommendations/music` e `POST /music/discover`
- [ ] Descoberta por linguagem natural (humor, atmosfera, energia, vocais, contexto)
- [ ] Descoberta **por referência** ("parecido com X, mas mais pesado") — seção 7
- [ ] Links externos (Spotify/YouTube) por música — seção 14
- [x] Modo sem login funcional
- [ ] Histórico de busca salvo para usuários autenticados
- [ ] Testes de integração e golden set de música

**Critério de conclusão:** critérios 3, 4 e 12 do MVP satisfeitos via API.

---

### Fase 6 — Book Discovery

**Objetivo:** segunda funcionalidade completa, reaproveitando o engine.

**Entregas**

- [ ] `POST /recommendations/books` e `POST /books/discover`
- [ ] Extração de gênero/subgênero, atmosfera, ritmo, presença/ausência de romance, foco em personagens/mundo
- [ ] Recomendação a partir de livros que o usuário gostou (seção 9)
- [ ] Capa, autor, descrição e link externo
- [ ] Testes e golden set de livros

**Critério de conclusão:** critérios 5 e 6 do MVP satisfeitos via API.

---

### Fase 7 — Read With Music

**Objetivo:** módulo diferencial; a "assinatura" do projeto.

**Entregas**

- [ ] `POST /recommendations/read-with-music`
- [ ] Busca e seleção de livro; extração de características da obra (atmosfera, temas, ambiente)
- [ ] Tradução do livro + contexto ("antes de dormir") em critérios musicais
- [ ] **Modos:** `focus`, `immersive`, `cinematic`, `calm`, `custom` (seção 11)
- [ ] Preferência por vocal/instrumental e duração-alvo
- [ ] Geração de lista/playlist coerente (duração, energia, atmosfera, repetição de artistas, letras)
- [ ] Testes por modo + golden set específico + restrições (ex.: `max_vocal_tracks`)
- [x] `POST /playlists`, `GET /playlists`, `GET /playlists/{id}`, `DELETE /playlists/{id}` (persistência básica) — API/SQLite, migração 0006; UI e PostgreSQL real pendentes

**Critério de conclusão (G4):** critérios 7 e 8 do MVP satisfeitos; cada modo produz resultados **mensuravelmente diferentes** e coerentes.

**Riscos:** subjetividade (o que "combina" com um livro). **Mitigação:** usar a descrição/subjects do livro como base de embeddings e validar com o golden set; permitir ajuste via modo `custom`.

---

### Fase 8 — Personalização

**Objetivo:** fazer o sistema aprender com o usuário.

**Entregas**

- [ ] `POST /recommendations/{id}/feedback` (Like, Dislike, Save, More/Less like this, Already know, Not interested)
- [ ] `user_profile.py`: perfil por pesos (`UserPreference`) e, no MVP, vetor de preferências simples atualizado incrementalmente
- [ ] Integração do perfil ao ranking (`user_preference_similarity` e penalidades)
- [ ] `GET /recommendations/history` e `GET /recommendations/{id}`
- [ ] `GET/POST/PATCH /users/me/preferences`
- [ ] Explicação sob demanda ("Por que isso foi recomendado?") a partir do *score breakdown*, com fallback por template
- [ ] Testes: feedback → perfil → ranking

**Critério de conclusão (G5):** teste automatizado demonstra que itens rejeitados não reaparecem e que likes elevam itens semelhantes; critérios 9, 10 e 11 do MVP satisfeitos.

**Riscos:** perfil instável (uma interação altera demais). **Mitigação:** taxa de aprendizado limitada, normalização, decaimento opcional.

---

### Fase 9 — Frontend

**Objetivo:** interface moderna e minimalista consumindo a API.

**Entregas**

- [ ] Projeto React + Vite, roteamento, cliente HTTP tipado, gerenciamento de estado de servidor
- [ ] Autenticação (registro, login, logout, sessão/refresh, rotas protegidas)
- [ ] **Home** ("What are you looking for?") com 3 cards: Discover Music, Find My Next Book, Read With Music
- [ ] Barra de busca inteligente (classificação automática de intenção)
- [ ] Telas: Discover Music, Find My Next Book, Read With Music
- [ ] Componentes de resultado (capa/arte, metadados, links externos, feedback, salvar, "por quê?")
- [ ] Dashboard (recentes, salvos, playlists, histórico, preferências aprendidas)
- [ ] Perfil (visualizar/editar preferências)
- [ ] Estados de *loading*, vazio e erro com mensagens compreensíveis
- [ ] Responsividade e acessibilidade básica
- [ ] Testes de componentes (Vitest/RTL/MSW) e primeiros E2E

**Critério de conclusão:** todos os 12 critérios do MVP executáveis pela interface.

> **Recomendação:** desde a Fase 5, validar a API pelo Swagger e por scripts/cURL para **não bloquear** o backend esperando a UI; iniciar o esqueleto do frontend (auth + home) ao final da Fase 7 para reduzir o risco do "big bang".

---

### Fase 10 — Polish

**Objetivo:** transformar um protótipo funcional em projeto de qualidade profissional.

**Entregas**

- [ ] E2E completos cobrindo os 12 critérios do MVP
- [ ] Revisão de performance (latência do pipeline, índice vetorial, *N+1*, cache)
- [ ] Revisão de segurança (checklist do Deployment Guide, seção 13)
- [ ] Tratamento de erros revisado em toda a stack (seção 61)
- [ ] Rate limiting e limites de gasto do LLM
- [ ] Acessibilidade e *loading states* refinados
- [ ] Documentos 1–15 revisados e consistentes com o código
- [ ] README completo com *screenshots* e GIF/vídeo de demonstração
- [ ] Diagramas finais (seção 71 do escopo)

**Critério de conclusão (G6):** CI verde; metas de cobertura atingidas; nenhum erro crítico/alto de segurança em aberto.

---

### Fase 11 — Deploy

**Objetivo:** publicar o MVP.

**Entregas**

- [ ] Banco gerenciado com pgvector e backups
- [ ] Backend em container com *health checks* e logs
- [ ] Frontend estático publicado, domínio(s) e HTTPS
- [ ] Variáveis de ambiente e segredos configurados
- [ ] CI/CD com *smoke tests* pós-deploy
- [ ] Monitoramento de uptime e erros
- [ ] Tag `v1.0.0`, *release notes* e `CHANGELOG.md`

**Critério de conclusão:** checklist de go-live (Deployment Guide, seção 15) 100% concluído; **definição de sucesso do MVP (seção 77) atendida em produção**.

---

## 6. Definition of Done (Global)

Uma tarefa/funcionalidade está pronta quando:

- [ ] Código tipado, revisado (autorevisão via PR) e sem *warnings* de lint/tipos
- [ ] Testes (unitário + integração) escritos e passando; metas de cobertura mantidas
- [ ] Erros tratados e mensagens compreensíveis
- [ ] Logs relevantes adicionados (sem dados sensíveis)
- [ ] Documentação e/ou ADR atualizados
- [ ] Migrações incluídas e testadas (up/down)
- [ ] Nenhum segredo commitado
- [ ] CI verde

---

## 7. Registro de Riscos

| # | Risco | Prob. | Impacto | Mitigação | Gatilho de revisão |
|---|---|---|---|---|---|
| R1 | Provider musical com metadados pobres | Alta | Alto | Spike na Fase 2; enriquecer via LLM/embeddings; combinar fontes | G1 |
| R2 | Mudança de termos/limites/endpoints de APIs externas | Média | Alto | Provider Pattern; cache; fixtures; suíte `live` semanal | Falha na suíte `live` |
| R3 | Custo/latência do LLM acima do esperado | Média | Médio | Rate limit; cache de intents; modelo menor no parser; explicação sob demanda | Custo diário > limite |
| R4 | Qualidade das recomendações insuficiente | Média | **Crítico** | Golden set; métricas; iteração de pesos; portões G3/G4 | Métricas abaixo do baseline |
| R5 | Saída do LLM fora do schema | Média | Médio | Structured output; validação; retry limitado; fallback | Conformidade < 95% |
| R6 | Escopo excessivo / *feature creep* | Alta | Alto | Pós-MVP explícito (seção 8); regra da seção 76 | Fase atrasada > 30% |
| R7 | Trocar modelo de embeddings (dimensão) | Baixa | Médio | Dimensão configurável; procedimento de reindexação documentado | Novo modelo avaliado |
| R8 | Limites da hospedagem gratuita (RAM, *cold start*) | Média | Médio | Embeddings via API; documentar *cold start*; escolher provedor conforme critérios | Fase 11 |
| R9 | Abuso do endpoint anônimo (custo de LLM) | Média | Alto | Rate limit por IP; limites de consultas anônimas; CAPTCHA se necessário | Picos de uso |
| R10 | Frontend só no final revela problemas de API | Média | Médio | Swagger/cURL desde a Fase 5; esqueleto da UI ao fim da Fase 7 | Início da Fase 9 |
| R11 | Perfil de usuário instável / viés de bolha | Média | Médio | Taxa de aprendizado limitada; diversidade no ranking | Testes G5 |
| R12 | Desmotivação / prazo | Média | Alto | Marcos curtos, entregas verticais, demo contínua | Marco atrasado |

---

## 8. Backlog Pós-MVP

Priorização sugerida (revisar após o MVP com base em uso real e métricas da seção 67 do escopo).

### Próximo ciclo (v1.x)

| Item | Valor | Esforço | Observação |
|---|---|---|---|
| Perfil vetorial avançado | Alto | Médio | Decaimento temporal, múltiplos "gostos" (clusters) |
| Progressão musical da playlist | Alto (diferencial) | Médio | Início calmo → meio aventura → final épico (seção 13) |
| Playlists persistentes avançadas | Médio | Baixo | Edição, reordenação, duplicação |
| Explicações avançadas | Médio | Baixo | Comparar com itens que o usuário curtiu |
| Exportar/limpar dados (privacidade) | Alto | Baixo | Limpar histórico, apagar preferências, excluir conta (seção 63) |
| Redis (cache/rate limit) | Médio | Baixo | Seção 60 |

### Médio prazo (v2.x)

| Item | Observação |
|---|---|
| Spotify OAuth + exportação de playlists | Considerar limites/termos vigentes da API; funcionalidade futura (seções 14–15) |
| Login Google (OAuth) | Seção 25 |
| Compartilhamento de playlists | Links públicos com privacidade controlada |
| Métricas de produto (Like rate, Save rate, Diversidade, etc.) | Seção 67 |

### Longo prazo / exploração

| Item | Observação |
|---|---|
| Recomendação colaborativa | Exige volume de usuários |
| Análise de comportamento | Depende de telemetria consentida |
| Sistema social | Fora do foco inicial |
| Novas mídias (filmes, games, podcasts) | Direção do "Unified Discovery Platform" (seção 75); manter o modelo de dados e providers extensíveis |

---

## 9. Cadência de Trabalho Sugerida

- **Ciclos de 1–2 semanas** com objetivo claro (ex.: "concluir `IntentParser` com testes").
- **Entregas verticais:** preferir uma fatia funcional completa (API + testes + doc) a várias camadas incompletas.
- **Revisão ao fim de cada fase:** checklist de entregas, DoD, atualização deste roadmap e do CHANGELOG.
- **ADR imediato** para decisões estruturais (não deixar para "documentar depois").
- **Demonstração mensal** (gravar GIF/vídeo curto): serve de motivação e de material de portfólio.
- **Registro de experimentos de ranking** (pesos, prompts, embeddings) em `docs/eval-reports/`, com data, mudança e métricas.

---

## 10. Como Manter Este Documento

- Marcar checkboxes conforme o avanço; registrar datas reais de início/fim por fase.
- Atualizar estimativas após a Fase 2 e ao final de cada marco.
- Toda alteração de escopo do MVP deve ser justificada e refletida no PRD e neste roadmap.
- Riscos novos entram na seção 7 com dono, gatilho e mitigação.
