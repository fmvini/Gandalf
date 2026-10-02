# Estado da implementação — 2026-10-02

> **Checkpoint final de 02/10:** seis commits seletivos da entrega em `318d97a`, `f2adc7c`, `1663c2c`, `ef0c284`, `137d492`, `03a51e9`, mais consolidação documental; sem push. Maestro aprovou 366 testes API, 38 de livros/capas pós-fix, Ruff84/gates v7 e build de 2.050 módulos. Dez módulos frontend aprovados em rodadas coordenadas; reteste continuation/favorites/live com API real/SQLite/duas contas/temas/mobile PASS. Covers PASS com 60 capturas e zero erros de runtime. Capas locais na seleção verificadas; novas URLs externas/normalizador/fallback corrigidos, mas fonte/capa externa atual não comprovada. API online PID31444/8000 com status/readiness200; frontend localhost:5173 (::1) serve patch200. Groq original/cota observada2/50, sem mudança de chave/modelo/limite. PostgreSQL/pgvector real e online externo continuam pendentes. Log/CONTINUATION possuem sequência e evidências; registros abaixo são históricos.

> **Checkpoint inicial de 02/10 (histórico):** re-roll musical implementado no backend/frontend com exclusões cumulativas e filtros preservados; disponibilidade/paginação corrigidas para livros e músicas. Alert público shadcn listado no 21st.dev e AnimatedContent React Bits adaptado para Motion integrados usando impeccable/taste; QA final pendente. Backend: 361 aprovados/3 bloqueados por pipes Windows na suíte completa, subset 185, reroll final20, Ruff83 e gates K=5/10 v7 sem regressões. TypeScript/testes de estado frontend passaram; build/E2E bloqueados por `spawn EPERM`. Favoritos herdados e mudanças desta sessão ainda sem commit: `.git` somente leitura (`index.lock` negado), nenhum push. API online8000/status/readiness200; fontes externas/Groq falharam no transporte/conexão recusada, sem indício de chave inválida, sem troca de chave/modelo/cota (uma tentativa consumiu 1/50). MCP21st também indisponível; componente veio da fonte pública oficial. PostgreSQL/pgvector real permanece pendente. Consultar log e registros dos agentes para validações finais/continuidade.

