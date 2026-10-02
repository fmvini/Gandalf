# Backend — sessão de 2026-10-02

## Implementado

- Revisão do WIP de favoritos sobre HEAD `bfa418b`, sem novos bloqueadores; autenticação/ownership, snapshot inicial, upsert no-op com RETURNING, rollback/503, independência da origem nas leituras/exclusões conferidos. Banco confirmou auditoria independente. Validação integral anterior (346 testes em 2026-10-01) é histórica; hoje não afirmar concorrência aprovada onde o sandbox impediu os workers.
- Re-roll de música aceita `excluded_music_ids` cumulativos (até 200 UUIDs) e offset 0–300, preservando query/filtros/limit. Livros mantém `excluded_book_ids`. Vistos efêmeros, sem modelos/migrações/histórico/feedback.
- Ambos retornam has_more/next_offset; próxima página externa avança 15 somente até 300, ou existe um extra aceito após relevância/filtros/diversidade. Avisos, candidatos rejeitados e páginas fora do orçamento não contam como disponibilidade. Offline usa exclusões, sem fatiar catálogo por offset. Deduplicação online por UUID e título/autoria; máximo dois itens por criador no batch. Query/filtros/exclusões reaplicados na IA e no fallback.
- Uma página por termo, até dois termos; até 25 candidatos, classificação de até limit+1 no mesmo pedido IA, sem mais chamadas/cota. Fonte insuficiente pode gerar vazio/degradado identificado; não inventa metadados. Trilha continua em generate_soundtrack/online_soundtrack.py, sem alteração de duração/paginação.
- Contrato combinado por `maestri ask Frontend`; Frontend possui frontend/** e implementa manutenção da lista/espera/cancelamento/erro/esgotamento, snapshot/login/vistos/offset. Sua entrega e E2E são separados.

## Arquivos principais alterados

Unidade **favoritos anterior** (10 arquivos, ainda WIP):

- `api/app/main.py`
- `api/app/services/auth_service.py`
- `api/app/routes/favorites.py`
- `api/app/schemas/favorite.py`
- `api/app/services/favorite_service.py`
- `api/tests/test_favorites.py`
- `api/README.md`
- `docs/05-API-Specification.md`
- `docs/adr/0016-owner-scoped-favorites.md`
- `docs/adr/README.md`

Unidade **re-roll desta sessão** (9 arquivos):

- `api/app/schemas/recommendation.py`
- `api/app/routes/recommendations.py`
- `api/app/services/recommendation_service.py`
- `api/app/services/online_recommendations.py`
- `api/tests/test_reroll.py`
- `api/README.md`
- `docs/05-API-Specification.md`
- `docs/adr/0017-ephemeral-discovery-reroll.md`
- `docs/adr/README.md`

Este relatório é o décimo arquivo da unidade re-roll/diagnóstico. README/Spec/índice ADR contêm alterações das duas unidades: primeiro registrar os hunks de favoritos, depois re-roll. Snapshot pré-re-roll preservado em `.impeccable/runtime/favorites-backend-20261002.patch` (ignorado, 44.827 bytes). Maestro reserva `docs/DEVELOPMENT_LOG.md`, `docs/CONTINUATION.md`, `docs/IMPLEMENTATION_STATUS.md` e consolidação dos commits. Banco reserva modelos/migrações/test_migrations e docs04; não foram editados pelo Backend.

## Decisões técnicas

- Espelhar o contrato público de livros com schema musical específico, proibindo campos adicionais e UUIDs/limites inválidos. Preservar IDs retornados pelos serviços, inclusive reconciliação de IDs legados do catálogo por provider/external_id; não recalcular antigos.
- has_more representa amostra limitada, sem promessa de todo o catálogo mundial. O cliente mantém offset quando next_offset=null e para sem truncar vistos ao atingir 200. Deduplicação por título/autoria é por amostra, não entre batches com UUIDs diferentes.
- Cache Groq mantém Intent/Selection por hash durante 24 horas, inclusive temas/referências. Distinto do cache de origem de uma hora sem query/parsed_query e dos UUIDs vistos no cliente. Nenhuma alteração de provider/modelo/chave/licença/cota.
- Plugin temporário do Maestro substitui apenas fixture tmp_path por mkdir com permissões herdadas; desabilita tmpdir/cacheprovider para contornar mkdir modo700 incompatível com SID restrito Windows. Não altera aplicação ou asserções. ProcessPoolExecutor segue bloqueado por named pipe no sandbox.

## Estado atual e evidências

### Testes simulados/local

Executados de `api/` com `.venv/Scripts/python.exe`; nenhum usa fonte online real:

```powershell
$env:PYTHONPATH = '../.impeccable/runtime'
.\.venv\Scripts\python.exe -m pytest -q -p no:tmpdir -p no:cacheprovider -p maestro_pytest_temp --tb=short tests/test_reroll.py tests/test_continuation.py tests/test_recommendations.py tests/test_online.py tests/test_music_filters.py tests/test_books.py
```

- **185 passed**, 26,27 s, na versão inicial de test_reroll com 18 casos. Contém provedores fakes/HTTP MockTransport, cache por página/reinício, filtros/IA/fallback e os gates de duração online simulada.
- Após adicionar dois casos de último batch contendo somente IDs vistos (MUSIC/BOOK), Maestro executou a suíte completa: **361 passed, 3 failed, 1 warning**, 69,87 s, 364 coletados (coleta anterior aos dois extras). Todos os três failed foram `WinError 5` ao abrir named pipe do ProcessPoolExecutor antes dos workers: dois de favoritos e um de cache. Não são casos aprovados e exigem runner que permita subprocessos.
- Com liberação do Maestro após a suíte, corrigidos apenas C408/literal equivalente e formatação do fake/teste; comando pytest acima apenas com `tests/test_reroll.py`: **20 passed**, 1,29 s. Inclui UUID/offset/limites inválidos, cumulatividade, local/offline, batch só vistos, offset300 sem excedente, falha IA/fonte, filtros/diversidade, dedup e limite200. Nenhuma asserção relaxada.
- Ruff final: `python -m ruff check .` → **All checks passed**; `python -m ruff format --check .` → **83 files already formatted**. Favorites review inicial também passou com 82 arquivos, antes do teste novo.
- Único warning final: StarletteDeprecationWarning do testclient/httpx; dependências não alteradas incidentalmente.

Gates executados de `api/`, sem alterar baselines:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.runner --k 5 --baseline ../docs/eval-reports/local-v7-piano-detective-k5.json --fail-on-case-regression --output ../.impeccable/runtime/backend-reroll-k5-20261002.json
.\.venv\Scripts\python.exe -m app.evaluation.runner --k 10 --baseline ../docs/eval-reports/local-v7-piano-detective-k10.json --fail-on-case-regression --output ../.impeccable/runtime/backend-reroll-k10-20261002.json
```

Ambos **PASS**: ranking local-rules-v7 preservado, catalog_changed=false, case_changes=[], regressions=[], case_regressions_count=0. Baselines permanecem intactos.

### Runtime e verificação externa limitada

Maestro constatou ausência de listeners em 8000/5173 antes da ativação. Start-Process com WindowStyle Hidden falhou por chaves de ambiente duplicadas Path/PATH; não é falha de credenciais. Com autorização explícita, a única API foi iniciada diretamente:

```powershell
# De api/, processo mantido em sessão exec; não iniciar outro se já houver listener.
$env:GANDALF_ONLINE = '1'
.\.venv\Scripts\python.exe local.py
```

- **PID 37452**, sessão exec 27472, Uvicorn em `127.0.0.1:8000`, mantido. Nenhum processo existente encerrado. local.py usa banco `.local/gandalf.db`, migra somente esse banco; configurações online/chaves existentes carregadas sem exposição/modificação. `Start-Process` não criou outra API.
- GET `/api/v1/system/status` **200**: catalog=online, Groq configured=true, model=`openai/gpt-oss-20b`, GPU=false. Configured indica presença de configuração, não conectividade/validade da chave. GET `/health/ready` **200**: database/schema ok, pgvector not_required (SQLite). Maestro confirmou ambos independentemente.
- GET `/api/v1/books/search?q=O+Hobbit&limit=3` **200**, um item provider=local: resposta híbrida/fallback, **não comprova Open Library real**. GET `/api/v1/music/search?q=GoGo+Penguin&limit=3` **503 MUSIC_PROVIDER_UNAVAILABLE**.
- Diagnóstico direto, uma tentativa OpenLibrary.search('The Hobbit',3) e uma MusicBrainz.search('GoGo Penguin',3), sem fallback/cache para este diagnóstico: respectivamente **502 UPSTREAM_ERROR** e **503 MUSIC_PROVIDER_UNAVAILABLE**. Ambas com cadeia ConnectError → ConnectionRefusedError, errno22/WinError1225, antes de resposta HTTP. Não confundir recusa de transporte deste ambiente com resposta do provedor ou indisponibilidade global.
- Groq: **uma interpretação** via GroqClient.interpret('Músicas calmas para estudar','music'), usando OnlineStore/banco/cota existentes e observador de status HTTP, sem imprimir corpos/headers. Resultado **503 AI_UNAVAILABLE**, causa ConnectError, nenhuma resposta HTTP. Contador UTC diário **0→1**, limite **50 inalterado**, sem cache hit. Nenhum segundo probe/retry manual/selection Groq foi realizado. Não há evidência de chave inválida, cota remota ou incompatibilidade de modelo; **não há motivo técnico para pedir chave nova**.
- Probes cessaram após confirmação de falha de transporte. Não foram expostos api/.env, Authorization, respostas upstream ou segredos. Saída registrada aqui é sanitizada; logs de requisição da API mostram apenas método/caminho/status/duração/request_id. Execução real de re-roll completo com LLM/fontes **não validada** nesta sessão; testes com fakes são a evidência funcional atual.

### Git e pendências

HEAD continua `bfa418b`; favoritos/re-roll não receberam commit. Maestro tentou git add seletivo e recebeu index.lock Permission denied (`.git` somente leitura). Nenhum push. Também não declarar frontend concluído: npm/esbuild/Playwright e rede são gates próprios do Frontend/Maestro. PostgreSQL real permanece pendente de daemon/auth/pgvector, conforme relatório do Banco.

## Próximos passos

- Maestro consolidar estes resultados em seus documentos reservados e serializar commits locais em ambiente com escrita Git: favoritos primeiro (10 arquivos/hunks do patch pré-re-roll), depois re-roll/backend docs (lista acima); revisar git diff seletivo e excluir frontend/modelos/docs de outros agentes.
- Frontend concluir re-roll musical e validar lista preservada em loading/cancel/erro/fim, snapshot submetido, login, filtros/UUIDs cumulativos/offset, sem novas buscas invisíveis nem truncar IDs. E2E/build bloqueados precisam runner que permita esbuild/Chromium; preservar asserções.
- Reexecutar três testes multiprocessos bloqueados em runner com named pipes permitidos. Não marcar concorrência hoje como aprovada a partir dos demais testes locais.
- Resolver transporte de rede do ambiente sem trocar chave/provider/model/cota; depois fazer amostra real limitada MUSIC/BOOK com re-roll e `meta.sources/ai_used/degraded`, preservando API/cota/cache. Qualquer erro HTTP real Groq que exija credencial deve ser comunicado ao Maestro com status/código sanitizados antes de alterar.
- Banco validar migrações/cache/favoritos em PostgreSQL/pgvector descartável; não usar SQLite/status200 para encerrar esse gate.
