# Frontend — gate de deployment — 2026-10-03

## Estado e reserva

Harness implementado e congelado para integração pelo Maestro/Banco. **Resultado final consolidado pelo Maestro: ca-7 PASS/exit0 create7/verify6 checks contra Nginx/API/PostgreSQL reais, antes/depois de restart, com SQL/sourcefreeze/cleanup aprovados.** Reservas do Frontend: `frontend/tests/deployment.mjs` e este documento. Nenhuma alteração de produto, package.json, CI, Git ou documentos compartilhados pelo Frontend. Dockerfile recebeu separadamente o secret BuildKit opcional de CA autorizado pelo Maestro.

UUID final `d611ad28-dff0-4523-abc0-8b6c049891aa`, SQL2 contas/2 favoritos/1 playlist11 faixas/3 caches com hashes antes/depois/verify iguais, AI0; browser/console/externo0. Aborts de logout4 create/2 verify correlacionados à prova completa.94 guards runner/67 Node/38 startup Backend, Ruff/format98/actionlint PASS. [Receita/evidência final](deployment-integration.md). O escopo aprovado é integração local offline com uma API; CI hospedada/HTTPS/publicação/fontes online continuam pendentes. Checkpoints de diagnóstico abaixo são históricos.

### ca-4/ca-5 — correlação estrita do abort de logout

- Maestro reportou ca-4 com todas as asserções create até o final (duas contas/auth/refresh/logout/revogação/ownership/snapshots), FAIL apenas em browser-clean; counters/failures não haviam sido preservados no runner. Acrescentado depois enum de error_code: ERR_ABORTED/ERR_FAILED/ERR_CONNECTION_REFUSED/other, sem texto bruto.
- ca-5 comprovou zero pageerror/console.error/rede externa e exatamente quatro failures POST auth/logout net::ERR_ABORTED; cada logout também tinha tráfego204, UI login e refresh revogado401. Cleanup verified. Isso autoriza tratar somente abort de logout completamente comprovado, sem ignorar requests por path genérico.
- `logoutProofTracker` mantém WeakMap por objeto Request, status HTTP real observado e prova completa. `logout()` marca o mesmo response.request somente depois de verificar token atual, heading/UI login e request real de refresh401. O filtro final tolera apenas esse mesmo objeto com POST da origem exata/path auth/logout sem query, status204 observado, prova completa e ERR_ABORTED. Objetos distintos com URL igual não compartilham prova; sem204/sem prova/outro método/path/origem/código continuam FAIL. HTTP de erro, console, pageerror e rede externa permanecem gate.
- Requests e tokens nunca são serializados. Relatório conserva failures sanitizados não resolvidos e contagem `proven_logout_abort_count`; nenhum objeto Request no artifact. Fixture SQL segue preservada nas duas fases.
- `node tests/deployment.mjs --self-test`: **67 checks PASS**, incluindo 19 casos novos do classificador (positivo e negativos de identidade/status/prova/método/path/origem/código). Sintaxe/diffcheck PASS. Sem browser/build/gate pelo Frontend. Freeze para ca-6 coordenado pelo Maestro; aprovação integrada ainda pendente.

### ca-3 — causa reproduzida e ajuste de HTTP204

- `.impeccable/runtime/deployment-gate-final-ca-3.json`: DeadlineError em `response-finished-204`, dentro de logout/apiResponse (`deployment.mjs153/239` na versão executada). POST auth/logout204 observado, UI já em /login, formbusy=false/alert0, sem HTTP de erro no navegador; cleanup verified. Causa comprovada do bloqueio: espera do harness por response.finished no 204 sem corpo, não falha de logout/cadastro do produto.
- Ajuste autorizado somente em apiResponse: após exigir status exato, não chamar response.finished para expected204. Logout continua exigindo refresh atual, heading Entre no Gandalf e refresh revogado401 real. Para 200/201 mantém finished/JSON reais com deadlines10s; nenhuma alteração de timeout, status, revogação, produto ou API.
- `node tests/deployment.mjs --self-test`: 48 checks offline PASS; sintaxe e diffcheck PASS. Sem build/browser/gate pelo Frontend. Freeze para nova rodada integrada do Maestro; este ajuste ainda não constitui create/verify PASS.

### ca-2 — deadlines do harness e progresso

