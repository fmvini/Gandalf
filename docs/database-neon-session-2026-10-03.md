# Neon — migrations opt-in — sessão 2026-10-03

## Entrega congelada, Neon real PENDENTE

Preparação iniciada em03/10 e finalizada em04/10/2026 (horário do Brasil).
Implementados somente `api/scripts/neon_migrate.py`,
`api/tests/test_neon_migrate.py` e este documento exclusivo. Nenhuma alteração
em schema/models/migrations, auth, API/Frontend, Git ou docs compartilhados.
Maestro serializa log/commits. Nenhum Neon real, Docker, PG existente ou `.env`
real foi usado; pesquisa pública documental não é execução do banco.

**60 testes focados offline PASS em0,41s**, sem SQLite/PG/rede; guards e
protocolo de conexão/transação simulados com fakes. Ruff PASS, dois arquivos
já formatados. Os resultados não aprovam migrations, locks ou TLS em Neon.

SHA256 congelados:

- Script: `204d16b5735187d0eae67318aefcaa6cc341ad284a07872f93c14d9077d54132`.
- Testes: `17329a822d8f490fc6a5ed0566ab6683f78346d836ed24f0ec0d4dd426ace820`.

Adendo de coordenação: usuário informou projeto existente
`round-rice-47636561`, branch `production`. Maestro conduz Neon CLI
login/link/config init/deploy solicitado, plano e identidade/schema READ ONLY
antes de qualquer migration. Não criar outro projeto/banco ou integração
Vercel; não presumir schema vazio. Este terminal não fez novas probes/rede ou
testes após freeze. Código/testes permanecem nos hashes acima; somente este
documento foi reconciliado com a nova informação.

## Contrato CLI e validação

Execução manual serial, fora do startup da API:

```text
GANDALF_NEON_MIGRATE=owned-project
NEON_DATABASE_URL_UNPOOLED=<URL direta do projeto próprio, somente childenv>
api/.venv/Scripts/python.exe api/scripts/neon_migrate.py
```

Sem argumentos/URLs em argv, dotenv, fallback DATABASE_URL, retry automático,
seeding ou import de app.main. O opt-in é declaração explícita do operador:
hostname e SQL identity não comprovam propriedade da conta/projeto Neon.
Maestro deve primeiro confirmar ownership/plano, identidade e schema do
projeto existente e fornecer contrato explícito, sem publicar credenciais.
Nenhuma migration real autorizada nesta entrega. O CLI não exige banco vazio:
aplica a sequência Alembic existente até head, portanto a revisão prévia do
schema e da revisão atual é necessária antes de decidir pela execução.

Validação stdlib ocorre antes dos imports runtime/DNS/connect:

- Aceita postgres/postgresql/postgresql+psycopg e normaliza para o driver
  psycopg existente. Exige username/password/db não vazios, porta ausente
  ou5432, endpoint público `ep-...` em domínio AWS/Azure Neon.
- Recusa pooler, SQLite/loopback/outro domínio, fragmento, espaço/control,
  query duplicada, hostaddr/host/service/options e qualquer parâmetro fora de
  sslmode/channel_binding. Exige sslmode=require/verify-ca/verify-full;
  channel_binding opcional prefer/require. Não aceita TLS disable/prefer.
- Cwd vazio próprio e whitelist de ambiente sistema durante imports/migrate:
  remove PG*, DATABASE_URL, JWT/LLM/segredos/SSL overrides herdados. Restaura
  cwd/env/sys.path/logging ao terminar; remove somente o diretório vazio próprio.
  Nenhuma dependência de um novo módulo reservado pelo Backend; validação
  específica do comando permanece nesta reserva, sem editar o entrypoint dele.

## Migração e prova SQL

Engine NullPool, psycopg, READ COMMITTED, connect_timeout10s,
statement_timeout60s/lock_timeout10s, prepare_threshold=None. Uma conexão:

1. Dentro da transação, compara current_database/current_user com a URL em
   memória; exige TLS ativo no cliente libpq e citext/vector disponíveis.
2. `pg_try_advisory_xact_lock` usa chave int64 estável com namespace do CLI.
   Se outro CLI cooperante já migra, recusa imediatamente antes do upgrade.
   Lock transacional liberado em commit/rollback/fechamento.
