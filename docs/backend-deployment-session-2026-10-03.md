# Backend — launcher de deploy — 2026-10-03

Entrega congelada e liberada ao Maestro/Banco para construção e gate de container.
HEAD consultado na entrada: `eca4145a145208f5fa0078b088c11ee5d1f82642`;
árvore inicialmente limpa. Lidos DEVELOPMENT_LOG, topos CONTINUATION e
IMPLEMENTATION_STATUS, launcher/config/Docker/compose e contrato de readiness.

## Achado e decisão coordenada

O Dockerfile executa `python local.py`. `local_settings` deliberadamente passa
SQLite, segredo JWT em arquivo local e CORS localhost como argumentos explícitos,
sobrescrevendo `DATABASE_URL`, `JWT_SECRET` e `CORS_ORIGINS` do ambiente. Isso é
correto para isolamento local, mas impede usar o mesmo comando para PostgreSQL
configurado no deploy. Readiness poderia aprovar SQLite quando o alvo pretendido
fosse PG. A regressão reproduziu os três valores sobrescritos em diretório novo.

Maestro aprovou **entrypoint separado** `api/deploy.py` e ampliou a reserva para
esse arquivo, `api/tests/test_deploy.py` e apenas COPY em `api/Dockerfile`.
`local.py`, `app/core/config.py`, `app/main.py`, auth/provider/schema ficaram
intactos. Sem flag GANDALF_DEPLOY ou mudança de comportamento do launcher local.
Compose opt-in PG e documentos compartilhados pertencem ao Maestro.

## Contrato implementado

`python deploy.py` carrega `Settings(_env_file=None)` do ambiente do processo.
Preserva URL, JWT, CORS e os campos existentes, sem chamar `local_settings`,
criar `.local`, SQLite em `/data` ou arquivo de segredo. Não lê `GANDALF_ONLINE`:
usa `ONLINE_CATALOG`/`BOOK_PROVIDER` do contrato Settings. Para gate offline,
ambos precisam ser explícitos: `ONLINE_CATALOG=false`, `BOOK_PROVIDER=local`,
`GROQ_API_KEY` vazio e credenciais descartáveis coordenadas pelo runner.

Antes de importar o aplicativo, migrar ou iniciar servidor:

- DATABASE_URL obrigatória e parseável. Suporta PostgreSQL `postgresql+psycopg`
  com host/database e porta válida, ou SQLite com database explícito em arquivo.
  Outros drivers/backends e SQLite em memória são recusados. Em memória, o
  engine de migração descartado não serviria o schema ao engine do aplicativo.
- JWT não vazio após strip e pelo menos **32 bytes UTF-8**, alinhado ao guard
  existente da autenticação; não modifica JWT, chave ou algoritmo.
- Configuração tipada existente precisa ser válida. CORS continua sendo lista
  JSON, não valores CSV dos exemplos antigos de documentação.
- `GANDALF_HOST` aceita IP literal ou localhost; default `0.0.0.0`.
  `GANDALF_PORT` aceita inteiro ASCII entre 1 e 65535; default8000.

Reutiliza `local.prepare(settings)`, que cria engine com a URL fornecida e passa
**essa conexão** ao Alembic/head; uma DATABASE_URL ambiente diferente após obter
Settings não redireciona a migração. Depois cria a aplicação com **a mesma
instância Settings** e chama Uvicorn. Engines de migração/aplicativo são distintos,
mas o alvo/configuração é o mesmo; não se alega compartilhar conexão física.
Falhas de config/prepare/factory impedem chamar o servidor. Boundary CLI aborta
com exit1 e mensagem fixa `Deployment startup failed.`, sem DSN, chave,
parametrização ou traceback da exceção capturada; exit0 após retorno normal.

Dockerfile somente copia deploy.py junto de local.py/alembic.ini. CMD local.py,
usuário não-root e demais defaults são preservados. O comando opt-in do compose
PG coordenado pelo Maestro será `python deploy.py`.

## Health/configuração e limite de import

`/health` indica processo; `/health/ready` verifica conexão, tabelas registradas
e pgvector (SQLite: not_required). `/api/v1/system/status` descreve configuração
de catálogo/IA, sem testar disponibilidade externa. Readiness não certifica
revision head, segredo JWT, qualidade de provider ou LLM. O entrypoint aplica
head e seu guard JWT; o gate Banco verificará independentemente DB/user UUID,
alembic head e extensões no alvo PG.

