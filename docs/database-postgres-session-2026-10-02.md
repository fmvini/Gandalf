# Gate PostgreSQL/pgvector — preparação de 2026-10-02

## Estado e escopo

- HEAD inicial `ffdd6a6`, árvore limpa; consultados DEVELOPMENT_LOG, CONTINUATION e `database-session-2026-10-02.md`. Checkpoint anterior tem 366 testes API aprovados, inclusive os três multiprocessos SQLite: essa aprovação não é PostgreSQL real.
- Banco reserva somente este relatório e eventual modelo/migration se surgir bug confirmado. Nenhum bug de schema confirmado nesta preparação; nenhuma alteração em API/frontend/modelos/migrations/testes versionados, Git ou documentos compartilhados.
- Maestro autorizou harness **ignorado**, sem versioná-lo antes de execução real, e reservou `.github/workflows/ci.yml`/`docs/CI.md` para integração futura. Nenhum container iniciado; aguardar coordenação antes da execução descartável.

## Disponibilidade atual: normal e elevada, somente leitura

| Verificação | Evidência |
|---|---|
| Context Docker ativo | `desktop-linux`; contexto alternativo `default` também identificado. |
| `docker version`, `ps`, `images` normais | Pipe `dockerDesktopLinuxEngine` inexistente. Imagens/containers não inventariáveis; não afirmar que não há imagem instalada. |
| `docker --context desktop-linux version/image ls` elevado | Mesmo pipe inexistente. Não é mero bloqueio de acesso do sandbox demonstrado. |
| `docker --context default version/image ls` elevado | Pipe `docker_engine` também inexistente. |
| `docker compose -f api/compose.yaml config --no-interpolate` elevado | YAML válido: `pgvector/pgvector:0.8.6-pg18`, porta 5433 e volume persistente `api_gandalf_pgdata`. Nenhuma variável/segredo interpolado. Não usar esse volume para o teste descartável. |
| `pg_isready` em 5432/5433 | 5432 aceita conexões; 5433 sem resposta. Não houve autenticação nem tentativa de senha. |
| Listeners consultados com permissão elevada | Somente 5432, PID 10140, nos candidatos 5432/5433/55432/55433. 55432/55433 sem listener **naquele instante**, verificar novamente antes de executar. |
| Serviço/extensões locais | PostgreSQL18 preexistente em execução. Nenhum arquivo `*vector*` nos diretórios `share/extension` e `lib` da instalação 18. Sem consulta autenticada de extensões nem inferência sobre outros servidores. |

**Resultado:** nenhuma instância PostgreSQL/pgvector descartável acessível nos endpoints verificados. Não iniciar Docker Desktop/serviços por inferência, não modificar PG18/5432, adivinhar credenciais, instalar extensão, puxar imagem ou usar dados/volume existentes. Gate real continua pendente.

## Lacuna concreta de integração

- `api/tests/test_migrations.py::test_postgresql_migration_generates_extensions_and_tables` usa `command.upgrade(..., sql=True)` e não abre PostgreSQL.
- Fixtures de `test_migrations.py`, `test_favorites.py` e `test_recommendation_cache.py` constroem URLs SQLite nos temporários. Exportar `DATABASE_URL` **não converte** esses testes em testes PostgreSQL.
- `.github/workflows/ci.yml` declara SQLite/provedores simulados e não tem serviço PostgreSQL/pgvector. Schema, JSONB/CITEXT/ARRAY/timestamptz, READ COMMITTED, upsert/RETURNING e advisory lock ainda carecem de execução real em conjunto.
- Alembic já aceita `Config.attributes['connection']`; `FavoriteService`, `RecommendationCache` e sessionmaker já usam o dialeto do engine. SQLAlchemy, psycopg, Alembic, FastAPI TestClient e pytest estão nas dependências existentes. Não é necessário adicionar dependência ou modificar schema para executar esse gate.

## Harness preparado, sem integração executada

Arquivo local ignorado: `.impeccable/runtime/postgres_gate.py`. Importa o código atual; não duplica implementação de favoritos/cache e não usa SQLite. Não é artefato versionado nem integração aprovada.

Proteções antes da primeira mutação:

