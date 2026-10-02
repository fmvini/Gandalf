# Auditoria de banco — 2026-10-02

## Escopo e estado de partida

- Lidos `docs/DEVELOPMENT_LOG.md`, `docs/CONTINUATION.md`, Git e código atual. HEAD inicial `bfa418b`: schema `0008_favorites` já commitado; favoritos API/frontend ainda WIP. Cache compartilhado integrado em `3547739`, schema em `54e13c2`.
- Contrato confirmado pelo Backend/usuário: IDs vistos efêmeros no cliente, UUIDs deterministas das fontes reais, sem histórico persistente e sem migration nova. Backend implementa música (`excluded_music_ids`, `offset`, `meta.has_more`/`next_offset`) e audita livros; esta auditoria não declara essa entrega concluída.
- Nenhum modelo, migration, serviço, frontend ou teste versionado foi editado. Documentos compartilhados de progresso/continuidade reservados ao Maestro. Somente este relatório e `docs/04-Data-Model.md` alterados por Banco de Dados.

## IDs, cache e reroll

- `api/app/providers/musicbrainz.py:45`: UUID5 (`NAMESPACE_URL`) da URL canônica `/recording/{mbid}`. MBID é validado/canonicalizado como UUID antes da conversão. Título/artista/duração não definem identidade; duas gravações da mesma obra com MBIDs diferentes continuam itens diferentes.
- `api/app/providers/open_library.py:89`: UUID5 da URL `/works/{OL...W}`; aceita chave da obra com/sem `/works/`. Título/capa portugueses vêm da edição sem trocar a identidade da obra. Chaves de edição `/books/...M` não são aceitas como obra.
- Verificação direta dos normalizadores passou: mesmo UUID com MBID em maiúsculas e título/duração alterados; mesmo UUID com chave de obra alternativa e edição portuguesa; MBID inválido e chave de edição rejeitados. Sem rede.
- `api/app/services/book_service.py:46`: chave de descoberta distingue offset, consulta normalizada, limite e prefixo `pt-editions-v2`; provedor/tipo também participam da unicidade de `external_search_cache`. Catálogo usa `(provider, external_id)` no upsert; conserva ID já catalogado e o devolve antes de serializar cache. Em banco legado com ID divergente, prevalece a identidade já existente, portanto estabilidade no mesmo catálogo não implica recalcular IDs históricos.
- `api/app/providers/musicbrainz.py:81`: chave distingue offset, busca por tag/texto, trilha/instrumental, termo normalizado e limite. `OnlineStore` persiste catálogo por ID e cache por tipo/provedor/chave/limite; JSON já comporta `has_more` sem coluna nova.
- `recommendation_results` possui UUID próprio por resultado e snapshot JSON/JSONB, não FK ao catálogo, TTL de uma hora e limite global de 256. Reroll publica nova origem; a lista de vistos não entra nesse snapshot. Favoritos salvos continuam independentes da expiração/evicção da origem.
- Limite de privacidade existente: snapshot de origem exclui `parsed_query`/consulta/conta no topo, mas conserva itens com score/explicação para explicações. Favoritos copiam somente `row['item']`. Cache externo armazena termos/chaves; `api/app/ai/groq.py:117` usa hash como chave e persiste respostas `Intent`/`Selection` por 24h, inclusive temas/referências interpretados. Não é histórico de vistos nem coleção por conta; tampouco se deve afirmar ausência de toda intenção interpretada em todos os caches.
- Conclusão: modelos e migrations atuais suportam persistência/IDs/cache do reroll contratado; nenhuma alteração de schema necessária.

## Revisão independente de favoritos e concorrência

