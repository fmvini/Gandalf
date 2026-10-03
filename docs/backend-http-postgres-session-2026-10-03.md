# Backend — duas apps HTTP ASGI / PostgreSQL — 2026-10-03

## Consolidação Maestro após execução Banco

O gate congelado foi executado por Banco em PostgreSQL 18.6 próprio: **PASS/exit0**, nove checks e 21 requests A/23 B, com SQL independente confirmando as contagens esperadas, head/extensões/READ COMMITTED e zero conexões cliente residuais. Fonte agregada inalterada, cleanup do container e remoção do arquivo privado confirmados. O bloco literal da CI também passou no mesmo container. [Evidência e limites](database-http-postgres-session-2026-10-03.md). Os resultados unitários e a entrega original do Backend abaixo são preservados; TCP/rollout não foram executados.

## Entrega e reserva

Implementados e congelados apenas `api/scripts/postgres_http_gate.py`, `api/tests/test_postgres_http_gate.py` e este relatório. Sem mudanças em produção, autenticação, schema, migrations, gates anteriores, CI, Git ou documentação compartilhada. Maestro serializa essas áreas; Banco executará o único gate PostgreSQL após freeze.

**38 testes focados PASS em 2,13s**, Ruff/format-check dos dois arquivos Python PASS. Essa evidência é de testes com fakes e SQLite temporário; **PostgreSQL real desta unidade ainda não executado pelo Backend**. Não confundir com ca-7, authgate PG ou aprovação TCP/multiprocessos.

## Contrato de execução

```powershell
$env:GANDALF_HTTP_PG_ALLOW = 'isolated-coordinated-backend-frozen'
# GANDALF_HTTP_PG_URL é fornecida só ao processo filho pelo Banco.
api/.venv/Scripts/python.exe api/scripts/postgres_http_gate.py
```

O allow específico é exigido antes de importar o runtime/criar engine; a função execute também o exige. Reutiliza `postgres_gate.validate_target`, `engine_for` e `validate_database`: DSN `postgresql+psycopg`, loopback127.0.0.1/localhost, porta55432/55433, usuário `gandalf_gate`, banco `gandalf_gate_<32hex>`, sem query de conexão. Banco coordena identidade UUID/container/porta livre/senha efêmera e cleanup, sem usar instância existente.

Antes de qualquer migration/escrita: conferir current_database/current_user, ausência de objetos do usuário e disponibilidade citext/vector. Migra `head` uma vez usando **a conexão verificada** em `Config.attributes['connection']`; não consulta DATABASE_URL/.env para Alembic. Confere head e extensões instaladas e READ COMMITTED. Não faz downgrade/drop, criação/remoção de container ou retries automáticos.

Imports de `app.main`/gate antigo ocorrem com cwd UUID vazio no workspace e ambiente de aplicação temporariamente removido: evita que o `app=create_app()` global leia `.env` real. Cwd/env são restaurados em finally; remove só o próprio diretório vazio com rmdir. As duas apps usam Settings(_env_file=None), mesmo DSN/JWT sintético, onlinefalse/booklocal/Groqempty/CORS[] e defaults auth15min/7dias/10reqmin explícitos. Não altera configuração global nem limites dos serviços existentes.

## Verificações novas

Nove checks públicos, executados por rotas/middleware/dependencies reais, sem override de rotas/DB/AuthService:

1. `independent_apps_offline`: engines/sessionmakers/limitadores distintos; status offline/readiness de ambas; READ COMMITTED nas conexões de ambas em PG.
2. `cross_app_register_login_headers`: cadastro A/login A, perfil B, outra conta B/perfil A; duplicate B409 e domínio reservado .test422, sem escrita parcial; headers no-store/pragma e request_id canônico nos endpoints auth.
3. `cross_app_refresh_replay_family_isolation`: refresh B e depois A; **access emitido B usado em /me A e access emitido A usado em /me B**, mesmo owner. Replay ancestral B401, descendente A401 e SQL zero ativos apenas nessa família; login independente continua utilizável.
4. `logout_current_old_foreign_contract`: logout token de outra conta204 não o revoga; logout ancestral consumido204 preserva filho; logout atual204/body vazio causa refresh na outra app401. Access anterior continua válido em /me, conforme contrato sem denylist.
5. `shared_origin_favorite_snapshot_ownership`: origem reading publicada por A, explicação igual por A/B; B salva favorito, A repete200/snapshot igual, outra conta não lista/status/exclui favorito alheio.
6. `shared_origin_playlist_snapshot_ownership`: B salva playlist da origem A; A lê snapshot/ordem, outra conta recebe404 em detail/delete e lista vazia.
7. `sql_ownership_cache_ai_zero`: observer independente confere owners/snapshots/posições/source IDs, cache persistido com TTL original sem renovação e contagens exatas; AI0.
8. `app_a_shutdown_preserves_b`: encerra lifespan A/dispose A; B continua autenticando o mesmo access.
9. `both_app_engines_disposed`: ambos engines encerrados uma vez; observer também encerrado em finally de execute, inclusive recusa/erro.