- Flag de coordenação `GANDALF_PG_GATE_ALLOW=isolated-coordinated` explícita.
- URL aceita somente `postgresql+psycopg`, loopback, porta 55432/55433, usuário `gandalf_gate`, banco `gandalf_gate_{32hex}`, sem parâmetros que redirecionem conexão.
- Consulta real deve confirmar database/user esperados, **nenhum objeto de usuário** (tabelas/partições/views/materialized views/sequências/foreign tables fora de schemas de sistema) e `vector`/`citext` disponíveis. Recusa com exceção explícita; proteções não dependem de assert/`python -O`.
- Essas validações são barreiras contra engano, não prova de que um servidor inteiro é descartável. Maestro deve verificar container/imagem/label/porta/banco antes de liberar a execução.
- Migration recebe conexão validada diretamente; não consulta DATABASE_URL/.env para selecionar alvo. Sem CREATE/DROP DATABASE e sem limpeza global. Se falhar após começar, deixa o banco **descartável** intacto para diagnóstico; não apaga estado automaticamente.
- Saída do boundary redige exceções para classe/status, sem DSN/senha/SQL/corpos. Um erro gera `NOT_PASSED`, nunca PASS parcial. Execução com `python -O` é recusada explicitamente, pois suprime asserções funcionais.

Cobertura proposta pelo arquivo:

1. Upgrade base→0007; duas contas sintéticas; upgrade→head; paridade metadata e READ COMMITTED real; versões/extensões e operações reais vector/citext; readiness PostgreSQL via TestClient local/offline, sem servidor adicional/provedores.
2. Seis POSTs equivalentes via `FavoriteService` em três processos independentes: um ID comum/uma criação; primeira data/proveniência/snapshot preservados em repetição; DELETE/status de outra conta isolados, timezone de data presente.
3. Dois processos criando/repetindo e um excluindo, 20 operações por processo; cada retorno de criação exige snapshot correto e contagem final MUSIC no cenário ≤1.
4. TTL de cache na fronteira com relógio controlado, sem extensão ao ler/repetir; três processos publicando/lendo 95 origens cada; limite global 256 real usando advisory lock. Favorito sobrevive à remoção da origem; cascata da conta preserva outra conta.
5. Downgrade 0008→0007 preservando outra conta, upgrade→head e downgrade→base em banco exclusivamente descartável. JSON de PASS somente após todos os passos, com versões/checks/timestamp, sem credenciais.

Limites: stress concorrente não determina todas as interleavings nem substitui um cenário de bloqueio controlado. Não cobre ainda HTTP autenticado entre duas instâncias PostgreSQL, todas as constraints negativas, rollout em banco pré-populado ou refresh concorrente. Após primeiro smoke real, incorporar testes versionados parametrizados PostgreSQL e esses casos conforme achados, antes de considerar todo o gate fechado. Se ProcessPoolExecutor falhar antes dos workers, registrar ambiente como pendente, sem trocar por aprovação SQLite/thread.

## Verificação local efetivamente executada

- Compilação em memória e import do harness passaram; nenhum engine/conexão PostgreSQL criado nessa verificação.
- **13 recusas explícitas** passaram: nove URLs perigosas (5432, 5433, host remoto, DB normal, usuário postgres, query de redirecionamento, driver diferente, nome inválido e porta 8000) e quatro estados perigosos (schema ocupado, identidade DB divergente, usuário divergente e ausência vector).
- Três controles válidos passaram: URLs 55432/55433 e preflight puro de DB vazio com identidade/extensões esperadas. Não afirmam que tal DB existe.
- Ruff check e format --check do harness passaram. Import mantém aviso Starlette/httpx conhecido.
- Invocação sem flag de coordenação recusou com `{"status":"NOT_PASSED","error_class":"ValueError"}` e exit 1, antes de conexão. Resultado esperado de proteção, não falha de aplicação.
- Nenhum teste de integração PostgreSQL, container, autenticação PG, migration real ou suíte SQLite foi executado nesta preparação.

## Plano executável após coordenação do Maestro

Pré-condições: Docker daemon acessível; `docker image inspect pgvector/pgvector:0.8.6-pg18` confirma imagem **local** (não pull); nova verificação de porta livre e ausência de outro gate. Não executar comandos abaixo antes da coordenação.

