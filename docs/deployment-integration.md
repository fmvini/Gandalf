# Integração de deploy com PostgreSQL

## Caminho executável

O Compose padrão continua usando `api/local.py`, com SQLite persistente e o modo online legado. Para usar PostgreSQL, combine `compose.yaml` com `compose.postgres.yaml`: esse overlay seleciona `python deploy.py`, aguarda o banco saudável e fornece a configuração explícita ao backend. O frontend é o build estático servido pelo Nginx de `frontend/Dockerfile`; `/api/` é encaminhado para `api:8000` e as rotas SPA têm fallback para `index.html`.

`api/deploy.py` lê o ambiente do processo, exige banco e segredo JWT válidos, aplica migrations na conexão configurada e só então inicia a API. Não gera um segredo local para substituir `JWT_SECRET`. O entrypoint local permanece disponível para desenvolvimento.

## Configuração

Copie `.env.postgres.example` para `.env.postgres`, que é ignorado pelo Git, e substitua os valores de exemplo. `POSTGRES_PASSWORD` e a senha em `GANDALF_DEPLOY_DATABASE_URL` devem corresponder; na URL, caracteres reservados da senha precisam de percent-encoding. Dentro da rede Compose, o destino é `db:5432`, mesmo que o PostgreSQL local esteja em outra porta. `POSTGRES_DB` e `POSTGRES_USER` também devem corresponder à URL.

Use um `JWT_SECRET` aleatório estável de pelo menos 32 bytes e conserve-o entre reinícios. `CORS_ORIGINS` é um array JSON: `[]` atende à interface pelo proxy de mesma origem; para uma interface em outro domínio, informe as origens exatas. As variáveis reais de autenticação são `JWT_SECRET`, `ACCESS_TOKEN_MINUTES` e `REFRESH_TOKEN_DAYS`.

O exemplo começa com `ONLINE_CATALOG=false` e `BOOK_PROVIDER=local`, sem chamadas a fontes externas ou IA. O Compose base pode carregar `api/.env` no serviço; valores explícitos do overlay têm precedência. Para ativar o catálogo experimental, configure conscientemente `ONLINE_CATALOG=true` e `BOOK_PROVIDER=open_library` e consulte os limites em `docs/IMPLEMENTATION_STATUS.md`. Credenciais não pertencem ao frontend.

```powershell
Copy-Item .env.postgres.example .env.postgres
# Edite .env.postgres e substitua os valores de exemplo antes de iniciar.
docker compose --env-file .env.postgres -f compose.yaml -f compose.postgres.yaml up --build -d
```

Interface: `http://127.0.0.1:8080`. API direta: `http://127.0.0.1:8001`; readiness: `/health/ready`. O banco fica na rede do Compose, sem porta publicada. O volume `gandalf_postgres_data` conserva os dados; não use `down -v` em um ambiente que contenha contas reais. Essas portas vêm do Compose base; não inicie se já estiverem ocupadas.

