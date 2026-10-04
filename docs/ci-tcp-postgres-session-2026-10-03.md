# CI — sessão TCP e PostgreSQL — 2026-10-03

## Entrega

O job PostgreSQL de `.github/workflows/ci.yml` cria agora bancos UUID vazios separados para auth, ASGI e TCP, além do banco inicial do gate geral. O bootstrap confirma identidade antes de escrever, escapa nomes com psycopg.sql.Identifier, usa connect_timeout5s/statement_timeout15s e publica URLs somente depois de criar todos os bancos. Não há tentativa de rollback de CREATE DATABASE autocommit; o serviço inteiro é descartável, inclusive em falhas.

Novo step executa `api/scripts/postgres_tcp_gate.py` com opt-in explícito e coleta somente `.impeccable/ci/postgres-tcp-gate.json` no artifact postgres-results. Bash preserva falhas via pipefail; upload usa always. O runner continua gerando JWT/tokens/senhas em memória; nenhuma credencial de produção foi adicionada ao workflow. As Actions e o digest PG não mudaram.

Ao iniciar, os terminais ainda exibiam o limite da sessão anterior; Maestro implementou e executou a unidade. Depois os três agentes voltaram a responder e concluíram revisões somente de leitura: Backend aprovou step/ALLOW/PYTHONPATH/isolamento; Banco confirmou bancos distintos, identidade antes de escrita, timeouts/autocommit e publicação; Frontend confirmou seleção dos artifacts e limites da prova HTTP. Sem achados concretos novos, edições, testes ou probes pelos revisores. A execução local permanece atribuída ao Maestro; a revisão não certifica Ubuntu/CI hospedada.

## Verificação

- Seis testes focados PASS em0,49s: executam literalmente o bootstrap com conexão fake e verificam bancos distintos, identidade errada sem escrita/publicação, falha parcial sem publicar URLs e step/artifact/opt-in. Sem rede/PostgreSQL ou import de app.main nos testes.
- Ruff/formatação do teste PASS; actionlint1.7.12 PASS no workflow final. Nenhuma suíte antiga, build, browser ou provider/LLM reexecutado.
- Prova local do trecho Python literal SHA256 `abbe8e738853a62323973d063b626dfc2962a73b0d18ddbc4dba7d32b320a46d` seguida exclusivamente do gate TCP PASS/exit0. Workflow congelado SHA256 `2c80c94139c93310ac729563b257ca7e7d999e05b774ca67838d871b895c67ba`; teste `2b1a24fcd414ec8e89ef4283600151c0e617b13788370ac97ee8e976936a077b`.

Execução em2026-10-04 02:33:07–02:33:37 UTC (2026-10-03 no Brasil), UUID `f819a195-4344-4d38-bf92-fa087f51676c`. Um PG18.6 local pullnever/tmpfs512MiB/loopback55432, container ID `13fa9153950d97ed202ffde5197fa67cc5ac85e9159fe23832a2268a7739904f`. Imagem oficial local `pgvector/pgvector@sha256:2ba9ca5f2e7daa0f0e7723cba1ee9167bab54efd3640516a44ac1a928dd67e7a`.

SQL READ ONLY verificou identidade/schema vazio dos três bancos novos e o mesmo server_id. O gate usou somente `gandalf_gate_f4f2476f823145778d5dce00f7719687`; os bancos auth/ASGI foram criados, mas seus gates não executados. As fontes75 do gate/worker permaneceram idênticas à entrega `c425c6c`, aggregate `c608200717b6aa6d615ff1b5506c0478017e1a0bb82e7aee68af6debd7d1fb52`; workflow/teste/lifecycle também inalterados durante a rodada.

Sete checks/30 requests TCP PASS: duas APIs identificadas por UUID/instância/PID, sessão em memória durante restart B sem login, refresh vigente aceito na nova B/access novo em A, snapshots/ownership/logout. SQL independente após shutdown confirmou READ COMMITTED/head0008_favorites/vector0.8.6/citext1.8, users2/favorites1/playlists1/tracks3/cache1/refresh4/não revogados1/AI0/expirados não revogados0/outras conexões cliente0.

Arquivo privado GITHUB_ENV removido antes do gate e container removido por ID/labels/imagem/mount/porta/env revalidados; verified/removed_identity_verified/porta55432 livre true. Serviços, volumes e dados existentes preservados. Artifact ignorado `.impeccable/runtime/tcp-postgres-ci-result-f819a195-4344-4d38-bf92-fa087f51676c.json`; resultado público normalizado em `.impeccable/ci/postgres-tcp-gate.json`. Nenhum DSN, token, email, senha ou SQL bruto publicado.

## Limites e continuidade

SHA256 do artifact de lifecycle: `0874ffcf61bdae30aaaa3b999bfc91d27b1facf687fc999e8bb8b33f16c666d4`.

Esta prova executa localmente o trecho literal Python e o gate novo, não o workflow inteiro nem Bash/tee/upload hospedados. Não comprova Ubuntu, instalação limpa, CI hospedada, browser multiupstream, rollout/mistura de versões, migrations concorrentes, HTTPS ou deploy remoto. Gates antigos continuam com suas evidências anteriores. Push somente por pedido explícito; depois verificar o job PostgreSQL e os quatro JSONs do artifact. Browser de mesma origem nginx com duas APIs/sessão contínua é a próxima unidade distinta.
