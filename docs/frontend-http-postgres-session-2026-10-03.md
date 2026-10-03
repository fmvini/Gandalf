# Frontend — revisão HTTP entre APIs/PG — 2026-10-03

## Consolidação Maestro após freeze e gate real

A lacuna identificada na revisão WIP foi fechada antes do freeze: o access emitido por refresh B é usado em `/auth/me` A e o emitido por refresh A em `/auth/me` B, com o mesmo proprietário. Backend38 testes PASS; Banco executou o script congelado em PostgreSQL 18.6 próprio com nove checks/44 requests, SQL e cleanup verificados. [Evidência Banco](database-http-postgres-session-2026-10-03.md). Essa prova usa ASGI em um processo; não foi executado browser, restart com sessão vigente ou TCP entre processos. Nenhum arquivo de produto/harness frontend foi alterado. As observações WIP abaixo são históricas.

## Estado e escopo

Parecer somente leitura após commit informado `1b1c9b7` e gate ca-7 PASS. Reserva exclusiva deste documento; nenhum produto/harness, teste, build, browser, rede, Git ou documento compartilhado alterado/executado. Consultados DEVELOPMENT_LOG/CONTINUATION, cliente auth/API, harness deployment, nginx e runner atuais. A aprovação ca-7 cobre uma API offline com restart, não HTTP entre duas APIs nem continuidade da mesma sessão.

## Viabilidade e evidências do cliente

- `frontend/src/lib/api.ts:26`: uma BASE_URL definida no build; produção usa `/api/v1`. `api.ts:40` envia fetch para essa base, sem escolher/identificar instância.
- `frontend/src/lib/auth.ts:46`: refresh usa `/auth/refresh` e substitui o par em memória. `auth.ts:51` single-flight é local à sessão JavaScript, não um lock distribuído entre browsers/APIs.
- `frontend/src/lib/auth.ts:66`: requests autenticados enviam Bearer pela mesma base e conferem revisão/abort/owner switch. `auth.ts:96` logout aguarda rotação em andamento. `auth.ts:129` login recebe tokens e consulta me, sem afinidade com processo.
- Tokens ficam apenas em memória; reload/nova página do app inicia outra sessão. Abrir uma segunda origem com page.goto não prova portabilidade da sessão atual; perde o módulo em memória conforme ADR-0006.
- Nenhuma hipótese de sticky session é exigida pelo cliente. Compatibilidade entre instâncias depende do servidor: mesmo banco PostgreSQL, segredo/configuração JWT coerentes e contratos públicos iguais. Isso é requisito de teste, não comprovação obtida nesta revisão.

## Contrato coordenado atual — ASGI/PG

**Nenhuma alteração frontend necessária.** Maestro definiu `api/scripts/postgres_http_gate.py`: duas instâncias create_app/TestClient, com lifespans e engines independentes, no mesmo processo e usando o mesmo PostgreSQL/JWT. WIP agora disponível e revisado somente leitura. Exercita endpoints HTTP via transporte ASGI; não é TCP nem comunicação entre processos.

Backend reserva auth cruzado/rotação de refresh/replay/logout, favoritos/playlists/cache e ownership, headers e checks SQL. Banco executará a prova em PostgreSQL real somente após freeze. Tokens permanecem em memória e o relatório deve ser sanitizado. **Ainda não executado nesta revisão; aprovação depende da evidência Banco.** Não há promessa de restart, rollout, load balancer ou browser nessa unidade.

Esse contrato permite verificar compartilhamento de estado entre duas apps/engines distintas e comportamento dos endpoints/middleware sobre PG. Mesmo aprovado, não demonstra transporte TCP, workers/processos independentes, continuidade da sessão através de restart ou disponibilidade durante troca de upstream. Single-flight do frontend continua local ao contexto JavaScript; esta unidade não o executa.

## Proposta TCP futura — fora do contrato atual

A recomendação inicial de cliente HTTP em rede permanece como extensão futura separada, não pré-requisito nem descrição da unidade ASGI autorizada. Se houver novo escopo, Backend pode manter um cliente TCP/HTTP e tokens em memória enquanto Banco controla dois processos identificados e PG descartável:

1. Identidade UUID/containers/portas loopback exclusiva, Settings explícito offline, PG compartilhado e JWT_SECRET estável; migrations serializadas antes de servir. Não usar serviços/dados/.env existentes nem chamadas de fontes/IA.
2. Cadastro/login A e me na B com access emitido A; refresh B, provar rotação e uso do novo par na A. Nunca registrar pares, headers ou corpos de autenticação.
3. Favoritos/playlists e origem pública produzidos em uma instância e consultados na outra; IDs/ordem/snapshots e ownership de duas contas verificados por HTTP real e SQL compartilhado.
4. Restart de uma API com identidade/configuração revalidadas e cliente de teste vivo; reutilizar a sessão vigente sem relogin para provar continuidade. A mera emissão de um novo login após restart não cobre isso.
5. Logout em uma instância e refresh revogado401 na outra; isolamento, opacidade 404/DELETE e SQL/cleanup explícitos. Corridas/replay concorrentes requerem cenário próprio, não inferir cobertura apenas de chamadas sequenciais.