- Maestro reportou TimeoutExpired Node300s em browser-create sem JSON childFAIL; SQL próprio mostrou uma conta, dois favoritos e uma playlist salvos, cleanup verified. Isso comprova que cadastro A/fluxos de salvamento avançaram; não identifica a operação exata bloqueada. HTTP204 response.finished permanece candidato, sem prova definitiva.
- Autorizado ajuste apenas do harness: deadline real Node de 10s em response.finished/json e evaluate (incluindo validade HTML/destino/storage/clock), headers/content/cookies; diagnóstico no catch limitado a 2s e fechamento do browser limitado a uma tentativa de 5s. Timer é do Node, independente de Date.now alterado somente no browser.
- JSON FAIL é emitido antes do fechamento no finally. Se transporte Playwright não fecha dentro do limite, emitir falha de cleanup e encerrar somente o processo Node do harness; não aprovar/ignorar cleanup. Runner continua responsável por recursos descartáveis e por conferir limpeza. Nenhum processo/serviço existente é encerrado.
- STDERR agora contém linhas JSON `PROGRESS` com phase/stage/substage/check em cada mudança/mark; STDOUT mantém um único artifact de sucesso. Sem credenciais/PII. Substage distingue `api-*`, `response-finished-<status>`, `response-json`, avaliação e fechamento; coleta do runner deve considerar a última linha PROGRESS quando houver kill/timeout.
- Mantidos JSON/status reais e asserções HTTP201/200/204/401/404, auth/ownership/persistência; nenhum aumento dos timeouts existentes. Guard/selftest foi reexecutado por mudança funcional: **48 checks PASS**, incluindo conclusão, rejeição original e timeout de promise pendente; sem browser/rede. Sintaxe e diffcheck PASS. Sem build/gate/suíte geral. Novo freeze para Maestro.

### Diagnóstico da primeira rodada real e novo freeze

- Evidência fornecida pelo Maestro: `.impeccable/runtime/deployment-gate-final-ca-1.json`. Build API/frontend PASS, PG18.6/head0008/vector0.8.6/citext1.8 e status offline PASS; browser create FAIL TimeoutError em `account-a-register`, cleanup verified. Portas descartáveis API32769/DB32768/frontend32770; serviços existentes preservados. Nenhuma nova execução do runner/browser pelo Frontend.
- Artifact anterior só informa a etapa ampla; não permite concluir se falhou no link/campo/POST/notice ou após login. **Não atribuir ainda causa comprovada à URL de cadastro ou a returnTo**. RO: `Authentication.tsx` conserva returnTo após register/login; `App.tsx` link Entrar na conta do cabeçalho não fornece state, e o harness usa esse link. Retorno a Music é possível em outros pontos de entrada; candidato informado pelo Maestro, sem prova específica nesse artifact.
- Harness agora aguarda `/register` e heading Crie sua conta antes de preencher, evitando preencher o E-mail remanescente do formulário anterior durante transição. Mantém espera POST register201, UUID e notice Conta criada; verifica validade HTML da fixture antes de submit. Após cadastro exige `/login`.
- Login lê somente pathname de returnTo allowlist no history.state, exige destino correto após API200 e sessão publicada (Minha conta), então abre `/account` pelo link SPA quando necessário, sem reload/perder tokens; preserva asserções Sua conta/perfil/accountReady/ownership.
- Diagnóstico de falha inclui `substage`, `failure_location` limitada a arquivo deployment.mjs/linha/coluna, `auth_diagnostic` com pathname allowlist/form presente/busy/número de alerts/IDs de campos inválidos e contagens sanitizadas de tráfego. Sem valores de inputs, DOM/texto de erro, emails, senhas, tokens, querystrings ou stack bruto. Banco/Maestro devem propagar esses campos sanitizados no próximo artifact.
- API wait e ação são observados juntos por Promise.all, impedindo timeout secundário não tratado quando click falha. Critérios/tempos funcionais e asserções auth/isolamento não reduzidos. Syntax `node --check tests/deployment.mjs` PASS após ajuste; selftest/build/suíte geral não repetidos. Novo freeze para próxima rodada do Maestro.

Consultados `docs/DEVELOPMENT_LOG.md`, topo de `docs/CONTINUATION.md` e `docs/IMPLEMENTATION_STATUS.md`, Compose/overlay PG, nginx/Dockerfile e contratos/seletores de `frontend/tests/live.mjs`. Aplicada skill webapp-testing ao harness e Maestri à coordenação; sem mudança visual que exija impeccable/taste.

## Contrato final do runner

- Executar no diretório `frontend`: `node tests/deployment.mjs`.
- `GANDALF_DEPLOYMENT_ALLOW=isolated-coordinated` obrigatório.
- `GANDALF_DEPLOYMENT_TOKEN`: UUID exclusivo do projeto descartável; não é credencial da API e não aparece no artifact.
- `GANDALF_DEPLOYMENT_BASE_URL=http://127.0.0.1:<porta>`: origem canônica literal IPv4, porta explícita maior que 1023. Proibidas **5173/8080/8000/8001/5432/5433/55432/55433**. Sem usuário/senha, caminho, query, fragmento ou hostname abreviado.
- `GANDALF_DEPLOYMENT_PHASE=create|verify`: duas invocações, sem renomear após freeze.
- `GANDALF_DEPLOYMENT_PASSWORD`: senha sintética de 10–128 caracteres fornecida somente no ambiente child, nunca em argumentos/logs/artifact. Emails/nomes de usuário distintos derivados do UUID, somente em memória.
- `GANDALF_DEPLOYMENT_ARTIFACT`: caminho próprio do runner. Create escreve JSON apenas após sucesso e fechamento do browser, com `flag=wx` para não sobrescrever estado anterior. Verify lê esse mesmo arquivo e não o modifica; compara origem/fingerprint do projeto e identidades UUID.
- Stdout de sucesso: um JSON com `status`, `phase`, `checks`, `user_ids` (2), `favorite_ids` (2, MUSIC/BOOK), `playlist_ids` (1), `public_snapshot_music_ids`, `public_snapshot_id`, `playlist_music_ids` em ordem, identidades `favorites`, fingerprint SHA256 do UUID, origem e contagens de tráfego. Sem emails/senhas/tokens/corpos de auth.
- Erros: JSON genérico com etapa, classe de erro e contagens/path/status de falhas; não imprimir Error.message, call logs Playwright, headers ou corpos. Entrada de artifact é reconstruída por whitelist antes de retornar, evitando refletir campos privados desconhecidos.