Em PowerShell, na raiz do projeto, após conferir essas condições:

```powershell
$gateToken = [guid]::NewGuid().ToString('N')
$gateContainer = "gandalf-pg-gate-$gateToken"
$gateDatabase = "gandalf_gate_$gateToken"
$gatePassword = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
$gateImage = 'pgvector/pgvector:0.8.6-pg18'
docker image inspect $gateImage --format '{{.Id}}'
if ($LASTEXITCODE -ne 0) { throw 'Imagem local indisponível; não executar pull.' }
if (Get-NetTCPConnection -State Listen -LocalPort 55432 -ErrorAction SilentlyContinue) { throw 'Porta ocupada.' }
docker run --pull=never --name $gateContainer --label 'com.gandalf.disposable-gate=true' --mount 'type=tmpfs,destination=/var/lib/postgresql' -p '127.0.0.1:55432:5432' -e "POSTGRES_DB=$gateDatabase" -e 'POSTGRES_USER=gandalf_gate' -e "POSTGRES_PASSWORD=$gatePassword" -d $gateImage
if ($LASTEXITCODE -ne 0) { throw 'Container não iniciou; não executar harness.' }
docker inspect $gateContainer --format '{{.Id}} {{.Config.Image}} {{json .NetworkSettings.Ports}} {{json .Mounts}}'
docker exec $gateContainer pg_isready -U gandalf_gate -d $gateDatabase
```

O último comando pode precisar ser repetido até pronto com prazo curto; não executar gate enquanto retorna falha. Mount é tmpfs exclusivo do container, sem volume/bind do projeto; confirmar mounts/label/porta antes da escrita. A senha é nova, descartável e não deve ser impressa nem colocada em documentação/logs. Os nomes/UUIDs acima evitam confusão com PG18/gandalf; não usar `api/compose.yaml up` neste gate.

Depois de readiness, ainda na mesma sessão PowerShell:

```powershell
$env:GANDALF_PG_GATE_URL = "postgresql+psycopg://gandalf_gate:${gatePassword}@127.0.0.1:55432/$gateDatabase"
$env:GANDALF_PG_GATE_ALLOW = 'isolated-coordinated'
Push-Location api
try { & .\.venv\Scripts\python.exe ..\.impeccable\runtime\postgres_gate.py }
finally { Pop-Location }
$gateExit = $LASTEXITCODE
Remove-Item Env:GANDALF_PG_GATE_URL, Env:GANDALF_PG_GATE_ALLOW
if ($gateExit -ne 0) { throw 'Gate não aprovado: preservar container descartável para diagnóstico.' }
```

Não publicar porta em 0.0.0.0 nem permitir migrations no servidor existente. Ao fim, Maestro pode remover **somente** `$gateContainer` após conferir ID/label criados nessa rodada; não usar prune, compose down -v nem apagar volumes/bancos gerais. Não incluir comando destrutivo automático no harness. Na falha, capturar classe/etapa com segurança antes de limpeza; não declarar PASS porque o container iniciou.

## Coordenação online: observação adicional somente leitura

Backend é único responsável por uma consulta pública por fonte e, somente se ambas responderem, uma interpretação Groq. Banco não faz probes externos/LLM nem consulta corpos/chaves/prompts.

Baseline próprio em `api/.local/gandalf.db`, mode=ro/query_only/transação, Unix ms `1790961236865`, dia UTC 2026-10-02: **2 chamadas Groq**, limite 50 conforme contrato/documentos. Contagens: 1 cache BOOK/open_library, 6 ONLINE/groq e 1 origem de recomendação, todos expirados. Somente agrupamentos de tipo/provedor/validade foram consultados.

Backend informou conclusão do diagnóstico inicial às 17:14:51 UTC: uma consulta pública por fonte, ambas com `SSLCertVerificationError`/verify_code 20 no **cliente diagnóstico HTTPX padrão/certifi**, antes de HTTP; Groq não chamado nessa tentativa. Leitura própria às **17:17:16 UTC**, Unix ms `1790961436991`, confirmou **2→2 chamadas**, mesmas contagens e linhas ainda expiradas. Essa leitura antecede a rodada corrigida e não descreve o consumo final. Não registrar TLS da aplicação como bloqueado a partir desse diagnóstico.