> **Favoritos — checkpoint de encerramento:** schema `0008_favorites` em `bfa418b` e backend com POST origem/item (201/200), GET paginado/tipo, POST status em lote e DELETE idempotente 204 por proprietário. Snapshot independente do cache/catálogo, primeiro salvo preservado, sem feedback/ranking/histórico automático. 346 testes backend, Ruff e gates K=5/10 aprovados; revisão corrigiu disponibilidade na validação da conta e concorrência criar/excluir. [Contrato](05-API-Specification.md#83-favoritos-individuais--contrato-implementado)/[ADR-0016](adr/0016-owner-scoped-favorites.md). Frontend **WIP sem commit**: build e favoritos isolados aprovados, 36 capturas; npm test/live e seis outros módulos atuais ainda não validados. Usuário encerrou o dia antes dessa execução; retomar validação/frontend antes de nova feature. PostgreSQL real continua pendente.

> **Cache compartilhado validado:** migração 0007 (`54e13c2`) e store de resultados públicos compartilham origem/explicações entre instâncias e após reinício, por até uma hora/256 resultados no banco inteiro. Snapshot mínimo sem consulta/intenção/conta; sem renovação de TTL ou segundo cache local. Expiração/evicção retorna 404; banco configurado indisponível retorna 503. 302 testes backend, Ruff/formatação e gates v7 K=5/10 aprovados; três processos SQLite concorrentes testados. [ADR-0015](adr/0015-shared-recommendation-cache.md). PostgreSQL real permanece pendente.

> **Playlists na interface:** salvar trilha completa, login/cadastro com retorno à seleção/controles, lista paginada na conta, detalhe e exclusão com confirmação integrados. Build e todos os módulos da suíte frontend aprovados, incluindo API real/SQLite temporário, duas contas, persistência, isolamento 404 e revogação 401. 24 capturas em 1440/390/320 px nos dois temas revisadas; reviewer retornou `ship` no escopo visual/código. Sem mudança de endpoints, dependências ou identidade aprovada. Continuidade em [CONTINUATION](CONTINUATION.md#playlists-na-interface--entrega-validada).

> **Correção de duração e idioma:** leitura online usa só faixas reais MusicBrainz de duração conhecida (90 s–10 min), até oito páginas de 50 candidatos por termo, 60 faixas/quatro por artista. Sucesso exige a duração pedida; insuficiência retorna `503 SOUNDTRACK_INCOMPLETE`, sem complemento local/estimado. IA não limita a quantidade. Busca de livros por títulos das edições, prioridade português e alias verificado de Alasca/John Green. Teste real com o pedido exato: 20 faixas, 91 min 57 s, meta 90, IA ativa/sem degradação. 293 testes backend, Ruff, build/suíte frontend e gates v7 aprovados. Detalhes e limitações no log.

> **Novos livros:** interface “Ver outros livros”, exclusões acumuladas e paginação/cache por página. Salvamento por origem aceita 60 faixas; manual 25. Groq mantém cota e retry limitados anteriores.

> **Instância online para teste do usuário:** frontend em `http://127.0.0.1:5173`, API/Swagger em `http://127.0.0.1:8000/docs`; readiness 200, Open Library/MusicBrainz e Groq `openai/gpt-oss-20b` ativos. Buscas reais e duas descobertas finais com fontes externas/`ai_used=true`/`degraded=false` verificadas; primeira tentativa acionou fallback transitório. Este registro pontual não fecha gates online. Verificar processos antes de reiniciar; usar `start-local.ps1 -Online` para manter internet. Detalhes no log.

> **Playlists básicas na API:** migração 0006 e POST/GET/GET por ID/DELETE com isolamento entre contas, faixas em ordem e metadados preservados após reinício. [Contrato](05-API-Specification.md#7-playlists-playlists) e [ADR-0014](adr/0014-owner-scoped-playlists.md). Interface integrada; favoritos/histórico, edição/exportação e PostgreSQL real ainda pendentes.

> **Checkpoint de 2026-10-01:** v7 de piano/detetive validado e preservado no commit `f120676`: 220 testes backend, Ruff/formatação e comparação estrita K=5/10 contra v6 sem perdas. A continuação de UI concluiu Accordion/Toggle Group/Skeleton e explicações compartilhadas; build, smoke, testes de componentes e E2E com API real passaram na árvore atual. Desktop 1440 px e mobile 390/320 px revisados nos dois temas, com contraste dos filtros e movimento reduzido verificados. Histórico em [HANDOFF_MAESTRI.md](HANDOFF_MAESTRI.md) e no log.

A matriz abaixo descreve as entregas verificadas registradas no log. Os documentos numerados incluem o desenho completo do produto. Histórico e continuidade: [DEVELOPMENT_LOG](DEVELOPMENT_LOG.md) e [CONTINUATION](CONTINUATION.md).

## Execução

| Modo | Ativação | Comportamento |
|---|---|---|
| Local | `start-local.ps1` ou `python local.py` | SQLite, 18 livros e 25 músicas, ranking determinístico `local-rules-v7`; sem chamadas externas após instalar dependências |
| Online experimental | `start-local.ps1 -Online` ou `GANDALF_ONLINE=1` ao executar `local.py` | Open Library, MusicBrainz, catálogo local; Groq opcional interpreta e pontua candidatos; fallback por regras |
| API configurada diretamente | `uvicorn app.main:app` em `api/` | `ONLINE_CATALOG` e `BOOK_PROVIDER` definem o comportamento |

`local.py` aplica migrações e mantém SQLite/segredo em `api/.local`. No modo offline ignora `.env`; no online lê `api/.env`, mantendo banco e segredo locais. O modo online é opcional. Seu limite interno de chamadas não consulta nem controla faturamento do fornecedor, portanto não garante custo zero de uma conta externa. Esta reconciliação não ativa integrações nem altera configurações do usuário.

## Entregas verificadas

| Área | Implementado | Pendências |
|---|---|---|
| API | FastAPI, erros padronizados, CORS, request ID, health/readiness, configuração tipada; workflow de CI preparado para Ruff/pytest/ranking local | Primeira execução hospedada da CI; mypy não integrado |
| Banco | SQLAlchemy, migrações 0001–0008, contas, catálogo/cache, cota diária de IA, playlists/faixas, snapshots temporários e favoritos; FKs SQLite; IDs reais deterministas auditados, sem migração para re-roll | PostgreSQL/pgvector real e concorrência de refresh entre processos pendentes; três casos multiprocessos SQLite aprovados na suíte Maestro |
| Auth | Registro, login, JWT, refresh rotativo, logout, `/auth/me`; telas `/register`, `/login` e `/account`, sessão em memória e renovação concorrente segura | Recuperação de senha, edição de conta; rate limiting compartilhado |
| Livros | Busca/detalhe local e Open Library, cache persistente, busca híbrida online; normalizador conserva capa da obra e gera default=false | Metadados incompletos; verificação atual de capas externas; sem embeddings |
| Música | Busca/detalhe local e MusicBrainz, UUID/MBID, duração opcional, cache persistente | Escolha final/licenças/cobertura de G1; interface abstrata musical |
| IA | Groq com schemas validados, timeout, cache e limite diário persistido | Não segue integralmente ADR-0002: IA também pontua; sem embeddings ou avaliação real no corpus |
| Descoberta | Três fluxos públicos, filtros, exclusões, referências, diversidade e explicações; re-roll MUSIC/BOOK com UUIDs cumulativos, paginação e disponibilidade limitada; ranking local v7 preservado; cache temporário compartilhado com banco configurado | E2E real atual de re-roll/fontes/LLM, cobertura parcial de instrumentos/subgêneros; personalização e histórico pessoal |
| Leitura | Cinco modos, preferência vocal/duração-alvo, critérios locais v4/v5; trilha completa salva na conta; contrato de duração conhecida online preservado | Revisão humana da diferenciação/afinidade |
| Playlists | API e interface para salvar trilha/listar/detalhar/excluir por proprietário; origem compartilhada entre instâncias, paginação e cópia de metadados/ordem/duração; até 60 faixas por origem e 25 manuais na API | Edição/exportação e criação manual na UI; execução real PostgreSQL |
| Favoritos individuais | Schema 0008 e API de snapshots por conta MUSIC/BOOK, origem validada, dedup, paginação/filtro, estado em lote e exclusão idempotente; UI validada e versionada com coleção/filtros/remoção e retorno do login | PostgreSQL real; backend e E2E SQLite/duas contas aprovados |
| Interface | Home imersiva, três fluxos, temas; Accordion/Toggle Group/Skeleton/Alert; AnimatedContent React Bits com movimento reduzido; re-roll MUSIC/BOOK e favoritos validados; capas compartilhadas com fallback por fonte/erro/1×1; explicações lazy/cache/retry; cadastro/login/conta/logout; playlists com retorno do login, confirmação de exclusão, retry e cancelamento | Fontes/capas externas reais atuais; histórico, feedback, perfil de preferências |
| Qualidade | 366 testes backend aprovados; 38 de livros/capas pós-fix, Ruff84, gates v7 K=5/10 intactos; build, dez módulos frontend e E2E real/SQLite aprovados em rodadas; 60 capturas de capas; corpus/baselines v3–v7 preservados; commits locais registrados | Fontes/capas/LLM real atuais por transporte, PostgreSQL; ranking sem revisão humana independente ou conjunto reservado |

## Contrato online efetivo

Implementação: `api/app/ai/groq.py`, `api/app/services/online_recommendations.py`, `api/app/services/online_store.py`.

1. IA interpreta termos de catálogo; o serviço usa até dois, recuperando até 15 itens por termo.
2. Pool final: até 18 itens externos e sete locais, deduplicados por título/autoria, até 25 candidatos.
3. IA retorna índices, scores e estimativas de voz/energia. Backend rejeita índices inválidos/repetidos, score abaixo de 0,25, referências, temas excluídos e violações dos filtros; limita dois itens por criador.
4. Falhas de interpretação/seleção acionam tentativa de ranking por regras; pode retornar vazio, informando degradação. Não há garantia de resultado útil para qualquer consulta.
5. Estimativas da IA não sobrescrevem metadados persistidos. `classification_source=ai_estimate` identifica a classificação aplicada a itens MusicBrainz; detalhe retorna dados da fonte.
6. `AI_DAILY_LIMIT` (padrão 50, máximo 200) conta tentativas não atendidas por cache em dia UTC; não tokens/dinheiro. Banco/cota/chave ausentes impedem novas chamadas da IA. Respostas válidas em cache podem ser reutilizadas; cache de IA dura 24 h.

Não há áudio integrado nem exportação Spotify. Energia/vocais não são fornecidos pelo normalizador MusicBrainz e permanecem nulos até a estimativa usada na recomendação. Rate limit musical usa intervalo por instância; não coordena múltiplos processos.

## Gates e sequência

- **G1 aberto:** MusicBrainz integrado experimentalmente; faltam matriz de cobertura e revisão atual de termos/campos para uso público. Evidência de 2026-09-28 no ADR é histórica.
- **G2 aberto:** testes com IA simulada; conformidade real não medida.
- **G3 parcial local:** [baseline registrado](eval-reports/2026-09-29-local-baseline.md), sem concluir motor semântico/persistência/cobertura do desenho completo.
- **G4 aberto:** três fluxos funcionam, mas distinção entre modos insuficiente.
- **G5 aberto:** feedback/perfil/ranking personalizado ausentes.
- **G6 aberto:** [CI inicial configurada](CI.md) e checks locais aprovados; falta execução hospedada verde, auditoria final e deploy público.

Piano/detetive foram validados na [etapa v7](eval-reports/2026-10-01-piano-detective.md); as [fontes e limitações de cobertura](catalog-metadata.md) distinguem obras de gravações. Usar v7 como baseline para novos experimentos, preservando julgamentos e relatórios históricos. Obter revisão humana/conjunto reservado; ampliar metadados somente com evidência por obra. A integração Accordion/Toggle Group/Skeleton foi concluída em `beb7569`; `HANDOFF_MAESTRI.md` preserva seu histórico. Autenticação e playlists na interface validadas com API real e duas contas; tokens somente em memória conforme ADR-0006, sem persistência de login após reload. Cache público compartilhado validado em SQLite conforme ADR-0015; PostgreSQL real ainda pendente. Favoritos possuem contrato próprio, backend/frontend e QA atuais validados; histórico exige contrato próprio. Fechar G1 e abstrações antes de ampliar integrações externas; preservar modo local sem custo. Personalização e gates completos seguem pendentes.
