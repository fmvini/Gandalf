# Estado da implementação — 2026-10-01

> **Checkpoint de 2026-10-01:** v7 de piano/detetive validado e preservado no commit `f120676`: 220 testes backend, Ruff/formatação e comparação estrita K=5/10 contra v6 sem perdas. A continuação de UI concluiu Accordion/Toggle Group/Skeleton e explicações compartilhadas; build, smoke, testes de componentes e E2E com API real passaram na árvore atual. Desktop 1440 px e mobile 390/320 px revisados nos dois temas, com contraste dos filtros e movimento reduzido verificados. Histórico em [HANDOFF_MAESTRI.md](HANDOFF_MAESTRI.md) e no log.

A matriz abaixo descreve as etapas validadas até v7. Os documentos numerados incluem o desenho completo do produto. Histórico e continuidade: [DEVELOPMENT_LOG](DEVELOPMENT_LOG.md) e [CONTINUATION](CONTINUATION.md).

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
| Banco | SQLAlchemy, migrações 0001–0005, contas, catálogo/cache, cota diária de IA | SQLite testado; PostgreSQL/pgvector e concorrência entre processos pendentes |
| Auth | Registro, login, JWT, refresh rotativo, logout, `/auth/me`; telas `/register`, `/login` e `/account`, sessão em memória e renovação concorrente segura | Recuperação de senha, edição de conta; rate limiting compartilhado |
| Livros | Busca/detalhe local e Open Library, cache persistente, busca híbrida online | Metadados incompletos; sem embeddings |
| Música | Busca/detalhe local e MusicBrainz, UUID/MBID, duração opcional, cache persistente | Escolha final/licenças/cobertura de G1; interface abstrata musical |
| IA | Groq com schemas validados, timeout, cache e limite diário persistido | Não segue integralmente ADR-0002: IA também pontua; sem embeddings ou avaliação real no corpus |
| Descoberta | Três fluxos públicos, filtros, exclusões, referências por título, diversidade e explicações; livros locais priorizam gêneros explícitos em empates; piano/detetive com fontes por obra e fallback online testado sem IA | Cobertura parcial de instrumentos/subgêneros; personalização e persistência de recomendações |
| Leitura | Cinco modos, preferência vocal e duração-alvo estimada; CALM favorece atmosfera e CINEMATIC favorece diversidade/etiqueta cinematográfica em empates, com avaliação v4/v5 | Revisão humana da diferenciação; playlists persistentes |
| Interface | Home imersiva, três fluxos, temas; Accordion Radix em filtros/explicações, Toggle Group com limpeza e filtros submetidos, Skeletons acessíveis nos carregamentos; explicações lazy/cache/retry inclusive nas trilhas; cadastro/login/dados da conta/logout | Histórico, salvos, feedback, perfil de preferências |
| Qualidade | 220 testes backend, smoke/componentes/auth/E2E frontend com cadastro e revogação reais; corpus de 45 consultas, baselines v3–v7 K=5/10 e comparação por caso com gate estrito opcional | Julgamentos do assistente, sem revisão humana independente ou conjunto reservado |

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

Piano/detetive foram validados na [etapa v7](eval-reports/2026-10-01-piano-detective.md); as [fontes e limitações de cobertura](catalog-metadata.md) distinguem obras de gravações. Usar v7 como baseline para novos experimentos, preservando julgamentos e relatórios históricos. Obter revisão humana/conjunto reservado; ampliar metadados somente com evidência por obra. A integração Accordion/Toggle Group/Skeleton foi concluída em `beb7569`; `HANDOFF_MAESTRI.md` preserva seu histórico. Autenticação na interface agora validada com API real e testes de sessão; tokens somente em memória conforme ADR-0006, sem persistência de login após reload. Fechar G1 e abstrações antes de ampliar integrações externas; preservar modo local sem custo. Após os gates aplicáveis, avançar para playlists/salvos persistentes e personalização conforme roadmap.
