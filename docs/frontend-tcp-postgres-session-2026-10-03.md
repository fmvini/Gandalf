# Frontend — revisão do gate TCP/PG — 2026-10-03

## Conclusão do Maestro após a preparação Frontend

Frontend congelou apenas o checklist RO abaixo e atingiu o limite de uso. Maestro confrontou o gate final com esse checklist e executou cliente TCP real; sem nova aprovação independente nem browser/UI nesta unidade.

PASS UUID `4328bd8e-e2fa-492f-b8f1-016fcb8394d2`: respostas identificadas UUID/instância/PID do Popen próprio; login A/me-refresh B/access novo A; favorito/playlist/ownership; tokens no mesmo cliente durante restart B, sem login; nova B aceita access/recursos/refresh vigentes, novo access funciona em A. Logout atual A204/refreshB401; access conserva semântica até expiração. SQL/snapshots/cleanup confirmados. Correção do redirector Windows preserva igualdade PID.

Sete checks/30 requests e57 testes focados PASS, status offline real/AI0/conexões0/fonte inalterada. [Evidências](database-tcp-postgres-session-2026-10-03.md). Produto/frontend/harness anteriores intactos, sem repetir fullstack. Browser com mesma origem nginx/vários upstreams continua pendente; cliente HTTP não comprova JavaScript em execução.

## Estado e reserva na leitura inicial — histórico

Retomada coordenada pelo Maestro após HEAD informado `2d30cc7`. Consulta RO do topo de DEVELOPMENT_LOG: gate anterior ASGI/PG aprovado com duas apps/engines em um processo; não aprova TCP/restart. Nesta leitura pontual, `api/scripts/postgres_tcp_gate.py` **ainda não estava disponível**. Revisão do código TCP pendente; checklist abaixo registra o contrato solicitado, não implementação validada. Sem prolongar espera.

Reserva exclusiva deste documento. Nenhum produto/UI/harness, mock, instalação, Git, documento compartilhado, browser, processo, teste, rede/API/LLM ou gate executado/alterado. Maestro coordena Git/CI/shared docs; Backend runner/worker; Banco PG real após sourcefreeze. Comunicação desta rodada pelo resultado final, sem ask-back ao Maestro.

## Contrato TCP atual e checklist de revisão futura

1. Dois processos API independentes, loopback com bind porta0 e porta efetiva verificada; mesmo PostgreSQL/JWT sintéticos. Pai valida banco descartável/UUID e aplica migrations uma vez antes de iniciar workers. Settings explícito sem api/.env, modo offline e nenhuma chamada de fonte/IA.
2. Cada resposta deve ser atribuída à API esperada por identidade de teste UUID/instance/PID, confrontada com o processo criado pelo runner; inclui respostas de erro. Header de identidade pertence ao worker de teste, sem mudança de produto. Não considerar só nome da URL como prova de processo.
3. Tokens/payloads de autenticação permanecem em variáveis do processo de teste, sem artifact, storage, logs ou arquivos. Identidades/contagens/checks públicos podem ser relatados por whitelist, nunca headers Bearer, emails, senhas, DSN ou corpos/tracebacks brutos.
4. Login A produz par P0; me B aceita seu access com o mesmo dono. Refresh B produz P1, prova rotação e me A aceita **access novo P1**, não apenas o access original. Testar o novo access explicitamente evita a lacuna identificada e corrigida na etapa ASGI anterior.
5. Criar origem pública/favorito/playlist em uma API, ler na outra e guardar IDs/ordem/snapshot esperados; segunda conta não acessa recursos alheios. Não confundir acesso do mesmo dono em ambas com isolamento entre donos.
6. Antes de restart B, conservar par vigente P1 no mesmo processo cliente. Encerrar/reiniciar apenas worker B próprio; revalidar novo PID/porta e mesmo UUID/instance/configuração/versão/PG/JWT. A continua viva. Não recadastrar nem logar outra vez para preparar a prova.
7. Após restart B, me/recursos B devem aceitar o access conservado P1 sem relogin; origem/cache/favorito/playlist e ordem/metadados/ownership permanecem iguais. Refresh B deve aceitar o refresh vigente conservado e emitir P2; novo access P2 utilizável em A. Evidência deve separar a sessão anterior ao restart de uma sessão nova, nunca serializar tokens para atravessar fases.
8. Logout A usa refresh atual P2 e access válido, resposta204; tentativa de refresh P2 na B exige401. Usar token já consumido/ancestral no logout não prova revogação do par vigente. Replay que revoga família precisa cenário separado ou ordem explícita para não invalidar acidentalmente a sessão destinada ao restart.
9. Revogação de refresh não equivale a denylist de access: JWT previamente emitido continua válido até expirar conforme contrato atual. Resultado não deve alegar logout invalidando imediatamente todo access.
10. SQL independente confirma dono/IDs/contagens/snapshots/cache/AI0 antes/depois, e cleanup por identidade própria/ports/conexões/processos. Timeouts devem falhar com diagnóstico sanitizado; nenhum fallback para mocks/ASGI para converter falha TCP em PASS.

## Relação com o cliente e limites

`frontend/src/lib/api.ts` usa uma BASE_URL definida no build; authSession não fixa instância e conserva tokens somente em memória. Single-flight/abort/owner switch são do contexto JavaScript, não coordenação distribuída. Um cliente HTTP do runner vivo durante restart é suficiente para a prova TCP contratada, sem editar UI.

`frontend/tests/deployment.mjs` create/verify usam processos/browsers distintos e relogin, com artifact apenas de IDs. Aquele gate comprova persistência/UI/nginx de uma API; não comprova continuidade do mesmo par A/B. Nesta unidade não é necessário reexecutá-lo nem estender suas tolerâncias.

Eventual PASS TCP prova endpoints reais entre dois processos e restart B **da mesma versão** no escopo observado. Não prova browser/authSession em execução, nginx/load balancer, CORS entre origens, expiração por tempo real, zero downtime, rollout/mistura de versões, migrations concorrentes, stress concorrente ou deploy remoto. Aprovação ASGI e checklist não substituem essa execução.

## Próximo ponto e freeze

Quando Backend disponibilizar o arquivo congelado, revisar somente RO as operações/par vigente antes/depois do restart, identidade dos workers, ownership/snapshots, logout/revogação e sanitização contra o checklist. Banco deve fornecer a execução TCP/PG real e cleanup; **nenhuma aprovação TCP registrada agora**. Documento congelado para Maestro, sem novas esperas ou gates nesta rodada.
