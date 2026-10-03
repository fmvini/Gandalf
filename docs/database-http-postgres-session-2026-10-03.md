# HTTP/auth entre duas aplicações e PostgreSQL — 2026-10-03

## Resultado final — PASS real / exit0

Às **20:30:19–20:30:30 UTC**, executado exclusivamente o novo script Backend
congelado sobre **uma** PG descartável nova. **Nove checks PASS**, transporte
`ASGI_TWO_APPS_SINGLE_PROCESS`; 21 requests na app A e 23 na B. Hashes do script,
testes e agregado de 71 arquivos conferidos antes de criar recursos e ao final;
snapshot do gate permaneceu idêntico. Não houve alteração de fontes ou nova
execução dos gates PostgreSQL geral/auth, suites antigas ou build.

| Grupo aprovado pelo novo gate | Evidência |
|---|---|
| Duas apps offline | Lifespans/engines independentes, mesmo PG/JWT sintético |
| Register/login cruzados | Auth HTTP real ASGI, headers privados/request ID |
| Refresh/replay e famílias | Access novo consumido na app oposta; replay revoga somente a família correta |
| Logout atual/antigo/owner errado | Contrato token informado; JWT access segue válido até expiração |
| Origem e favorito compartilhados | Origem A consumida em B, snapshot e isolamento de owner |
| Origem e playlist compartilhadas | Snapshot/ordem das três faixas e isolamento de owner |
| SQL/ownership/cache | Contagens exatas e AI0 |
| Encerramento da app A | App B continua atendendo `/me` |
| Encerramento de ambas | Engines das duas apps e observer encerrados |

### SQL independente depois do gate

PostgreSQL **18.6 (Debian18.6-1.pgdg12+2)**, engine `postgresql`,
`READ COMMITTED`, role `gandalf_gate`, head `0008_favorites`, vector**0.8.6** e
citext**1.8**. Consulta adicional READ ONLY contra o DB HTTP próprio confirmou
exatamente os mesmos números do JSON Backend:

| Tabela/medida | Contagem |
|---|---:|
| users | 2 |
| favorites | 1 |
| playlists | 1 |
| playlist_tracks | 3 |
| recommendation_results | 1 |
| refresh_tokens | 8 |
| Não revogados | 1 |
| Não revogados expirados | 0 |
| AI calls | 0 |
| Outras conexões cliente no DB HTTP após lifespans | 0 |

`active_refresh_tokens` é o contador não revogado do Backend; a consulta
separada comprovou que nenhum desses tokens estava expirado. Não foram
publicados tokens, digests de tokens, emails, senhas, queries/DSNs ou corpos.

### Identidade, bloco CI e cleanup

- UUID da única instância: `553df499-8193-40f6-bf21-35b7c7e29b2c`.
  Nome `http-postgres-553df499819340f6bf2135b7c7e29b2c`; ID completo
  `b4737f568b6e015d9aca8038e571dfa868af68c16f9773edb2678768411a6be7`.
- Imagem oficial local/pullnever no digest abaixo, tmpfs512MiB, labels UUID,
  role/banco/env e bind `127.0.0.1:55432` conferidos antes do SQL e novamente
  imediatamente antes do `docker rm -f` exclusivamente desse ID.
- **Bloco CI literal PASS** no mesmo PG; SHA256 do body extraído do workflow:
  `c499192116142782a1f889e78be0d4cb2a10a4c095e68649b761b8e573f0ebe6`.
  Bootstrap `gandalf_gate_553df499819340f6bf2135b7c7e29b2c`;
  DB HTTP vazio criado `gandalf_gate_3cce88cc57004ea9936f2e04d12927e1`;
  DB auth criado `gandalf_gate_dd8174ad0c514956a19748c1d072a056`, **não testado**.
  Somente o DB HTTP recebeu migrations/fixtures do novo gate.