Requests abaixo dos limites auth existentes; não foi necessário aumentar rate limit. A limitação por app permanece explícita e não é interpretada como limite global distribuído. Não há corridas de serviço repetidas, barreiras concorrentes, restart, rollout, desativação/exclusão concorrente ou mistura de versões nesta unidade.

## Resultado público e SQL esperado

CLI: exatamente um JSON final stdout; exit0 somente PASS, exit1 NOT_PASSED. Erros contêm apenas status/stage fixo/error_class controlada, sem mensagem, DSN, email, token, headers, request/response body ou traceback. PASS é reconstruído: transport `ASGI_TWO_APPS_SINGLE_PROCESS`, nove checks fixos, contagens int estritas (bool rejeitado), requests a/b limitados, head, SHA agregado, source_unchanged e observer_disposed. Extras arbitrários não são refletidos.

Contagens para o fluxo atual: **users2/favorites1/playlists1/playlist_tracks3/recommendation_results1/refresh_tokens8/active_refresh_tokens1/ai_calls0**. O script permite tracks1–60, exigindo igualdade com o snapshot/ordem realmente retornados; o catálogo offline atual/reading15min produziu3 no teste SQLite. Famílias são distintas: replay encerra família1, logout encerra família2, família da outra conta mantém um token ativo. IDs/corpos das contas e refreshes ficam somente em memória, não no JSON final. Head atual esperado `0008_favorites`, verificado dinamicamente contra Alembic.

## Testes e reprodução

```powershell
# cwd api; plugin existente altera somente diretórios temporários/ACL.
$env:PYTHONPATH = '../.impeccable/runtime'
.venv/Scripts/python.exe -m pytest -q -p no:tmpdir -p no:cacheprovider -p maestro_pytest_temp --tb=short tests/test_postgres_http_gate.py
.venv/Scripts/python.exe -m ruff check scripts/postgres_http_gate.py tests/test_postgres_http_gate.py
.venv/Scripts/python.exe -m ruff format --check scripts/postgres_http_gate.py tests/test_postgres_http_gate.py
```

Primeira rodada:33 PASS/1 FAIL no cadastro HTTP com fixture example.test; serviços diretos do gate antigo não passam por EmailStr. Fixture corrigido para example.com, sem relaxar validação; o próprio fluxo agora comprova .test422. Rodada seguinte34 PASS. Após completar portabilidade dos novos access tokens e guards de URL/contagens/teardown: **38 PASS/1 warning**. Aviso conhecido Starlette/httpx TestClient, sem falha; nenhuma dependência alterada.

Fakes verificam alvo/preflight recusados antes de migration, conexão Alembic explícita, disposal após falha, freeze alterado não PASS, import cwd/env isolados e JSON sanitizado. Fluxo SQLite usa duas apps reais e schema migrado temporário; spy externa nunca chamado. Falha sintética do transporte de teste comprova fechamento de ambos lifespans, sem substituir DB/AuthService/rotas. Nenhuma suíte geral/gate antigo ou probe real repetido.

## Freeze para Banco/Maestro

- Script SHA256: `e7137358431d4976b94e79a13c7cf38ebbb247a186cc8f76d8e71119e75d8d80`.
- Testes SHA256: `b9e2c9d07258df2f88d49cbe7f8185a167d5b605530bd9eb87c60a51b6afc0dc`.
- `source_snapshot()` cobre71 arquivos explícitos: todos app/alembic Python, alembic.ini/pyproject, gate base e nova unidade script/test. Agregado JSON sort_keys SHA256: `b08d71a67ad5909f29124586a38db94177e38e3df48a9077a38cfc3208a5faa0`, comparado novamente antes PASS.
- AuthService preservado: `86ddfb61f7639433319bd40acb2f2890ccd74c241d37da7b14837275861577ed`; security: `78471d057a8440a1ed785214c1821cb73d461ebf96ba2f089a5ff479a59117f1`.

Próximo passo exclusivo Banco: executar **somente esse CLI** em uma PG descartável vazia com allow/DSN acima; registrar JSON, SHA fonte, identidade SQL e cleanup próprio. Não declarar live aprovado até seu resultado. ASGI cobre duas apps/engines no mesmo processo; sockets/TCP, múltiplos workers, load balancer, rollout e segurança integral permanecem fora dessa prova.