Rodada corrigida informada pelo Backend, encerrada **17:17:39 UTC**: `external_client` real da aplicação/trust store do sistema, Open Library HTTP 200 e MusicBrainz HTTP 200 (três itens normalizados por fonte), uma interpretação Groq HTTP 200/cache miss e consumo **2→3/50**. Sem persistir catálogo dos provedores nessa rodada; somente Intent/cache/uso via OnlineStore. Evidência de requests reportada pelo Backend, sem repeti-los por Banco. Leitura do código local `api/app/core/http.py` confirma `verify=ssl.create_default_context()`; validação TLS permanece habilitada, sem patch por Banco.

Leitura própria **após** a rodada corrigida, às **17:19:40 UTC**, Unix ms `1790961580951`, confirmou **3 chamadas**, um cache ONLINE/groq válido com TTL restante **86.282 s** (cerca de 24h) e uma origem de recomendação expirada. Não restavam linhas externas expiradas BOOK/groq: isso é compatível com a limpeza global de expirados já feita por `OnlineStore.put` ao gravar a nova Intent, não expurgo executado por Banco. Só contagens/TTL/providers/uso consultados, sem corpos/prompt/chaves. Orçamento do próximo gate de recomendação pertence ao Maestro; Banco não o executa nem fecha o gate PostgreSQL com esse resultado online.

Leitura final adicional autorizada, **17:24:49 UTC**, Unix ms `1790961889115`, após gate API encerrado pelo Backend às 17:23:23 UTC: **5 chamadas Groq / limite 50 documentado**, **3 caches ONLINE/groq válidos** (TTL restante 85.973–86.322 s), **4 caches ONLINE/musicbrainz válidos** (3.516–3.521 s) e **2 origens de recomendação válidas** (3.519–3.522 s). Nenhum corpo/hash/consulta/chave foi lido por Banco; contagens agregadas não provam a fonte dos itens efetivamente entregues.

Backend reportou dois POSTs MUSIC/renovação, offsets 0/15, `ai_used=true`, `degraded=false`, mas itens entregues do catálogo local; consumo 3→4→5, uma tentativa por POST e nenhum retry fora do orçamento. Reportou também reaproveitamento da mesma Intent com TTL decrescente, sem renovação. Essa identidade/semântica individual é evidência do Backend, não inferência das contagens agregadas de Banco. O novo snapshot 5/50 não substitui os históricos 2/50 e 3/50, nem aprova recomendação externa ou PostgreSQL. Banco não repetiu POSTs, GET de capa, provedores ou LLM.

**Adendo reportado pelo Backend, sem nova leitura de Banco:** gate adicional do Maestro às **17:25:48 UTC**, um POST BOOK e um MUSIC. BOOK entregou três itens Open Library com seleção Groq ativa, consumo **5→7**; MUSIC de jazz instrumental retornou vazio, `ai_used=true`/`degraded=false`, consumo **7→9**. Backend confirmou **9/50** na leitura RO do seu script, quatro novas tentativas dentro do orçamento de até oito. O snapshot próprio de Banco **17:24:49 UTC / 5/50** é anterior a esse gate e continua válido para seu instante; **9/50 é evidência do Backend**, não medição repetida por Banco. Sem novo probe/leitura/patch/schema/PG nesta atualização documental. Resultado musical vazio não deve ser descrito como recomendação externa musical entregue.

## Continuidade

- Entregar somente este novo documento ao Maestro; harness ignorado permanece local e não deve ser stage/commitado antes de execução real/revisão. Nenhum arquivo compartilhado/Git editado por Banco.
- Quando ambiente ficar disponível: coordenação de um único container, execução do harness, registrar versões/checks/falhas; somente então decidir se há bug confirmado em migration/model ou integração versionada de testes/CI. Scripts em `.impeccable` não sobrevivem necessariamente a outro checkout: se ausentes, reconstruir a proposta/cobertura antes de executar, nunca declarar gate aprovado por este relatório.
- Gate PostgreSQL/pgvector real permanece pendente. Não há bloqueio de credencial a resolver nesta etapa nem necessidade de alterar servidores atuais.