Somente uma execução futura com evidência poderia aprovar HTTP entre processos nesse escopo. Nem esse desenho, por si, certifica comportamento de load balancer, UI com troca de upstream, zero downtime, mistura de versões, rollout/migrations concorrentes ou deploy remoto. Não implementado/executado/autorizado nesta unidade ASGI.

## Limites do harness atual

- `frontend/tests/deployment.mjs:155`: helper Node só envia API pela origem de frontend configurada. `deployment.mjs:196` bloqueia requests do browser fora dessa origem.
- Create e verify são invocações/browser distintos; artifact contém IDs públicos, nunca tokens. `deployment.mjs:430` verifica cache após restart, e `deployment.mjs:437` faz login novo. Prova persistência e relogin, não continuidade do mesmo par entre APIs.
- Tráfego registra método/path/status/contagem, sem identidade de upstream. Mesmo que nginx distribua requests, esse artifact sozinho não prova qual API emitiu/rotacionou/atendeu cada chamada.
- Nginx atual aponta para `api:8000`; adicionar apenas uma segunda API não demonstra que foi utilizada pelo browser.

Se Maestro exigir browser adicional, conservar a mesma origem/SPA e roteamento de teste controlado para login/register A e refresh/me/recursos B, com prova de upstream pelo runner. Para restart com sessão viva, precisaria checkpoint no mesmo processo/browser. Não alterar api.ts, persistir tokens, relaxar guard de origem ou mockar API para obter essa prova. Essa extensão não está implementada/autorizada nesta reserva.

## Revisão do contrato Backend e freeze

Leitura RO do WIP `api/scripts/postgres_http_gate.py`, sem executar/importar o script ou testes. Backend estava preparando/formando a fonte durante esta leitura; números de linha podem mudar até freeze. Achados:

- `http_contract`: duas create_app com Settings/model_copy, TestClients/lifespans aninhados e engines/session_factories/limitadores distintos; dependency_overrides vazio. Settings explícito `_env_file=None`, PG compartilhado/JWT gerado para esta execução, catálogos locais/Groq vazio. Imports ocorrem em diretório próprio vazio com ambiente filtrado; não consultam api/.env existente.
- Rotas/payloads coerentes com contratos atuais: register201/login200/me/refresh/logout204, recomendações de leitura por book_id/mode/target_duration_min, favoritos por recommendation_id/item_id e playlists por source_recommendation_id. Middleware exercitado: X-Request-ID UUID, no-store/no-cache em auth, envelope/código de erro e corpo vazio204.
- Auth cruzado explícito: login A e me B; refresh B do par A, descendente refresh A, replay ancestral B401, família sem ativos e descendente rejeitado A401; famílias independentes preservadas. Logout alheio/antigo não revoga família vigente; logout com refresh atual e rejeição posterior na outra app.
- Uso de `headers(first)` depois de revogar a família não é defeito de contrato: access JWT continua válido até expirar e logout/replay não aplica denylist ao access. O script testa essa semântica explicitamente por me. Os refresh tokens usados em cada rotate/logout correspondem aos pares definidos no cenário, sem persistir credenciais no relatório.
- **Lacuna concreta de cobertura, não defeito de produto:** `rotate` exige mudança do refresh, mas não valida mudança/formato do access retornado nem envia o novo access como Bearer em me/recursos na outra app. Header de recursos reutiliza first. Assim, mesmo eventual PASS cobre rotação/portabilidade do refresh e aceitação do access original; não deve ser descrito como comprovação de que o access recém-rotacionado é aceito em A/B ou como teste completo do cliente authSession. Maestro decide eventual ampliação Backend; nenhum código foi alterado pelo Frontend.
- Origem criada A, explicação consultada A/B, favoritos criados B e repetidos/listados A com snapshot igual, status/DELETE alheio opacos; playlist criada B/lida A, GET/DELETE alheio404 e listas por dono. SQL confere IDs de dono, origem, ordem e conteúdo das faixas/favorito, cache/TTL inalterados, contagens e AI0.
- Lifecycle: listeners engine_disposed comprovam fechamento A uma vez enquanto B permanece utilizável por me, depois fechamento B; observer dispose em finally. É shutdown de uma app com outra viva, **não restart**, processo morto/recriado ou reconexão TCP.
- Sanitização: public_result reconstrói whitelist de checks/contagens/requests A-B/head/hash/transport/dispose; não inclui emails/senhas/tokens/DSN/corpos. Main converte exceção em classe enum+stage, sem mensagem/traceback. Objetos de sessão e pares permanecem internos. Esta leitura não certifica canais de logging do ambiente inteiro.
- Fixture `@example.test` ainda aparecia no WIP lido; hipótese EmailStr já comunicada pelo Maestro. Não dupliquei reprodução nem aviso ao Backend. Revalidar a fonte congelada pela equipe responsável antes PG real; não tratar esse WIP como executável aprovado.

Nenhum novo defeito funcional confirmado além do candidato de fixture já coordenado; lacuna do access rotacionado registrada como limite de cobertura. **Sourcefreeze Backend e execução PostgreSQL real/Banco pendentes**, sem resultado de gate nesta revisão. Restart sem relogin e transporte TCP continuam exclusivamente na proposta futura.

Documento congelado para Maestro. Sem nova aprovação de runtime, testes ou HTTP entre apps nesta entrega. Maestro mantém Git/shared docs e decide qualquer escopo adicional.
