# Backend — gate TCP/PostgreSQL — 2026-10-03

Maestri reservou worker/testes ao Backend. O terminal atingiu o limite de uso antes de concluir o protocolo e os testes; Maestro assumiu os arquivos após conferir o estado parado. Este relatório registra a conclusão pelo Maestro, sem revisão independente posterior do Backend.

## Entrega validada

- `api/scripts/postgres_tcp_worker.py`: worker exclusivamente de teste, Settings explícito/offline, imports protegidos pelo loader existente, socket loopback porta0, Uvicorn com lifespan real, sem migrations ou logs de credenciais.
- Configuração stdin JSON com `database_url`, `jwt_secret`, `run` UUIDv4 e `instance` a/b; chave repetida, campo extra, segredo curto ou entrada excessiva são recusados. Opt-in `GANDALF_TCP_PG_ALLOW=isolated-coordinated-backend-frozen` antes do import.
- READY somente após startup; cabeçalhos `x-gandalf-gate-run`, `x-gandalf-gate-instance`, `x-gandalf-gate-pid` em todas as respostas. Wrapper de teste preserva aplicação/rotas, sem dependências ou serviços substituídos.
- STOP/EOF solicita shutdown e disposal; pai usa prazo8s e fallback terminate/kill exclusivamente do Popen próprio, marcando falha se precisar forçar. Erros mostram somente etapa/linha local, sem mensagens, stack, DSN, senha ou token.
- `api/scripts/postgres_tcp_gate.py`: valida destino e banco vazio antes de migrations, mantém os tokens em memória no mesmo cliente, confirma cada resposta do processo esperado, bloqueia redirects/proxies herdados e reconstrói o JSON público.

No Windows, o executável venv é redirector: PID do launcher não era o PID da API. As duas tentativas iniciais recusaram essa identidade. A correção usa interpretador base diretamente com `-S` e PYTHONPATH apenas dos packages do ambiente atual; igualdade PID permanece obrigatória. Também se conferiu a chave composta de playlist_tracks para ordenar os fingerprints SQL corretamente.

## Verificação

57 testes novos/focados PASS em0,22s: guards/protocolo/sanitização/status offline, identidade/middleware, fechamento socket/engine e cleanup dos dois filhos antes de remover cwd temporário. Ruff/formatação4 arquivos PASS. Testes não executaram PG nem serviços existentes; o gate real separado executou exclusivamente o cenário novo.

Prova final TCP real PASS em PostgreSQL18.6, UUID `4328bd8e-e2fa-492f-b8f1-016fcb8394d2`, sete checks/30 requests. Login em A, me/refresh em B, token novo em A; favoritos/playlists compartilhados e ownership; shutdown/restart B com o mesmo par ainda em memória, recursos preservados e refresh aceito pela nova B; token novo em A; logout204 em A/refresh401 em B. Access anterior permanece válido até expiração, conforme contrato atual. Snapshot de recursos/cache idêntico, AI0 e SQL independente/conexões0/cleanup verificados.

Fonte congelada: gate SHA256 `24b509f550662560aa752b204e9388349c076c9a58994880e48533b793de3219`; worker `f7e59b820dcf25be8ff1d9b071ba62a7a3bd8cfad1033fb34693cfd9c3965a14`; aggregate75 fontes `c608200717b6aa6d615ff1b5506c0478017e1a0bb82e7aee68af6debd7d1fb52`. Artifact/hash/SQL em [relatório Banco](database-tcp-postgres-session-2026-10-03.md).

## Limites

Dois processos TCP com a mesma versão e restart controlado; cliente HTTP stdlib, sem browser/nginx/load balancer novo. Nenhuma mudança em app/main/auth/config/schema/local/deploy/cliente, build ou suíte antiga. Não certifica rollout, versões distintas, migrations concorrentes, logout-refresh concorrente, falhas de commit, stress, HTTPS ou CI hospedada. Rate limiter continua local por processo; JWT estável e banco comum são pré-condições. Workflow TCP ainda pendente conforme [CI](CI.md).