3. Alembic `upgrade head` recebe config.attributes.connection exatamente igual
   à conexão validada, com transação externa; head único resolvido do repo e
   versão conferida antes do commit. Não muda alembic/env.py ou migrations.
4. Nova transação READ ONLY na mesma conexão reconfirma identity/head e
   versões instaladas citext/vector. Engine descartada no finally.

stdout é somente um JSON final. PASS contém head/extensões, modo TLS,
tls_active/direct_connection/identity_verified/serial_lock/readonly_verified;
falha exit1 contém somente status NOT_PASSED, etapa allowlist interna e
error_class fixa MigrationError. Não publica URL/host/user/password/SQL ou
exception; logs runtime stdout/stderr são suprimidos durante a operação.

Limitações: advisory serializa somente comandos que adotem a mesma chave;
não controla migrations executadas por outros launchers. Prova READ ONLY é
depois do commit: falha de verificação pode ocorrer após migrations já
confirmadas, não significa rollback do schema. `sslmode=require` exige
criptografia; não equivale a autenticação de hostname por verify-full.
`verify-*` pode depender de CA disponível ao libpq; não desabilitar TLS se
falhar. Novas migrations devem ser revisadas quanto à transação externa.

## Pesquisa oficial e implicações para Vercel/Neon

- [Extensões Neon](https://neon.com/docs/extensions/pg-extensions): lista
  citext e pgvector, instalado com nome SQL vector. Na referência consultada,
  PG18 lista citext1.8/vector0.8.6; PG14–17 listam citext1.6/vector0.8.0.
  CLI verifica disponibilidade e reporta versão real, sem exigir versão PG18.
- [Pool Neon](https://neon.com/docs/connect/connection-pooling): PgBouncer em
  modo transaction; endpoint -pooler recomendado para workloads serverless,
  direto recomendado para migrations e recursos de sessão. O comando recusa
  pooler deliberadamente. Isso não obriga a API a usar o mesmo endpoint.
- [Psycopg preparado/PgBouncer](https://www.psycopg.org/psycopg3/docs/advanced/prepare.html):
  suporte depende de versões/config de PgBouncer/libpq; prepare_threshold=None
  desliga preparação automática. CLI usa direto e essa configuração explícita;
  configuração runtime da API pertence ao Backend, não foi alterada aqui.
- [Regiões Neon](https://neon.com/docs/introduction/regions): projeto tem
  região fixa, escolha perto da função API. Referência lista AWS us-east-1,
  us-east-2, us-west-2, eu-central-1, eu-west-2, ap-southeast-1,
  ap-southeast-2 e sa-east-1. Disponibilidade real da conta deve ser conferida;
  não provisionamos nenhuma região. iAD1/us-east-1 é opção coerente se essa
  for a região escolhida para a função, não decisão de provisionamento.
- [Integração Neon/Vercel](https://neon.com/docs/guides/vercel-overview):
  opções Vercel-managed, Neon-managed e manual; diferem em billing e limpeza
  de branches preview. Conexão manual por env permite controle explícito da
  migração; não implica integrar marketplace ou criar branches automaticamente.
- [Vercel Hobby](https://vercel.com/docs/plans/hobby): gratuito com limites e
  destinado a uso pessoal não comercial. Não ativar plano pago/upgrade nesta
  tarefa; não afirmar gratuidade ilimitada ou aprovação de uso comercial.

Páginas Neon foram verificadas também no repositório oficial
[neondatabase/website](https://github.com/neondatabase/website/tree/main/content/docs),
pois o fetch de neon.com retornou text/markdown não suportado. Fontes acima
são pesquisa de compatibilidade; live e deploy público seguem pendentes.

## Continuidade

Maestro recebe freeze/contrato e integra docs/log/commit seletivo. Próximo
passo: setup solicitado no projeto `round-rice-47636561`/branch `production`,
conferência READ ONLY de plano/ownership/identidade/schema/revisão atual, sem
assumir base vazia e sem criar outra integração. Somente após contrato e
autorização de migration reais, coordenar credenciais em childenv e executar
este CLI, registrando JSON sanitizado/head/ext/TLS reais. Se falhar,
identificar etapa sem imprimir exception/URL e coordenar
correção comprovada. A aprovação dos gates locais PG anteriores não substitui
Neon ou Vercel reais; nenhuma execução adicional autorizada neste terminal.