- `api/app/models/favorite.py` e `0008_favorites`: NOT NULL, CHECK MUSIC/BOOK, unicidade `(user_id, type, item_id)`, índices de proprietário/tipo/data/ID e única FK para conta com CASCADE. Sem FK para origem/catálogo, preservando snapshots.
- `api/app/routes/favorites.py`: conta vem da autenticação, não do corpo. Criação valida origem pelo cache; `FavoriteService.create` exige item retornado nela, rejeita payload arbitrário e copia somente o item. A origem é pública/anônima; não exige ownership da origem.
- `api/app/services/favorite_service.py:83`: conflito faz atualização sem mudança de valores (`id = favorites.id`) e `RETURNING(Favorite)` com `populate_existing`; resposta materializada antes do commit. Conserva ID, snapshot, proveniência e data, sem SELECT posterior suscetível a DELETE concorrente. UUID candidato distingue novo/repetido. Rollback de falha SQL/commit retorna 503 genérico.
- Listagem/status/DELETE filtram proprietário; status também tipo. DELETE ausente/de outra conta retorna o mesmo 204. Essas operações não precisam de cache de origem disponível. Não identificado novo bloqueador de ownership/deduplicação no código revisado.
- Revisão de semântica PostgreSQL, **não teste real**: [READ COMMITTED](https://www.postgresql.org/docs/18/transaction-iso.html#XACT-READ-COMMITTED) e [INSERT / ON CONFLICT / RETURNING](https://www.postgresql.org/docs/18/sql-insert.html). Upsert com DO UPDATE fornece resultado da própria operação; não dá garantia de existência após um DELETE que ocorra depois do commit. DO NOTHING seguido de SELECT não oferecia essa proteção entre comandos.
- Observação não bloqueante: `list_favorites` calcula COUNT e página em SELECTs distintos; sob READ COMMITTED, alterações concorrentes podem gerar `total` diferente da página. Não há contrato de snapshot consistente entre esses comandos. Se produto exigir essa garantia, Backend deve revisar transação/consulta, sem migration por padrão.
- `api/app/services/recommendation_cache.py:36`: todas as operações obtêm lock consultivo por transação em PostgreSQL (SQLite inicia escrita via DELETE) antes de purgar/limitar. Leitura também serializa; evita corrida de limite/limpeza entre workers cooperantes, com custo de contenção. Não identificado defeito funcional novo; medir esse custo em PostgreSQL antes de ampliar workers.
- TTL não renova em GET nem ao sobrescrever origem ainda existente; limpeza é por tráfego, não job. Limite/TTL dependem de writers usando o serviço. Republish de UUID já removido cria nova linha; o fluxo normal gera UUID4 novo e não retém cópia local capaz de ressuscitar origem.
- Correção documental feita em `docs/04-Data-Model.md:512`: substituído contrato obsoleto DO NOTHING pelo upsert/RETURNING real e documentado reroll efêmero/IDs/cache. Sem mudança de comportamento.

## Testes e evidências desta sessão

| Verificação | Resultado / limite |
|---|---|
| Cinco módulos: migrations, favorites, recommendation_cache, continuation, online | **122 passaram; 3 bloqueados por ambiente**, 1 aviso Starlette/httpx; 66,16 s. Pytest reporta os bloqueios como `3 failed`; não houve falha de asserção nesses três casos. Não é suíte integral aprovada. |
| Três casos multiprocessos | `test_concurrent_processes_deduplicate_atomically`, `test_concurrent_repeated_create_and_delete_return_detached_snapshots`, `test_concurrent_sqlite_processes_enforce_global_capacity`: `concurrent.futures.ProcessPoolExecutor` falha em `multiprocessing.connection.Pipe` / `_winapi.CreateFile`, `PermissionError: [WinError 5]`, antes de executar workers e as asserções de concorrência. |
| Normalizadores reais, sem rede | Verificação direta de estabilidade UUID5/canonicalização/edição e rejeição de IDs inválidos passou. |
| Ruff check de `app/models`, `alembic`, `tests/test_migrations.py` | Passou. |
| Ruff format --check no mesmo escopo | 18 arquivos já formatados. |
| `git diff --check` em docs04 | Passou; Git avisa somente conversão LF/CRLF futura. |

Execução original com `--basetemp=../.impeccable/database-audit-20261002` foi bloqueada por acesso aos diretórios criados pelo pytest (inclusive cleanup); uma reprodução isolada mostrou o mesmo WinError 5. Não usar essa tentativa como resultado de testes.

Para executar as mesmas asserções, foi criado runner **ignorado pelo Git**, `.impeccable/database-audit-runner.py`: desativa somente plugin de temporários/cache do pytest e fornece fixture `tmp_path` por teste em diretórios únicos criados com permissões herdadas. Não altera testes, multiprocessing, workers, asserções ou código de aplicação. Bancos de teste ficam em `.impeccable/database-audit-inherited-{uuid}/`; nenhum banco existente é usado.

Comando de reprodução (em `api/`):

```powershell
.\.venv\Scripts\python.exe ..\.impeccable\database-audit-runner.py tests/test_migrations.py tests/test_favorites.py tests/test_recommendation_cache.py tests/test_continuation.py tests/test_online.py
.\.venv\Scripts\python.exe -m ruff check app/models alembic tests/test_migrations.py
.\.venv\Scripts\python.exe -m ruff format --check app/models alembic tests/test_migrations.py
```

As verificações de migrations são SQLite e geração SQL PostgreSQL; testes dos adaptadores online usam HTTP simulado/fixtures, **não chamadas atuais a MusicBrainz/Open Library/Groq**. Código WIP de Backend mudou durante a sessão; os resultados não fecham o checkpoint final de reroll nem favoritos/frontend. Maestro deve validar a árvore final e reexecutar os três casos multiprocessos em seu terminal; aprovação registrada no dia anterior não vale como reexecução nesta sessão.

Backend informou separadamente que sua tentativa inicial com fábrica de temporários gerou erros de teardown `_retention_policy`, corrigidos com fixture simples. Esses erros ambientais não são regressões da aplicação e invalidam a aprovação daquela execução; suas contagens não estão somadas aos 122 testes desta auditoria. O subset de favoritos daquele terminal ainda estava em execução no momento do aviso, portanto não é apresentado aqui como resultado confirmado.

## Disponibilidade PostgreSQL/pgvector — gate pendente

| Evidência read-only | Resultado |
|---|---|
| `Get-Command docker,psql,pg_isready` | Clientes presentes; PostgreSQL em `C:\Program Files\PostgreSQL\18\bin`, Docker CLI do Docker Desktop. |
| `docker version`, `docker ps`, `docker images` | Daemon Linux inacessível: `npipe:////./pipe/dockerDesktopLinuxEngine`, arquivo não encontrado. Não foi possível confirmar imagens/containers disponíveis. |
| `pg_isready -h 127.0.0.1 -p 5432 -t 2` | Aceita conexões; serviço `postgresql-x64-18` em execução, preexistente. |
| Mesmo comando em 5433 | Sem resposta (porta prevista em `api/compose.yaml`). |
| `psql -X -w -h 127.0.0.1 -p 5432 -U postgres -d postgres -c ...` | `fe_sendauth: no password supplied`; SELECT de versão/extensões não executou. Nenhuma tentativa de adivinhar senha. |
| Inventário `share\extension\*vector*` e `lib\*vector*` na instalação 18 | Nenhum arquivo encontrado; `citext.control` está presente. Evidência de ausência nesses diretórios, não consulta SQL autenticada nem inventário de todas as instalações. |

Não havia instância PostgreSQL/pgvector descartável acessível com os recursos verificados. Nenhum servidor/serviço foi iniciado, parado, reconfigurado ou instalado; nenhum banco existente foi migrado ou recebeu escrita. Não criados/removidos bancos/containers; nenhum segredo lido/exposto; nenhum consumo de cota online nesta auditoria.

**Gate PostgreSQL/pgvector real permanece aberto.** SQLite, compilação SQL e revisão da documentação PostgreSQL não o aprovam.

## Continuidade e commit

1. Maestro revisar somente `docs/database-session-2026-10-02.md` e `docs/04-Data-Model.md` para o commit documental serializado; reservar favoritos/backend/frontend para seus checkpoints. Sugestão: `docs: registra auditoria de persistência e gate PostgreSQL`, com corpo explicando contrato reroll/upsert, testes e limites. Banco de Dados não faz stage/commit concorrente nem push. Backend informou bloqueio de escrita em `.git/index.lock` até o Maestro; nenhum stage/commit foi tentado por este terminal.
2. Reexecutar os três testes multiprocessos no terminal Maestro, preservando as asserções; registrar separadamente resultado e árvore final. Não converter falha de named pipe em aprovação.
3. Quando um daemon/imagem pgvector já instalado estiver acessível ou houver instância **isolada** com credenciais, conferir isolamento e usar banco/container de nome único, sem volume/banco do projeto. Se partir de Docker, usar imagem local pgvector confirmada, sem pull/instalação externa; não usar o compose com volume `gandalf_pgdata`.
4. No ambiente descartável: consultar versão e `pg_available_extensions`, aplicar upgrade base→0008, readiness com vector, paridade metadata, tipos JSONB/timestamptz/FKs/CHECK/unicidade, round-trip 0008→0007→0008 com tabelas anteriores preservadas. Validar UUIDs reais e persistência de snapshots após origem/catálogo removidos, ownership entre duas contas e cascata.
5. Com sessões/processos independentes e READ COMMITTED: criar/repetir/deletar mesmo favorito, conferir snapshot retornado/primeiro ID/data/origem e rollback; publicar/ler/prunar cache concorrente com TTL/empate/limite global 256; refresh concorrente é gate relacionado da autenticação. Registrar versões, comando, resultados e limpeza apenas dos recursos descartáveis criados para o teste.