- Arquivo privado `GITHUB_ENV` removido no finally; diretório temporário
  vazio próprio removido. Container ausente por inspeção do ID e filtro UUID;
  `removed_identity_verified=true`, `cleanup.verified=true`, porta55432 livre.
  Nenhuma imagem/volume/serviço/dado existente removido ou reiniciado.
- Artefato final sanitizado UTF-8:
  `.impeccable/runtime/http-postgres-result-553df499-8193-40f6-bf21-35b7c7e29b2c.json`.
  SHA256: `7e7a16d0eca4bcc0ff2c5acb6c68c8efab32fc4b540566c73f4573c1abc92d81`.

### Freeze e limites

- Script: `e7137358431d4976b94e79a13c7cf38ebbb247a186cc8f76d8e71119e75d8d80`.
- Testes: `b9e2c9d07258df2f88d49cbe7f8185a167d5b605530bd9eb87c60a51b6afc0dc`.
- Agregado71 fontes: `b08d71a67ad5909f29124586a38db94177e38e3df48a9077a38cfc3208a5faa0`.
- Backend informou38 unit tests PASS/2,13s/1warning e Ruff/format PASS.
  São evidências separadas; este terminal não as duplicou.
- Aprovação local de **ASGI duas apps, processo único e PostgreSQL real**;
  não TCP/dois processos, rollout, mistura de versões, HTTPS ou CI hospedada.
  Nenhuma corrida controlada/suite auth anterior foi executada nesta unidade.
- **Reserva Banco congelada/liberada ao Maestro após este registro**; nenhum
  stage/commit/shared docs/Git/LLM/serviço existente alterado.

## Escopo coordenado

Backend mantém `api/scripts/postgres_http_gate.py`, seus testes e relatório.
Banco mantém este documento e o lifecycle ignorado
`.impeccable/runtime/http-postgres-lifecycle.py`. Maestro mantém CI, Git e
documentos compartilhados. Sem schema/model/migration nova, dados/serviços
existentes, `.env` real, fontes/LLM, build, instalação ou push.

Esta unidade valida duas apps ASGI/TestClient, lifespans e engines/pools
independentes sobre o mesmo PostgreSQL exclusivo. Não certifica TCP, dois
processos, Nginx, rollout/mistura de versões ou concorrência controlada de
logout/refresh. Os gates PostgreSQL geral/auth e a suíte SQLite anteriores não
são duplicados ou reexecutados.

## Contrato e isolamento

- Backend: `GANDALF_HTTP_PG_ALLOW=isolated-coordinated-backend-frozen` e
  `GANDALF_HTTP_PG_URL`; guards reaproveitados de `postgres_gate`:
  PostgreSQL/psycopg, loopback55432/55433, role `gandalf_gate`, DB
  `gandalf_gate_{32hex}` vazio, vector/citext disponíveis antes de migrar.
- Lifecycle: flag própria `GANDALF_HTTP_PG_LIFECYCLE_ALLOW` com o mesmo valor e
  `GANDALF_HTTP_PG_GATE_SHA256`, `GANDALF_HTTP_PG_TESTS_SHA256` e
  `GANDALF_HTTP_PG_SOURCE_SHA256` fornecidos após freeze. Confere hashes antes de
  criar recursos e antes/depois do script; o script verifica seu snapshot de
  fontes sem pin permanente. Antes do freeze só `--preflight` RO é permitido.
- **Uma** instância PG nova, imagem local/digest
  `pgvector/pgvector@sha256:2ba9ca5f2e7daa0f0e7723cba1ee9167bab54efd3640516a44ac1a928dd67e7a`,
  `--pull=never`, nome/labels UUID, tmpfs512MiB em `/var/lib/postgresql`, sem
  volumes/binds. 55432 ou55433 em127.0.0.1 precisa estar livre antes do run.
  PG existente5432 e dados/volumes/serviços reais não são alvos.
