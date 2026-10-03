# Integração contínua

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). Configurado em 2026-10-01 para pull requests destinados a `main`, pushes em `main` e execução manual pelo GitHub Actions. Esta implementação não faz deploy nem altera proteção de branch.

## Checks implementados

| Job | Ambiente | Verificações |
| --- | --- | --- |
| `API e ranking local` | Ubuntu 24.04, Python 3.12 | Instalação da API com ferramentas de desenvolvimento, Ruff/lint e formatação, pytest com SQLite/provedores simulados, comparação estrita K=5/10 contra v7 |
| `PostgreSQL e pgvector reais` | Ubuntu 24.04, Python 3.12, pgvector 0.8.6/PostgreSQL 18 | `scripts/postgres_gate.py`: migrations/favoritos/cache/round-trip; `scripts/postgres_auth_gate.py`: constraints/digests e concorrência; `scripts/postgres_http_gate.py`: endpoints entre duas apps ASGI/engines independentes, JWT/refresh/replay/logout e snapshots por proprietário. Cada gate usa banco vazio próprio |
| `Build e fluxos públicos` | Ubuntu 24.04, Node 24, Python 3.12, Chromium | `npm ci`, instalação do Chromium/bibliotecas, TypeScript/build e `npm test` conforme o script versionado do frontend |
| `Nginx, API e PostgreSQL integrados` | Ubuntu 24.04, Python 3.12, Node 24, Docker Compose e Chromium | Constrói Dockerfiles do checkout, combina Compose base/overlay PG/overlay descartável, testa interface estática sem Vite/mocks, confirma migrations/dados por SQL e persistência após reiniciar a API |

Os testes de navegador usam respostas simuladas e uma API real iniciada pelo E2E com SQLite temporário. `GANDALF_PYTHON=python` aponta para o Python preparado pela Action; não depende de uma `.venv` previamente criada no runner. `GANDALF_ONLINE=0` mantém essa API no modo local. `frontend/tests/live.mjs` é um E2E com API local, apesar do nome; não é uma avaliação real de Open Library, MusicBrainz ou Groq.

A instalação requer rede para dependências, Actions e navegador. Os testes usam catálogo local e HTTP simulado, sem chaves de provedores, conta de IA ou dados de produção. Nenhum segredo de `.env` é usado pela configuração da CI.

O job integrado usa `GANDALF_DEPLOYMENT_ALLOW=isolated-coordinated` e `python scripts/deployment_gate.py`. A imagem PG é baixada pelo digest acima do gate; API/frontend são construídos pelos Dockerfiles reais. Dependências de build exigem rede. Os containers usam bridge exclusiva do projeto; `internal: true` suprimiu os bindings publicados no Docker 29.8 local e foi recusado para esse gate host. Providers/IA ficam offline, sem chave Groq; o browser bloqueia requisições externas e SQL exige zero chamadas IA, sem alegar firewall de egress. O runner escolhe projeto/banco/credenciais/portas exclusivos, substitui `env_file` e volumes persistentes do Compose, valida configuração efetiva e identidade antes das operações e remove somente recursos próprios. O navegador testa o proxy `/api/v1` do Nginx, rotas SPA e dados por conta; as fases `create`/`verify` são separadas por um reinício real da API. SQL verifica engine PostgreSQL, head Alembic, extensões e snapshots antes/depois. Não executa o teste contra serviços existentes.