O proxy usa resolução dinâmica de `api` pelo DNS do Docker (`127.0.0.11`), com cache de um segundo, mantendo caminho e query da requisição. Isso permite descobrir o novo IP quando a API é recriada sem recriar o Nginx. A recuperação após troca de IP não elimina a indisponibilidade durante a substituição da única API. Referências: [proxy_pass do Nginx](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_pass), [resolver](https://nginx.org/en/docs/http/ngx_http_core_module.html#resolver) e [DNS de redes Docker](https://docs.docker.com/engine/network/#dns-services).

Essa receita prepara containers locais. Publicação, HTTPS, backups, segredos do provedor e execução hospedada da CI exigem configuração do ambiente de destino. Migrations automáticas deste entrypoint foram desenhadas para uma única API; um rollout com múltiplas instâncias precisa serializar migrations separadamente.

Para um banco gerenciado, configure a URL do destino e disponibilize as extensões `vector` e `citext` e as permissões necessárias às migrations antes de iniciar. A imagem PostgreSQL do Compose fornece essas extensões; o gate local não certifica as permissões de um serviço gerenciado.

## Confiança TLS durante o build

Em hosts com inspeção TLS, o builder pode precisar da CA pública que o administrador já instalou e confiou no host. O erro `CERTIFICATE_VERIFY_FAILED` não deve ser contornado desativando a verificação. Exporte somente o certificado público aprovado para um arquivo PEM fora do Git e use o overlay opcional `compose.build-ca.yaml`, depois dos overlays normais, com `GANDALF_BUILD_CA_CERT` apontando para esse arquivo.

O BuildKit monta `gandalf_build_ca` somente no comando de instalação: `PIP_CERT` para pip e `NODE_EXTRA_CA_CERTS` para npm. A CA não é copiada para a imagem nem montada nos serviços em execução. Sem o overlay, o build mantém sua confiança padrão. Para o gate, o arquivo deve estar dentro de `.impeccable/runtime/`; o runner valida o PEM público e verifica seu hash antes e depois da execução. Não exporte chaves privadas nem substitua uma CA sem conferir sua origem. Referências: [segredos de build Docker](https://docs.docker.com/build/building/secrets/), [certificados HTTPS do pip](https://pip.pypa.io/en/stable/topics/https-certificates/) e [NODE_EXTRA_CA_CERTS](https://nodejs.org/api/cli.html#node_extra_ca_certsfile).

Exemplo após disponibilizar o PEM público aprovado nesse caminho:

```powershell
$env:GANDALF_BUILD_CA_CERT = (Resolve-Path .impeccable/runtime/build-ca-bundle.pem).Path
docker compose --env-file .env.postgres -f compose.yaml -f compose.postgres.yaml -f compose.build-ca.yaml up --build -d
```

O runner do gate acrescenta esse overlay automaticamente somente quando a variável explícita está presente. A CI hospedada usa a confiança padrão do builder, sem esse arquivo local.

## Gate descartável

`scripts/deployment_gate.py` e `compose.deployment-test.yaml` exercitam o Compose base e o overlay PostgreSQL com dados descartáveis. O gate deve construir as imagens do checkout atual, usar UUID exclusivo, banco/tmpfs e portas loopback efêmeras; não utiliza `api/.env` nem os serviços existentes. Os containers usam uma rede bridge exclusiva do projeto, como a receita de deploy. Não há bloqueio de egress por firewall: o catálogo/IA estão offline, a chave Groq é vazia, o navegador recusa requisições externas e o SQL exige zero chamadas IA. Dependências de build podem usar a rede.

No Docker 29.8 testado, `internal: true` deixou as portas publicadas sem bindings efetivos, mesmo com containers ativos. Um probe isolado reproduziu o comportamento e removeu seus próprios recursos; por isso o gate host/Chromium usa a rede bridge comum e valida isolamento por identidade de projeto/dados e modo offline. Não confundir esses checks com uma política de firewall de produção.

O teste `frontend/tests/deployment.mjs` usa Chromium contra Nginx, sem Vite nem respostas simuladas de API. O runner verifica a identidade PostgreSQL e as migrations por SQL, além de health/readiness/status. As fases de navegador e reinício verificam os fluxos públicos, autenticação, favoritos e playlists, incluindo isolamento entre contas e persistência.

O resultado final só deve ser aprovado se todos os checks e a limpeza dos recursos próprios passarem. Os guards offline não substituem uma execução real. Este gate não aprova a qualidade das fontes musicais, corridas HTTP entre várias APIs, HTTPS, produção ou o runner hospedado.

Pré-requisitos: Docker Linux/Compose com suporte a `!reset`/`!override`, Python, Node, dependências instaladas em `frontend` e Chromium do Playwright. A imagem PG fixada em `compose.postgres.yaml` precisa estar disponível localmente; a CI faz o pull explícito antes do gate. O runner constrói as imagens API/frontend do checkout atual.

Na raiz, em PowerShell:

```powershell
$env:GANDALF_DEPLOYMENT_ALLOW = 'isolated-coordinated'
.\api\.venv\Scripts\python.exe scripts/deployment_gate.py
```

Em Linux ou com outro Python preparado, use `GANDALF_DEPLOYMENT_ALLOW=isolated-coordinated python scripts/deployment_gate.py`. Progresso sai em stderr; stdout contém um único JSON final e exit0 só ocorre com todos os gates e limpeza aprovados. `npm run test:deployment-state` em `frontend` executa somente guards offline; `test:deployment` depende do ambiente exclusivo montado pelo runner e não faz parte de `npm test` comum.

## Validação local — 2026-10-03

Gate final **PASS/exit0**, UUID `d611ad28-dff0-4523-abc0-8b6c049891aa`, Docker29.8/Compose5.5.1, builds atuais API/frontend com CA pública temporária. PostgreSQL18.6/READ COMMITTED, Alembic `0008_favorites`, vector0.8.6 e citext1.8 confirmados por SQL. Create7 checks e verify6 checks passaram no Chromium contra Nginx real.

SQL confirmou duas contas, dois favoritos, uma playlist com11 faixas e três resultados públicos. Snapshots e cache conservaram os mesmos hashes antes do restart, após restart e após verify; zero chamadas IA. Frontend/DB permaneceram nas mesmas portas; a porta efêmera da mesma API mudou32782→32784 e foi revalidada por ID/labels/loopback antes de retomar os checks. A receita normal usa portas fixas.

Zero erros de browser/console/requisições externas. Chromium registrou aborts nos logouts204:4 em create/2 em verify, aceitos somente após correlacionar o mesmo Request a204 real, refresh atual, UI deslogada e refresh revogado401; nenhuma exceção genérica por endpoint. Guards:38 startup Backend,94 runner e67 Node; Ruff/format98 arquivos/actionlint PASS. Prova DNS separada BEFORE502→AFTER200 conservou URI e o mesmo Nginx após trocar o IP da API.

Sourcefreeze e cleanup PASS: três containers, rede e tags UUID removidos; dados/serviços existentes preservados. Artefato sanitizado ignorado `.impeccable/ci/deployment-gate.json`, SHA256 `a909c28c4569410e3fcd54883a0459bc5c72598a7e4e02669106240684fce9d2`. Snapshot salvo SHA256 `7fa37ac90109836a08fb13c816b8be0184c849e1a24ae2170669de83924d171e`; cache público `da0237ee80a97dce448f19a6eb05219cdd319c57ebc0a867b41b9770dc8ad39f`.

Essa evidência valida integração local offline com uma API. CI hospedada, HTTPS/deploy público, permissões de banco gerenciado, backups, fontes online/G1 e rollout misturando versões/APIs continuam pendentes. A documentação de CI fica em `CI.md`; os relatórios dos três agentes registram os checkpoints e limites por camada.