- Role de teste `gandalf_gate`, banco bootstrap UUID e senha aleatória; senha
  transmitida via ambiente filho, sem literal em argumentos/log. Docker
  config/env é capturado, comparado em memória e nunca impresso.
- ID completo, nome, labels, image ID/digest local, mounts, portas e role/banco
  são verificados antes de qualquer SQL/migration. Mesma identidade é
  reinspecionada antes de remover somente o ID próprio; sem prune/volumes ou
  operações gerais. Falha de identidade recusa remoção e deixa gate pendente.

## Adendo CI no mesmo container

Maestro autorizou executar **literalmente** o body Python de criação dos dois
bancos UUID vazio extraído do workflow frozen. O lifecycle extrai o único
heredoc que contém `GANDALF_AUTH_PG_URL` e `GANDALF_HTTP_PG_URL`, registra SHA256
e verifica que o body não mudou. Usa `GANDALF_PG_GATE_URL` do bootstrap próprio
e `GITHUB_ENV` em arquivo próprio temporário, sem publicar seu conteúdo.

O body conserva sua verificação de database/user, CREATE DATABASE com
Identifier e renderização das duas URLs. Importa as dependências em cwd vazio
e ambiente filho limpo com caminho de módulos explícito. Depois o lifecycle
verifica host/porta/role/senha e DBs UUID distintos em memória e usa somente
`GANDALF_HTTP_PG_URL` para executar o novo gate. O banco auth é criado mas não
testado; nenhuma segunda instância ou suíte auth é executada. O arquivo
GITHUB_ENV é removido no finally, mesmo quando o gate falha; a remoção do
container é tentada independentemente da limpeza desse arquivo.

Após PASS do novo script, SQL adicional **somente leitura**, contra o DB HTTP
próprio, confirma engine/identidade/versão/READ COMMITTED/head/extensões,
contagens exatas do JSON, AI0 e ausência de conexões cliente das duas apps
após seus lifespans. `active_refresh_tokens` segue a definição do script
(`revoked_at IS NULL`); adicionalmente exige zero não revogados expirados.
Nenhum token/digest de token, email, senha, query/DSN ou snapshot bruto integra
o artefato público.

## Preflight histórico — antes do freeze/live

Naquele checkpoint, a execução live estava **PENDENTE** aguardando Backend.
O resultado final acima substitui esse estado sem converter preflight em PASS.

Às **20:13:26–20:13:30 UTC**, preflight RO:

- Docker normal recusou acesso ao pipe Docker Desktop Linux; preflight elevado
  autorizado passou, Engine29.8.0/Linux.
- Imagem oficial local/digest esperado verificados. Nenhum container deste
  gate já existente; portas55432 e55433 livres por bind local exclusivo.
- Nenhum container criado, SQL/migration/teste/build executado; resultado
  `PREFLIGHT_PASS`, `integration_executed=false`, cleanup verified.
- Artefato sanitizado:
  `.impeccable/runtime/http-postgres-result-0af9c320-1df2-4297-ae20-646acbfedc9d.json`.

O código de lifecycle havia sido preparado, inclusive o adendo CI, mas ainda
não executado em modo live. Preflight não aprova HTTP/auth, persistência ou CI
hospedada; sua evidência continua separada do resultado final acima.

## Receita usada após freeze e continuidade

Foram confirmados SHA256 e contrato final com Backend e executado o lifecycle ignorado
com flag+hash em processo elevado quando o pipe exigir. Ele cria uma PG,
executa o bloco CI literal e exclusivamente `postgres_http_gate.py`, consulta
SQL RO final e limpa arquivo privado/container por identidade. JSON, versões,
contagens e cleanup estão registrados acima; reportar pelo CLI ao Maestro e
encerrar o turno, sem ask-back. Maestro serializa CI/docs compartilhados/Git.
Não repetir o gate aprovado sem mudança/falha nova; CI hospedada permanece
pendente e o lifecycle ignorado não compõe o artefato versionado do Backend.