Limite RO mantido por coordenação: `app.main` ainda cria app default/Settings()
ao importar o módulo, inclusive pelo import de local.py. Nenhum patch dessa
factory foi autorizado nesta unidade. A factory servida recebe Settings explícito
do deploy. A imagem exclui `.env` via `.dockerignore`; os testes importam em cwd
temporária, nunca de `api/.env`. Não se alega eliminar a tentativa de dotenv da
instância default não servida, nem suportar dotenv real em um deploy direto fora
da imagem sem revisar esse comportamento.

## Evidência focada

Executado normalmente, somente `test_deploy.py`, com ambiente sintético limpo,
diretórios temporários e plugin tmp_path existente que herda ACLs do workspace.
Nenhum subprocesso de servidor, porta real, API8000, `.env` real, conta/segredo
real, provedor, LLM, PostgreSQL ou Docker foi usado nestes testes.

```powershell
# cwd api
$env:PYTHONPATH='../.impeccable/runtime'
& .venv/Scripts/python.exe -m pytest -q -p no:tmpdir -p no:cacheprovider -p maestro_pytest_temp tests/test_deploy.py --tb=short
& .venv/Scripts/ruff.exe check deploy.py tests/test_deploy.py
& .venv/Scripts/ruff.exe format --check deploy.py tests/test_deploy.py
```

Final **38 passed / 1 warning em 1.56s**. Rodada inicial36 passou; rodada final
após ajustes de lint e dois casos SQLite em memória. Ruff PASS, formato2 PASS,
diff-check seletivo dos três arquivos PASS. Único warning observado: depreciação
Starlette/HTTPX TestClient existente; sem mudança de dependências.

Casos: reprodução de local sobrescrevendo env; deploy preservando DB/JWT/CORS e
offline; recusa de dotenv para config do deploy; guards URL/secret/host/port e
Pydantic antes de filesystem/migração; falha sanitizada sem listen; mesma Settings
e ordem migrate→factory→serve; engine/connection/URL exatos usando fake; SQLite
novo realmente migrado com TestClient health/ready/status/CORS e cliente externo
proibido. Sem testes novos de auth, providers ou migrations reservadas ao Banco.

## Freeze

- `api/deploy.py`: SHA256 `AEEFA038633868344FF3EA289FDA84F6C9A2732FF951716A6FB8284FC8A6F8E4`
- `api/tests/test_deploy.py`: SHA256 `706E57C88180273035DCD56CCEDD8303C935DE901935185878BB69B6DAC83CCB`
- `api/Dockerfile` no freeze inicial, antes da extensão CA: SHA256 `6B3CB9DF5CCD45BB060F9EC106BFA6AE131A97B50DB93AFE04E8EB207407704C`

Código congelado antes de concluir este relatório; Banco e Maestro avisados.
Sem edição/stage/commit/push pelo Backend nos arquivos compartilhados ou dos
colegas. Nenhum processo/dado/chave existente modificado ou reiniciado. Não foi
repetida suíte geral. Gate PG + API container + frontend nginx depende da execução
coordenada seguinte; esta entrega não o declara aprovado nem libera produção.

## Extensão coordenada — confiança do builder

O build atual encontrou inspeção TLS com CA Avast já confiada no Windows, mas ausente no builder. O Backend acrescentou um segredo BuildKit opcional `gandalf_build_ca`: quando presente, `PIP_CERT` vale somente para `pip install`; ausência mantém a instalação anterior. Sem TLS desabilitado, mudança de dependências ou cópia da CA para a imagem. O hash Dockerfile após a extensão foi `FF105C461D090F5DA2D6FE3C2A43D6540810FB5A14B360176A0E76F3CEB564AC`.

Maestro executou o diagnóstico de build dos Dockerfiles atuais API e frontend em tags UUID próprias: ambos PASS, cleanup verificado. Essa evidência cobre o build e não substitui o gate navegador/PostgreSQL. Resultado integrado final e limites em `deployment-integration.md` e `DEVELOPMENT_LOG.md`.
