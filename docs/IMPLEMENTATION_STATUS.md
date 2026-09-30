# Estado da implementação — 2026-09-30

Este documento descreve o código atual. Os documentos numerados incluem o desenho completo do produto. Histórico e continuidade: [DEVELOPMENT_LOG](DEVELOPMENT_LOG.md).

## Execução

| Modo | Ativação | Comportamento |
|---|---|---|
| Local | `start-local.ps1` ou `python local.py` | SQLite, 18 livros e 25 músicas, ranking determinístico `local-rules-v4`; sem chamadas externas após instalar dependências |
| Online experimental | `start-local.ps1 -Online` ou `GANDALF_ONLINE=1` ao executar `local.py` | Open Library, MusicBrainz, catálogo local; Groq opcional interpreta e pontua candidatos; fallback por regras |
| API configurada diretamente | `uvicorn app.main:app` em `api/` | `ONLINE_CATALOG` e `BOOK_PROVIDER` definem o comportamento |

`local.py` aplica migrações e mantém SQLite/segredo em `api/.local`. No modo offline ignora `.env`; no online lê `api/.env`, mantendo banco e segredo locais. O modo online é opcional. Seu limite interno de chamadas não consulta nem controla faturamento do fornecedor, portanto não garante custo zero de uma conta externa. Esta reconciliação não ativa integrações nem altera configurações do usuário.

## Entregas verificadas

| Área | Implementado | Pendências |
|---|---|---|
| API | FastAPI, erros padronizados, CORS, request ID, health/readiness, configuração tipada | CI e mypy não integrados |
| Banco | SQLAlchemy, migrações 0001–0005, contas, catálogo/cache, cota diária de IA | SQLite testado; PostgreSQL/pgvector e concorrência entre processos pendentes |
| Auth | Registro, login, JWT, refresh rotativo, logout, `/auth/me` | Tela de conta; rate limiting compartilhado |
| Livros | Busca/detalhe local e Open Library, cache persistente, busca híbrida online | Metadados incompletos; sem embeddings |
| Música | Busca/detalhe local e MusicBrainz, UUID/MBID, duração opcional, cache persistente | Escolha final/licenças/cobertura de G1; interface abstrata musical |
| IA | Groq com schemas validados, timeout, cache e limite diário persistido | Não segue integralmente ADR-0002: IA também pontua; sem embeddings ou avaliação real no corpus |
| Descoberta | Três fluxos públicos, filtros, exclusões, referências por título, diversidade e explicações | Personalização e persistência de recomendações |
| Leitura | Cinco modos, preferência vocal e duração-alvo com indicação de estimativa; CALM desempata por atmosfera ambiental, com avaliação v4 sem regressões | Avaliação CINEMATIC; playlists persistentes |
| Interface | Home, música/livros/leitura, ajustes, temas, responsividade, loading/erro/vazio | Login, histórico, salvos, feedback, perfil |
| Qualidade | 152 testes backend, testes frontend, corpus de 45 consultas e baselines K=5/10 | Julgamentos do assistente, sem revisão humana independente ou conjunto reservado |

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
- **G6 aberto:** sem CI, auditoria final ou deploy público.

Continuar por diferenciação FOCUS/CALM/CINEMATIC com critérios explícitos e comparação contra os dois baselines. Depois revisar baixa precisão/cobertura e obter revisão humana/conjunto reservado. Fechar G1 e abstrações antes de ampliar integrações externas; preservar modo local sem custo. Após os gates aplicáveis, avançar para persistência, auth na interface e personalização conforme roadmap.
