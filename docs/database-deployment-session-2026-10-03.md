# Gate descartável fullstack — 2026-10-03

## Resultado final consolidado pelo Maestro

Após o freeze do Banco, Maestro integrou CA pública BuildKit/diagnósticos/sanitização e rebind efêmero apenas da mesma API. **ca-7 PASS/exit0**, UUID `d611ad28-dff0-4523-abc0-8b6c049891aa`: builds atuais, PG18.6/READ COMMITTED/head0008/vector0.8.6/citext1.8, create7/verify6 checks, restart no mesmo API ID e sourcefreeze verificado. SQL2 contas/2 favoritos/1 playlist11 faixas/3 resultados públicos, ownership e fingerprints antes/depois/verify idênticos, AI0. Frontend/DB portas estáveis; API32782→32784 revalidada. Cleanup3 containers/rede/tags UUID PASS, sem dados existentes.

94 guards runner PASS/0,69s,67 Node/38 startup Backend; Ruff/format98/actionlint PASS. Artefato ignorado `.impeccable/ci/deployment-gate.json`, hash `a909c28c4569410e3fcd54883a0459bc5c72598a7e4e02669106240684fce9d2`. [Receita/evidência final](deployment-integration.md). Integração local offline aprovada; CI hospedada/publicação/rollout amplo continuam pendentes. As seções abaixo são checkpoints históricos do Banco e da integração, não substituem este resultado final.

## Escopo e contrato

Reserva Banco: `compose.deployment-test.yaml`, `scripts/deployment_gate.py`,
`api/tests/test_deployment_gate.py` e este documento. Maestro mantém Git, CI,
Compose de produção e documentos compartilhados; Backend mantém `deploy.py` e
nginx; Frontend mantém `frontend/tests/deployment.mjs`. Nenhuma alteração de
modelos, migrations, dados existentes ou chamadas a fontes/LLM.

CLI da raiz, com Docker/Compose local, Node e Playwright já disponíveis:

```text
GANDALF_DEPLOYMENT_ALLOW=isolated-coordinated python scripts/deployment_gate.py
```

Stdout contém um único JSON final `PASS`/`FAIL`; progresso vai para stderr.
CI pode redirecionar stdout para `.impeccable/ci/deployment-gate.json`.
O runner usa somente stdlib no host e as dependências da imagem API no SQL.
Não carrega `.env` da raiz nem `api/.env`: ambiente filho restrito e um
`--env-file` vazio próprio; `api.env_file` efetivo é removido pelo overlay.
Senhas descartáveis, JWT e URL ficam apenas no ambiente/memória dos recursos
próprios, sem credenciais nos artefatos. Docker inspect/config é capturado e
validado em memória, sem publicar seus conteúdos.

## Isolamento e verificações

- Merge obrigatório: `compose.yaml` + `compose.postgres.yaml` +
  `compose.deployment-test.yaml`; os Dockerfiles reais são herdados e ambos são
  construídos antes de `up`, com tags e labels UUID desta execução. Imagens
  antigas não são aceitas como prova do patch atual.
- PostgreSQL oficial local, `pull_policy: never`, digest
  `sha256:2ba9ca5f2e7daa0f0e7723cba1ee9167bab54efd3640516a44ac1a928dd67e7a`.
  Projeto, usuário e banco exclusivos por UUID. PG usa tmpfs de 512 MiB;
  volumes nomeados/binds e recursos persistentes herdados são recusados.
- Três portas publicadas como `127.0.0.1:0` para frontend/API/PG, distintas;
  portas de desenvolvimento `5173/8080/8000/8001/5432/5433/55432/55433` são
  proibidas. Rede bridge própria por UUID, não externa/host; online false,
  provider local e chave Groq vazia. Rede para instalar dependências no build
  foi autorizada. Não há alegação de firewall/isolamento de egress: Maestro
  reproduziu Docker 29.8 sem publicação de portas no modo `internal`, que
  inviabiliza o browser no host; a decisão coordenada foi `internal: false`.
  O runner recusa `internal: true` neste gate. Offline é verificado por
  configuração/status, bloqueio de requests externos no browser e SQL AI zero.
- Antes do navegador: IDs, imagens, labels, mounts, rede/portas e saúde;
  status real por nginx e API (`catalog=local`, AI não configurada/provider
  null); SQL via psycopg na API confirma engine PostgreSQL, banco/usuário UUID,
  head Alembic atual, vector/citext e baseline sem contas/favoritos/playlists.
  Readiness sozinho não certifica esses requisitos.
- Node `create` cria duas contas, dois favoritos BOOK/MUSIC e uma playlist;
  devolve IDs públicos e checks, preservando fixtures. PASSWORD é ambiente
  filho; TOKEN é UUID exato e ARTIFACT é arquivo próprio escrito após PASS.
  SQL confirma IDs, ownership, Argon2id, ordem das faixas, snapshots e cache
  público, com hashes sanitizados e consumo AI zero.
- Restart somente da API própria, mesmo ID/DB. SQL antes/depois compara
  contagens e fingerprints; Node `verify` faz relogin real e leitura pela UI,
  preservando fixtures para SQL final. Não repete o gate auth concorrente.
- Snapshot SHA256 dos inputs no início/fim detecta edições durante build/gate;
  não fixa hashes permanentes. A limpeza reinspeciona ID/image/labels/mounts
  imediatamente antes de remover containers próprios e rede própria sem
  endpoints estrangeiros; remove somente tags de build deste UUID. Sem prune,
  compose down genérico, volume remove ou restart de serviços existentes.
