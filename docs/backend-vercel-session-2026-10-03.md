# Backend Vercel — entrega congelada

Entrega concluída em 2026-10-04 (Brasil), no arquivo reservado na coordenação de 03/10. Publicação, Git e documentos compartilhados pertencem ao Maestro.

## Contrato implementado

- Root Directory `api`; entrypoint ASGI `vercel_app:app`, usando a factory atual `create_app(settings=...)`.
- `Settings(_env_file=None)`: configuração exclusivamente pelo ambiente. `DATABASE_URL` e `JWT_SECRET` são obrigatórios; segredo não vazio com pelo menos 32 bytes após retirar espaços das extremidades. Nunca são impressos.
- URL aceita `postgresql://` ou `postgresql+psycopg://`, normalizada para `postgresql+psycopg://`. Exige usuário, senha, banco, host com sufixo `.neon.tech` e porta ausente ou 5432. Rejeita SQLite, outros drivers, destinos arbitrários e parâmetros capazes de substituir o host.
- TLS obrigatório: `sslmode=require`, `verify-ca` ou `verify-full`. Somente parâmetros `sslmode`, `channel_binding` (`disable|prefer|require`) e `connect_timeout` (1–60 segundos) são permitidos; parâmetros repetidos são recusados. `require` exige criptografia, mas esta validação não comprova certificado/hostname ou conexão real. As formas de URL Neon com `sslmode=require&channel_binding=require` constam na [documentação oficial de conexão](https://github.com/neondatabase/website/blob/main/content/docs/cli/connection-string.md).
- `ONLINE_CATALOG`, `BOOK_PROVIDER`, `CORS_ORIGINS` e demais opções continuam seguindo os Settings existentes; o entrypoint não altera fontes/modelo/chaves/cotas nem ativa serviços pagos. Para primeira publicação offline, usar `ONLINE_CATALOG=false`, `BOOK_PROVIDER=local` e Groq ausente/vazio.
- Falhas de configuração/import/factory têm mensagens genéricas e contexto suprimido. Nenhuma DSN, senha, token, e-mail ou corpo upstream é registrado pelo entrypoint.

## Import e lifecycle

`app.main` tem `app = create_app()` no nível do módulo. Sua aplicação padrão é criada durante o import e normalmente chamaria `Settings()` com leitura de `.env`. O entrypoint primeiro valida seus próprios Settings e bloqueia `env_file` na configuração da classe somente durante esse import, restaurando o objeto original em `finally`. Não altera cwd ou ambiente do processo, nem lê `.env`. A aplicação padrão não é exportada por este entrypoint e seu lifespan não é iniciado.

A aplicação exportada tem outro conjunto de Settings, com URL normalizada. Não há migrations, uvicorn, conexão DB ou engine criado pelo entrypoint durante o import. O lifespan atual da factory cria seu engine e o descarta ao terminar; não executa migrations. `main`, auth, schema, session, Docker e CI não foram modificados.

O guard do import pressupõe inicialização sequencial do entrypoint no cold start. Ele não é uma solução geral para múltiplas construções concorrentes de Settings no mesmo processo durante o import. Retirar a aplicação padrão de `main` seria outra unidade, não autorizada nesta reserva.

## Evidência focada

Na cwd `api`, com o plugin temporário já existente que fornece diretórios com permissões herdadas:

```powershell
$env:PYTHONPATH = '../.impeccable/runtime'
.venv/Scripts/python.exe -m pytest -q -p no:tmpdir -p no:cacheprovider -p maestro_pytest_temp --tb=short tests/test_vercel_app.py
.venv/Scripts/ruff.exe check vercel_app.py tests/test_vercel_app.py
.venv/Scripts/ruff.exe format --check vercel_app.py tests/test_vercel_app.py
```

- **43 testes PASS em 1,33s**, com um warning conhecido de depreciação do TestClient/httpx. Ruff e formatação PASS.
- Cobertura: normalização e TLS; parâmetros duplicados/redirecionamento; segredo obrigatório; erros sanitizados; `.env` sintético ignorado inclusive na aplicação padrão; restauração do guard após falha; configuração/CORS preservados; factory real com lifespan e engine **fake**, health/status offline e dispose.
- A primeira execução teve 38 PASS/2 FAIL porque dois asserts comparavam a ordem textual dos parâmetros da URL; SQLAlchemy os reordena ao renderizar. Os asserts passaram a comparar a URL semanticamente. Nenhum comportamento de produção foi relaxado.
- Não foram usados `.env` real, PostgreSQL real, rede nos testes, API existente, LLM, migrations, Docker, build, suite geral ou publicação. A consulta documental pública não consumiu APIs do projeto.

## Freeze e limites

Arquivos exclusivos, sem stage/commit/push:

| Arquivo | SHA256 |
| --- | --- |
| `api/vercel_app.py` | `b1a99e21c2ea40f0865751163092fef482d7efd5dc5b1bebabaf0aac7b4ac0b6` |
| `api/tests/test_vercel_app.py` | `a287de6029612c8f5c652b7f8908d4a4036c558cad261fd10d53b02772f2f3d3` |

Código/testes congelados; relatório também liberado ao Maestro. Os testes não aprovam Vercel hospedada, TLS real Neon, migrations/extensions/permissões no banco remoto, autenticação pública, limites do plano ou custo zero. O Maestro deverá preparar o schema separadamente antes de publicar e validar readiness, sem migrations em requests/cold starts.

Pooling permanece o atual (`pool_pre_ping=True`), por engine/instância serverless. Seleção de endpoint pooled/direct e orçamento de conexões Free precisam validação na publicação, sem alterar `session.py` nesta unidade. O rate limiter em memória permanece por instância, sem promessa de limite global. Nenhuma publicação foi realizada pelo Backend.
