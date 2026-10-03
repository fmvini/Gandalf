# Duas APIs TCP e PostgreSQL descartável — 2026-10-03

## Resultado final — PASS pelo Maestro

Banco preparou o lifecycle abaixo e atingiu o limite de uso. Maestro assumiu o contrato JSON e a execução, com os agentes parados. O preparo original permanece como histórico; não constitui revisão independente do resultado final.

- PASS/exit0 em23:38:52–23:39:06 UTC, UUID `4328bd8e-e2fa-492f-b8f1-016fcb8394d2`. Um PG local pullnever/tmpfs512MiB/loopback55432, ID `3c56f421c969426132c07b423633ba862f75de279d3d0b91ed3805aeead8f832`, digest oficial indicado abaixo.
- Duas APIs TCP próprias; B reiniciada manteve o mesmo par do cliente e renovou refresh sem login. Sete checks, requests A11/B11/B reiniciada8; configuração offline por HTTP nas três instâncias, snapshots preservados e fonte75 inalterada.
- SQL independente READ ONLY: PG18.6/READ COMMITTED/head0008_favorites/vector0.8.6/citext1.8; users2/favorites1/playlists1/tracks3/cache1/refresh4/não revogados1/AI0/expirados não revogados0/outras conexões cliente0. Contagens iguais ao gate.
- Processos/lifespans encerrados; PG removido somente após revalidar ID/labels/imagem/mount/porta/env. Container ausente e55432 livre; cleanup verified/removed_identity_verified true. Serviços/dados existentes preservados.
- Artifact ignorado `.impeccable/runtime/tcp-postgres-result-4328bd8e-e2fa-492f-b8f1-016fcb8394d2.json`, SHA256 `1760293d11bd77ff1ded5bb5db8b7dd8eac3ee832f3b3a9578dcb0dd2dbcf89c`; aggregate75 fontes `c608200717b6aa6d615ff1b5506c0478017e1a0bb82e7aee68af6debd7d1fb52`. JSON público reconstruído em `.impeccable/ci/postgres-tcp-gate.json`, sem emails/senhas/tokens/DSN ou fingerprints brutos.

Tentativas iniciais UUID `86eab38c-a4ba-46fb-b5e7-956ff3dadf93` e `0398e6ac-772f-41fe-9232-a786b874433e` falharam no guard PID do redirector Windows; cleanup verificado em ambas. Corrigido o launcher, rodada `5d753820-0b6b-4818-bd5a-5387d1f0a72f` PASS; a final acima adicionou status offline real e refresh na B reiniciada. Não usar a prova intermediária para certificar fonte final.

Sem build, suíte auth antiga, CI snippet ou DB adicional. Limite: duas versões idênticas/restart controlado, sem browser multiupstream/nginx/rollout/CI hospedada. [Backend](backend-tcp-postgres-session-2026-10-03.md), [continuidade](CONTINUATION.md).

## Preparação anterior ao limite de uso — histórico

Reserva Banco somente deste documento e do lifecycle ignorado
`.impeccable/runtime/tcp-postgres-lifecycle.py`. Nenhuma fonte versionada,
schema/model/migration, Git, CI ou documento compartilhado alterado.

Maestro implementa `api/scripts/postgres_tcp_gate.py`; Backend implementa
`api/scripts/postgres_tcp_worker.py`. O runner só poderá executar o novo gate
após ambos congelarem código/testes e fornecerem hashes SHA256. Sucesso HTTP
ASGI anterior não é aprovação TCP. Nenhum gate antigo será reexecutado.

## Contrato de lifecycle

- Reutiliza por import as definições de identidade/readiness/cleanup do
  lifecycle HTTP aprovado; não executa seu `__main__`, gate HTTP ou bloco CI.
  SHA256 desse arquivo é conferido antes/depois durante a nova rodada.
- Uma instância UUID própria, imagem oficial local
  `pgvector/pgvector@sha256:2ba9ca5f2e7daa0f0e7723cba1ee9167bab54efd3640516a44ac1a928dd67e7a`,
  `--pull=never`, tmpfs512MiB `/var/lib/postgresql`, sem bind/volume existente.
  Label `com.gandalf.tcp-postgres-gate=<UUID>` mais disposable-gate=true.
- Loopback55432 ou55433 previamente livre; role `gandalf_gate`, um banco
  `gandalf_gate_<UUIDhex>` inicialmente vazio e senha aleatória somente em
  ambiente filho limpo. Sem `.env`, segredo herdado, URL em argv/log ou build.
- ID completo, imagem/digest, nome/labels, mounts, role/banco/env e porta são
  comparados em memória antes do SQL e novamente antes do cleanup por ID.
  Preservar PG5432/APIs/frontend/volumes/dados existentes. Sem prune.
- O gate Maestro valida DB vazio, migra uma vez, inicia duas APIs em processos
  filhos TCP exclusivos e reinicia B com sessão vigente. Worker não migra.
  Processos/ports TCP e encerramento são responsabilidade do novo gate.
- Depois do gate: prova SQL READ ONLY independente de engine/identity,
  READ COMMITTED/head/extensions, contagens iguais ao JSON, AI0,
  refreshes não revogados expirados0 e outras conexões cliente0.
- Sem CI snippet ou banco auth adicional nesta rodada.

## Opt-in/hashes propostos para executar depois do freeze

Ambiente do lifecycle (nenhuma credencial nestes valores):

```text
GANDALF_TCP_PG_LIFECYCLE_ALLOW=isolated-coordinated-backend-frozen
GANDALF_TCP_PG_GATE_SHA256=<freeze Maestro>
GANDALF_TCP_PG_WORKER_SHA256=<freeze Backend>
GANDALF_TCP_PG_SOURCE_SHA256=<aggregate do source_snapshot do gate>
```

`api/.venv/Scripts/python.exe .impeccable/runtime/tcp-postgres-lifecycle.py`
fornece somente ao filho `GANDALF_TCP_PG_ALLOW` no mesmo valor e
`GANDALF_TCP_PG_URL` do banco próprio. O gate deve manter import stdlib antes
opt-in e oferecer `source_snapshot()`; lifecycle calcula aggregate pelo JSON
sort_keys igual ao padrão anterior. Whitelist do JSON TCP será reconciliada
com o freeze antes de qualquer criação de container; no preparo atual recusa
PASS desconhecido explicitamente.

`--preflight` apenas leitura: verifica Docker/context local/Linux/imagem
local/nenhum container com label TCP gate e portas55432/55433. Não cria PG,
não exige app pronta, não migra nem certifica integração.

## Limites e continuidade

Ainda não há aprovação TCP nem resultado SQL nesta etapa. Backend/Maestro
estão preparando fontes. Após freeze: completar contrato JSON, executar uma
única rodada nova e registrar resultado sanitizado/sourcefreeze/cleanup.
Uma futura aprovação limita-se ao que os checks mostrarem; não implica
Nginx/browser/load balancer, mistura de versões, HTTPS, CI hospedada ou
corridas não reproduzidas. Banco não stage/commita; Maestro serializa.
