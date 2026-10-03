# Backend — renovação DNS nginx — 2026-10-03

## Escopo e correção congelada

Reserva autorizada: `frontend/nginx.conf` e este relatório; posteriormente ampliada pelo Maestro para o RUN pip de `api/Dockerfile`. Git, documentação compartilhada, runner de integração e serviços existentes permanecem sob coordenação do Maestro/Banco.

O proxy estático resolvia `api:8000` ao iniciar e conservava o endereço antigo após substituir o container API. O patch usa `resolver 127.0.0.11 valid=1s ipv6=off`, `resolver_timeout 5s`, `set $api_upstream api:8000` e `proxy_pass http://$api_upstream`, sem URI/barra. Timeout de leitura e headers anteriores preservados.

Hostname variável utiliza o resolver e ausência de URI preserva a URI original; `valid` controla a validade do cache DNS. Referências primárias: [nginx proxy_pass](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass), [nginx resolver](https://nginx.org/en/docs/http/ngx_http_core_module.html#resolver). O DNS incorporado das redes Docker personalizadas usa `127.0.0.11`: [Docker networking](https://docs.docker.com/engine/network/#dns-services).

SHA256 congelado de `frontend/nginx.conf`: `545072b53f5cd33a0819ceeeebd0b5ffc8259e256ef9895d8a51fec98d77df65`. Diff revisado: apenas essas diretivas; `git diff --check -- frontend/nginx.conf` PASS. Nenhum stage/commit/push pelo Backend.

## Prova final — bridge própria e HTTP pelo host — PASS

Critério definitivo coordenado pelo Maestro: BEFORE **502 ou 504** representa indisponibilidade por upstream antigo, conservando o HTTP realmente observado; AFTER exige **200/marcador B/path-query exatos/nginx ID e StartedAt intactos/cleanup verificado**. A rodada bridge abaixo observou 502 e satisfez inclusive o critério anterior mais restrito. Não houve repetição após essa revisão; os artefatos históricos conservam seu status original.

Maestro reproduziu em Docker29.8 que `--internal` conserva `HostConfig.PortBindings`, mas pode deixar `NetworkSettings.Ports` vazio mesmo com container running. Essa escolha inicial do harness não correspondia ao networking da receita de deploy e impedia acesso pelo host. A decisão coordenada autorizou rede bridge UUID própria, `Internal=false`, sem host network/rede preexistente. Não há alegação de firewall ou bloqueio de egress.

O harness passou a criar bridge privada, publicar somente a porta nginx aleatória em `127.0.0.1` e requisitar HTTP do host com proxies de ambiente desabilitados. Fake API stdlib apenas responde HTTP, sem importar app/engine/config ou fazer chamadas externas; build da imagem corrigida continua `--pull=false --network=none`. Nenhuma edição adicional em `frontend/nginx.conf`.

Comando final autorizado: `api/.venv/Scripts/python.exe .impeccable/runtime/backend_nginx_dns_proof.py`, fora do sandbox. **Exit0/PASS**, escopo `before-and-after`; artefato ignorado `.impeccable/runtime/backend-nginx-dns-proof-bridge-result.json`. UUID `92335a7dbbf64c009a9eb5d45345cc42`, rede própria `192.168.247.0/24`, driver bridge/Internalfalse; uma subnet Docker e 21 rotas IPv4 do host conferidas, sem sobreposição (rota default excluída). Todos os recursos têm label de ownership UUID; máximo dois containers simultâneos.

| Fase final | Aquecimento | API A → B, mesmo alias `api` | Após troca e espera 2s | nginx preservado |
| --- | --- | --- | --- | --- |
| BEFORE, baseline existente | 200, marcador A e path/query exatos | `192.168.247.10` → `192.168.247.11`; A removida/verificada | **502**, pedido/verificação 38,891s | Mesmo ID e StartedAt |
| AFTER, imagem própria corrigida | 200, marcador A e path/query exatos | `192.168.247.10` → `192.168.247.11`; A removida/verificada | **200**, marcador `after-B` e path/query exatos; HTTP aproximadamente0,031s, verificação0,109s | Mesmo ID e StartedAt |

Ambas as fases: nginx `1.30.5`, `nginx -t` exit0. BEFORE nginx ID `d9e89c8ce7076b3c44fa062e234e21bf891cb5875111444545c0e6fe3261b004`, porta host61133. AFTER ID `7d1697612ca1c7cb96e74b5ed111c82ad0b54bb9d422819eae0b7d1cf247655d`, porta49316. Imagem corrigida própria `gandalf-backend-dns-92335a7dbbf64c009a9eb5d45345cc42:patched`, ID `sha256:4c1ab0eb6eecb7027b21fb078742d2663b3409a4caf559635c63db85ac77c5f9`, derivada do baseline com somente COPY nginx. Nenhum bundle ou dependência reconstruído nesta prova.

**Cleanupverifiedtrue:** removidos apenas containers próprios por ID/label/rede, rede própria vazia por ID/label/driver e tag de imagem própria por ID/label; ausência conferida. Baseline `gandalf-frontend:latest` manteve tag/ID. Serviços e dados existentes preservados. O critério original BEFORE502/AFTER200 agora passou, sem modificar baseline ou relaxar o nginx. Resultados internal/504 abaixo são históricos, não a prova final.

Este teste usa HTTP real pelo host, não browser nem gate fullstack. Não lê `.env` ou importa app, não usa fonte musical/LLM/DB ou faz chamadas externas de aplicação. A rede bridge não impede egress: offline deriva do comportamento explícito da fake; controles Settings/browser do gate principal pertencem ao Banco/Maestro. Limpeza não atingiu recursos deles.

## Prova anterior — rede internal, evidência histórica

Harness exclusivo ignorado: `.impeccable/runtime/backend_nginx_dns_proof.py`. Docker executado fora do sandbox conforme autorização; engine `29.8.0`. Sem API real, DB, `.env`, chave, fonte musical ou LLM. Nestas rodadas anteriores, cada rede era `internal`, com containers UUID/label `com.gandalf.backend-dns-proof`; subnet privada conferida contra uma subnet Docker e 21 rotas IPv4 do host, sem sobreposição (rota default excluída da comparação). Máximo dois containers simultâneos, nenhum volume/dado real e nenhuma porta publicada nas execuções via `docker exec wget`. Esse HTTP no loopback do nginx percorreu o proxy real até a API fake, mas não comprovou acesso pelo host.

Baseline imutável: `gandalf-frontend:latest`, ID `sha256:a98e49f30e1eb17ecc419d58e1b73d0e5fdb506c8b5f181cfe8afc3c7463af00`. Fake HTTP stdlib executada na imagem API existente por ID, sem importar aplicação/configuração. Imagem corrigida UUID derivada do baseline com somente `COPY nginx.conf`; build `--pull=false --network=none`, sem substituir tags existentes ou refazer bundle frontend.

Pedido idêntico nas provas:

```text
/api/v1/dns%20path/check?q=Jazz%20instrumental&x=%2F&x=a%2Bb&empty=
```

| Prova | Resultado |
| --- | --- |
| BEFORE — rede `192.168.226.0/24`, UUID `fa24ffc81dd3410d947cc1d5b7e39fa0` | Aquecimento 200/marcador A/path-query exatos; API A removida e B iniciada em IP distinto/same alias. Checagem de nginx ID/StartedAt preservados passou. Proxy antigo retornou **504 em 60,172s**, não o 502 previsto. |
| AFTER — rede `192.168.238.0/24`, UUID `f45b79d4c83140f89835902d3305fefe` | Aquecimento 200; API `192.168.238.10` removida, nova `192.168.238.11`, mesmo alias `api`. Após espera de 2s: **200**, marcador `after-B` e URI integral idêntica. nginx ID/StartedAt preservados; versão `1.30.5`, `nginx -t` exit0. Pedido respondeu em aproximadamente 0,125s; verificação completa em 0,203s. |

AFTER nginx ID: `e60111363a8a58ad5fe9a7dc62dad8d2f1bb18ec04c3ff3fcfe29fce8d955354`. Imagem própria `gandalf-backend-dns-f45b79d4c83140f89835902d3305fefe:patched`, ID `sha256:6ec6e3c063c6c17b2421f4473b897db542b8a443e3872f27225d45940691a436`.

Comandos executados:

```powershell
api/.venv/Scripts/python.exe .impeccable/runtime/backend_nginx_dns_proof.py
api/.venv/Scripts/python.exe .impeccable/runtime/backend_nginx_dns_proof.py --after-only
```

Evidências ignoradas: `backend-nginx-dns-proof-result.json` (BEFORE, exit1/NOT_PASSED pelo critério estrito 502), `backend-nginx-dns-proof-after-result.json` (AFTER, exit0/PASS). O segundo comando não repetiu BEFORE. A diferença 504/502 foi reportada ao Maestro: não alegar que o critério original 502 passou nem modificar o baseline para forçar esse status.

## Tentativas, limpeza e limites

Primeira tentativa parou no harness porque publicação de porta retornou lista vazia na rede internal; não concluiu aquecimento. Segunda terminou em assert, sem diagnóstico suficiente. Ambas tiveram limpeza verificada; evidências preservadas em `backend-nginx-dns-proof-preflight-result.json` e `backend-nginx-dns-proof-second-result.json`. A terceira instrumentou etapa/status e confirmou BEFORE504. Todas as execuções removeram apenas IDs próprios após conferir UUID/label/rede; rede vazia removida e ausência verificada. AFTER também removeu a tag de imagem própria após conferir ID/label. `cleanup_verified=true` em todas; baseline/tag existente preservados.

Patch e relatório final congelados e liberados ao Banco/Maestro; prova bridge BEFORE502/AFTER200 acima substitui a limitação histórica. A prova confirma recuperação do proxy após troca de IP, não disponibilidade sem interrupção, browser, auth, migrations ou persistência PostgreSQL. Gate fullstack pertence ao Banco/Maestro e não foi duplicado. Nenhuma suíte de produto repetida. Nenhuma edição fora da reserva, restart de serviço existente ou chamada externa de aplicação.

## Extensão autorizada — trust CA transitório no build pip

Após a prova DNS, Maestro autorizou o ajuste mínimo em `api/Dockerfile` para o erro de build `CERTIFICATE_VERIFY_FAILED / unable to get local issuer certificate` no índice PyPI. O RUN pip aceita `--mount=type=secret,id=gandalf_build_ca,required=false`: se o arquivo montado existe, somente o subprocesso pip usa `PIP_CERT=/run/secrets/gandalf_build_ca`; sem arquivo, mantém `pip install --no-cache-dir .`.

Não há TLSoff/trusted-host, COPY da CA, ENV persistente ou alteração de dependências/CMD/runtime. A CA pública existente e sua exportação ignorada são responsabilidade do Maestro; o mount é temporário de build. Não foi executado novo build/probe/teste pelo Backend nesta extensão, conforme instrução. Diff revisado e diff-check PASS; validação real do build com CA e gate fullstack permanece com Maestro/Banco. Dockerfile e este relatório liberados congelados, nginx permanece no hash anterior.