O job PostgreSQL usa a imagem oficial fixada no digest testado localmente, tmpfs e publicação somente em `127.0.0.1:55432`; usuário/banco e senha públicos de teste pertencem exclusivamente ao serviço novo dessa execução. Não usa compose/volumes existentes. O script exige `GANDALF_PG_GATE_ALLOW=isolated-coordinated`, URL loopback/porta55432 ou55433/usuário `gandalf_gate`/banco `gandalf_gate_{32hex}`, identidade correspondente, schema vazio e extensões disponíveis antes de qualquer migration. Não executar contra banco de desenvolvimento/produção. O serviço é descartado pelo runner ao terminar o job, inclusive falhas. Networking/healthcheck seguem a [documentação oficial de serviços PostgreSQL](https://docs.github.com/en/actions/tutorials/use-containerized-services/create-postgresql-service-containers); imagem/extensão são do [projeto pgvector](https://github.com/pgvector/pgvector).

O resultado final PASS/NOT_PASSED é JSON em stdout; progresso fica em stderr, sem DSN/senha/SQL. Shell Bash com `pipefail` conserva falha do script ao coletar com `tee`; nenhum PASS parcial. Guards/import não substituem execução real. A suíte SQLite continua separada: exportar DATABASE_URL não a converte para PostgreSQL.

O gate auth exige `GANDALF_AUTH_PG_ALLOW=isolated-coordinated-backend-frozen` e `GANDALF_AUTH_PG_URL`, reutilizando os mesmos guards de destino/identidade/schema vazio. A CI cria um segundo banco `gandalf_gate_{UUID}` no mesmo serviço descartável, com nome escapado por `psycopg.sql.Identifier`; não reaproveita o schema migrado pelo gate geral. O script fotografa hashes das fontes no início/fim, recusando mudanças durante a execução sem fixar uma revisão eterna. Usa AuthService real e sessões independentes em READ COMMITTED: barreira antes do commit e `pg_blocking_pids` comprovam a espera na corrida ancestral/descendente. Sem bloqueio observado ou com qualquer refresh ativo após replay, o gate falha.

O gate de endpoints exige `GANDALF_HTTP_PG_ALLOW=isolated-coordinated-backend-frozen` e `GANDALF_HTTP_PG_URL`. O mesmo bloco da CI cria um terceiro banco UUID vazio, com os guards de destino/identidade/extensões existentes e migrations serializadas antes das aplicações. Duas factories e lifespans reais usam engines independentes, o mesmo banco e JWT sintético, catálogo local e IA sem chave. TestClient percorre rotas, middleware, schemas e sessões SQL sem overrides: cadastro/login numa aplicação, sessão/refresh na outra, replay e logout conforme o contrato atual, favoritos/playlists com origem pública compartilhada e isolamento entre duas contas. SQL, headers, disposal dos engines e snapshot das fontes são verificados. O transporte é ASGI em um processo; não há TCP entre processos, navegador novo, balanceador ou rollout nessa prova. Não repetir o gate de concorrência para inferir essa cobertura.

Os jobs falham se algum check falhar, sem retry que esconda perdas. A comparação usa `--fail-on-case-regression`: perdas individuais também bloqueiam, mesmo que as médias não caiam. Baselines atuais: `docs/eval-reports/local-v7-piano-detective-k5.json` e `local-v7-piano-detective-k10.json`. Atualizá-los exige uma etapa de ranking validada e documentada; não regenerá-los automaticamente na CI.

## Resultados e diagnóstico

- `api-results`: relatório JUnit do pytest e relatórios JSON K=5/10, quando gerados.
- `frontend-screenshots`: somente PNGs de `.impeccable/review/`, quando gerados pelos testes.
- `postgres-results`: JSONs finais `postgres-gate.json`, `postgres-auth-gate.json` e `postgres-http-gate.json`, com versões/checks/hashes/etapa segura, sem credenciais/banco bruto.
- `deployment-results`: `deployment-gate.json`, resultado final sanitizado do teste integrado, incluindo checks e limpeza. Sem tokens, emails, senha, DSN ou dados brutos do banco.
- Os artefatos são coletados mesmo após falha e retidos por sete dias. Se uma etapa anterior impedir sua geração, o upload avisa; o check que falhou permanece vermelho.
- Logs das etapas ficam no run do GitHub Actions. Não há upload de `.env`, banco, segredo JWT ou da pasta `.impeccable/` inteira.
- Uma execução nova do mesmo workflow/ref cancela a anterior. Limites: dez minutos para API/PostgreSQL, quinze para build/E2E e vinte para integração Docker.

## Dependências do workflow

Actions fixadas por SHA completo, com versão em comentário. Os hashes foram conferidos pela API oficial do GitHub contra estes releases:

| Action | Release |
| --- | --- |
| `actions/checkout` | [v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1) |
| `actions/setup-python` | [v7.0.0](https://github.com/actions/setup-python/releases/tag/v7.0.0) |
| `actions/setup-node` | [v7.0.0](https://github.com/actions/setup-node/releases/tag/v7.0.0) |
| `actions/upload-artifact` | [v7.0.1](https://github.com/actions/upload-artifact/releases/tag/v7.0.1) |

`contents: read` é a permissão do token; checkout não mantém credenciais para os comandos posteriores. Referência para revisar essas escolhas: [segurança de Actions](https://docs.github.com/en/actions/reference/security/secure-use). A instalação do navegador segue a [documentação de CI do Playwright](https://playwright.dev/docs/ci).

Node instala pelo `frontend/package-lock.json`. Python instala as faixas de versões do `api/pyproject.toml`; ainda não há lock de dependências Python. Os caches são de pip/npm, invalidados pelos respectivos arquivos; não reutilizam `.venv`, banco ou `node_modules`.

## Validação realizada e próximos passos

Em 2026-10-03, o novo gate de endpoints passou no PostgreSQL 18.6 exclusivo: **PASS/exit0**, nove checks e 44 requests entre duas apps ASGI, engines independentes e o mesmo banco/JWT sintético. SQL independente confirmou head `0008_favorites`, vector0.8.6/citext1.8, duas contas/um favorito/uma playlist de três faixas/um cache/oito refreshes (um ativo), AI0 e zero conexões cliente após teardown. O bloco literal da CI criou os bancos UUID separados no mesmo container; somente o gate novo foi executado. Fonte e cleanup verificados, arquivo privado removido. 38 testes focados/Ruff/formatação e actionlint passaram. [Relatório Banco](database-http-postgres-session-2026-10-03.md), [Backend](backend-http-postgres-session-2026-10-03.md) e [revisão Frontend](frontend-http-postgres-session-2026-10-03.md) distinguem essa prova de TCP/rollout/browser.

Em 2026-10-03, o job integrado foi validado localmente pelo mesmo runner versionado: **PASS/exit0**, imagens API/frontend atuais, Nginx/Chromium reais e PostgreSQL18.6/pgvector0.8.6/citext1.8/head0008. Create/verify, ownership, refresh/logout/revogação e restart da mesma API passaram; SQL confirmou2 contas/2 favoritos/1 playlist11 faixas/3 caches com fingerprints idênticos antes/depois/verify e AI0. Sourcefreeze/cleanup PASS;94 guards runner,67 Node e38 startup Backend aprovados, Ruff/format98/actionlint PASS. Detalhes, CA BuildKit opcional, observação Chromium204 e limites em [deployment-integration.md](deployment-integration.md). Isso não certifica o runner Ubuntu hospedado nem o destino público.

Em 2026-10-02, após corrigir a corrida de replay, Maestro executou o **script auth versionado** em uma nova instância exclusiva PostgreSQL18.6: os quatro grupos passaram, incluindo seis constraints negativas, mesmo-token200/401/zero ativos e ancestral rotação200/replay401/bloqueio observado/zero ativos. O trecho Python de criação do banco vazio da CI foi executado literalmente nessa instância e passou. 20 testes offline do gate, 12 recusas CLI, Ruff/formatação e actionlint passaram. Container removido após identidade verificada; nenhum serviço/dado existente alterado pelo gate. Relatório: [auditoria auth Banco](database-auth-session-2026-10-02.md). Essa evidência local não certifica o runner hospedado.

Em 2026-10-02, Docker Desktop/Engine Linux autorizado pelo usuário: gate real aprovado em PostgreSQL18.6/pgvector0.8.6/citext1.8, no harness e no script versionado reexecutado sobre banco vazio. Os 17 testes de proteção passaram, assim como Ruff e actionlint1.7.12 no novo workflow. Container exclusivo com tmpfs foi removido após conferência de ID/label, sem tocar servidores/volumes existentes. Evidências/limites em `docs/database-docker-session-2026-10-02.md`; isso não substitui a execução hospedada abaixo.

O YAML passou no [actionlint v1.7.12](https://github.com/rhysd/actionlint/releases/tag/v1.7.12), baixado da fonte oficial com SHA-256 conferido. No Windows, os comandos de Ruff/formatação passaram, 220 testes da API geraram JUnit e os gates K=5/10 contra v7 passaram sem perdas ou mudança de catálogo. `npm run build` e `npm test` (smoke, componentes e E2E com API real) passaram no checkout após a integração de UI `beb7569`, usando as variáveis da CI.

O teste de carregamento responsivo espera o layout se ajustar após mudar viewport/tema antes de verificar overflow. A espera é limitada pelo timeout do Playwright e continua falhando se houver overflow persistente. Na unidade auth posterior, testes de estado, browser auth/continuation, live com SQLite temporário e build também passaram; evidências e limites em [relatório Frontend](frontend-auth-session-2026-10-02.md).

**Ainda não há execução validada no runner hospedado.** O workflow está preparado para um futuro push autorizado; não foi enviado automaticamente. Depois desse envio, verificar os quatro jobs e os artefatos. Ubuntu, instalação limpa de dependências, build Docker e bibliotecas do Chromium precisam dessa confirmação remota.

O gate G6 permanece aberto: CI hospedada verde, auditoria final e deploy público não estão concluídos. O job cobre apenas os cenários PostgreSQL descritos acima; HTTP TCP entre processos, stress multiprocessos auth, corrida logout/refresh/desativação/exclusão, falhas reais de commit PG, demais constraints, rollout pré-populado/mistura de versões, mypy e avaliações online reais continuam fora de sua cobertura. O exemplo mais amplo de `docs/11-deployment-guide.md` continua um desenho futuro.