- Falhas imprimem somente etapa, classe, código de retorno/local de código
  seguro e resultado da limpeza; nenhum dump de exceção/SQL/DSN/segredo.
  Redirect HTTP é recusado antes de seguir Location, inclusive mesma origem;
  teste offline verifica ausência de segundo request. Builds parciais são
  descobertos mesmo sem registro anterior em memória: somente tag UUID exata,
  ID/image label e RepoTags verificados são removidos.

## Evidências até este checkpoint

**Gate real fullstack ainda pendente neste checkpoint.** nginx foi congelado
com resolução dinâmica; o build principal encontrou bloqueio TLS na imagem
API. O cenário de recriação de API/IP diferente é reservado ao Backend e
não é duplicado aqui; este gate conserva restart da API no mesmo ID.

- Docker normal recusou o pipe; preflight elevado autorizado: Engine 29.8.0,
  Compose 5.5.1, Linux e imagem PG digest presente. Serviços/dados existentes
  não foram usados.
- 60 testes offline de guards PASS; Ruff/format PASS. Frontend informa freeze e
  seu `--self-test` foi executado: 45 guards PASS, sem navegador/rede.
- Tentativa 1, UUID `78a05bea-4de8-4a3a-ab70-17a655e58c6e`: FAIL no preflight,
  sem build/container/rede criado; cleanup verified. Artefato sanitizado
  `.impeccable/runtime/deployment-gate-attempt-1.json`.
- Causa do preflight: Compose serializa `tmpfs.size` como string `536870912`;
  fixture usava inteiro. Guard passou a aceitar somente a representação
  decimal exata desse tamanho (não unidades/tamanhos alternativos); cobertura
  offline adicionada. Render RO confirmou Dockerfile/context herdados,
  publicação loopback efêmera e ausência de volumes nomeados no merge.
- Tentativa 2, UUID `5b5d47af-b3da-46b7-9d86-8527fe4de0d3`: FAIL no build,
  sem container/rede criado, cleanup verified. Artefato sanitizado
  `.impeccable/runtime/deployment-gate-attempt-2.json`. O stderr desta versão
  era capturado mas descartado; classificação sanitizada foi adicionada ao
  runner para as próximas falhas, sem logs brutos nos artefatos finais.
- Diagnóstico dirigido somente de build, UUID
  `4493fefc-1d1e-4093-a3ab-e77dcf01393f`: API falha em
  `RUN pip install --no-cache-dir .`; frontend não executado, sem containers
  e cleanup verified. Resumo
  `.impeccable/runtime/deployment-build-diagnostic-result.json`.
- Buildx 0.37.1 disponível; leitura RO do log já retido pelo BuildKit
  confirmou `CERTIFICATE_VERIFY_FAILED`/`unable to get local issuer certificate`
  no índice PyPI ao instalar o build dependency `setuptools>=68`.
  `No matching distribution` é consequência da falha TLS, não evidência de
  pacote ausente. Nenhum TLS foi desabilitado/imagem antiga usada como prova.
  Maestro/Backend foram avisados para coordenar confiança pública do builder;
  não foram alterados Dockerfiles ou truststores por este terminal.

## Continuação

### Consolidação pelo Maestro após liberação das reservas

- Integrada CA pública opcional via `compose.build-ca.yaml`: caminho explícito dentro de `.impeccable/runtime/`, PEM somente certificados, parse SSL e hash antes/depois; nenhum segredo em runtime. Dockerfiles API/frontend usam mount BuildKit transitório. Windows validou TLS PyPI com a CA Avast já instalada; não houve TLS desabilitado nem alteração de truststore global.
- Diagnóstico dos Dockerfiles atuais API/frontend PASS em UUID `719eb7f2-a180-4157-bc05-6f745a179ff3`, tags próprias removidas e cleanup verificado. Guards finais do runner: **74 PASS/0,75s**, incluindo CA e reconstrução sanitizada de diagnostics; Ruff/format CI completos PASS/98 arquivos. Tentativas sandbox de fixtures foram bloqueadas antes das asserções por permissão; rodada autorizada em temp UUID próprio passou.
- Primeiro gate com CA, UUID `9a284d9d-e753-41bb-9087-bcdccf6136f6`: build atual/startup/SQL PostgreSQL18.6/head0008/vector0.8.6/citext1.8/offline PASS; browser FAIL TimeoutError no estágio amplo account-a-register. Limpeza das três instâncias/rede/tags próprias verificada. Frontend acrescentou subpassos/diagnóstico de validade nativa e destino de login; causa exata daquela falha não comprovada. Artefato: `.impeccable/runtime/deployment-gate-final-ca-1.json`.
- Resultado integrado final deve ser conferido em `deployment-integration.md` e no topo de `DEVELOPMENT_LOG.md`. O checkpoint do Banco acima precede a extensão CA e permanece histórico; não usar sua pendência como resultado de uma rodada posterior.

Após resolver confiança TLS do builder de forma coordenada: executar runner
elevado autorizado com fontes congeladas, registrar JSON final,
três portas, engine/head/extensões/contagens, create/verify, restart,
fingerprints e identidade/cleanup. Não declarar aprovação por guards offline,
build isolado ou execução de uma versão anterior. CI hospedada permanece
pendente até execução do workflow pelo Maestro.