Banco controla Compose root + overlay PG + overlay teste, projeto/labels/UUID, isolamento de rede, migrations/identidade SQL e readiness **antes** da primeira página. O harness não inicia servidor, Vite, API, containers ou banco; fecha apenas seu Chromium. O opt-in não substitui a prova de identidade PG pelo runner.

## Checks implementados

1. Antes do browser, GET real via nginx `/api/v1/system/status` exige `catalog=local`, `ai.provider=null`, `ai.configured=false`; fetch de Node não segue redirects e aceita somente paths da mesma origem.
2. Create verifica acesso direto às rotas SPA públicas/login/cadastro e protegidas (estas exigem login). Documento inicial deve retornar 200 com servidor nginx e sem `/@vite/client`.
3. Descoberta musical offline com filtros instrumental/energia baixa, itens exibidos iguais à quantidade retornada e explicação real. Descoberta de livros/O Hobbit; leitura/Duna com trilha, favorito musical, playlist e favorito BOOK salvos por UI.
4. Duas contas cadastradas/logadas por UI, conta correta exibida, tokens somente em memória; storage/cookies sem autenticação persistente.
5. Refresh real iniciado pelo botão Atualizar dados: adianta temporariamente **só Date.now do cliente**, exercitando expiração proativa; exige POST refresh 200/rotação de ambos os tokens e perfil carregado. Relógio/API/respostas não são simulados; não certifica expiração JWT por tempo real.
6. Logout real 204 usa refresh atual; tentativa posterior de refresh revogado exige 401. Credenciais ficam somente em variáveis de memória, com asserções booleanas que não imprimem valores.
7. Conta B sem favoritos e sem acesso GET/DELETE à playlist A (404); status de favorito alheio vazio, DELETE favorito alheio 204 inofensivo. UI B vazia. Relogin A preserva dois favoritos e ordem da playlist.
8. Verify após reinício lê explicação da origem pública anterior, confirma identidades das contas via me, favoritos/playlist por UI e API, IDs em ordem e relogin após reload (sessão em memória termina conforme ADR). Conta B continua vazia.
9. Create e verify preservam contas/favoritos/playlist até SQL final. Runner compara SQL antes restart, após restart e após verify. Exclusão própria não é gate desta unidade; DELETE alheio/ownership permanece coberto.
10. Tráfego real exigido em auth/login/me/refresh/logout, favoritos e playlists; status/método/path e contagens sanitizados. Browser pageerror/console.error/HTTP >=400/requisição falha/rede externa bloqueada fazem falhar. Exceções estreitas: GET books/search supersedido pelo debounce com net::ERR_ABORTED e abort de logout204 correlacionado pelo mesmo objeto Request com prova completa descrita acima. Sem route.fulfill ou mocks. URLs externas das faixas não são seguidas.

## Validação executada pelo Frontend

- `node tests/deployment.mjs --self-test`: **PASS, 45 checks**, browser_executed=false, network_executed=false. Casos: ausência/erro de opt-in, UUID, fase, senha, artifact; loopback e portas; URL com credenciais/caminho/query/fragmento/host obfuscado; artifact de outra origem/projeto/inválido; sanitização de campos privados extras.
- `node --check tests/deployment.mjs`: **PASS**.
- `node tests/deployment.mjs` sem ambiente opt-in: **recusa esperada exit1**, estágio opt-in-guard; nenhum browser/rede.
- Nenhum build, suíte geral, auth/live duplicado, API8000, chamada externa/LLM, uso de api/.env, alteração/restart dos serviços existentes ou push.

## Pendências e limites

Create + SQL/restart + verify + cleanup passaram na rodada final do Maestro. Reexecutar somente após mudanças/falhas novas, em ambiente descartável offline com identidade PG e imagens atuais. Não classificar build/guard/rodada parcial como browser PASS. O artifact preserva IDs/ordem, sem cópia completa de metadados públicos: comparação exata dos snapshots antes/depois é responsabilidade do SQL do runner; UI compara títulos retornados e identidade/ordem, não certifica áudio, qualidade online/G1, fontes externas, TLS de publicação, deploy remoto ou CI hospedada. Não houve QA visual nova e esta unidade não altera interface.

Freeze entregue ao Maestro/Banco; quaisquer falhas reais exigirão reprodução e reserva antes de alteração de produto. Maestro serializa package/CI/docs compartilhados e commits locais.
