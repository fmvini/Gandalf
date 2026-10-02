# API do Gandalf

CI inicial configurada em [`.github/workflows/ci.yml`](../.github/workflows/ci.yml): Ruff/formatação, suíte pytest com SQLite e comparação estrita K=5/10 contra o baseline v7. Relatórios JUnit/JSON são preservados como artefatos. [Escopo, resultados locais e limites](../docs/CI.md); a execução no GitHub ainda precisa ser confirmada após um push autorizado.

> **Atualização de 2026-10-01:** as instruções abaixo se referem principalmente ao caminho local. A [matriz de implementação](../docs/IMPLEMENTATION_STATUS.md) descreve também o modo online experimental e suas limitações. O ranking local atual é `local-rules-v7`; a [especificação da descoberta](../docs/05-API-Specification.md#61-post-recommendationsmusic) distingue contrato implementado de exemplos futuros.

Piano e detetive agora são reconhecidos pelo parser e pelo fallback online sem IA. Há sete músicas com `piano` e um livro com `detetive`, com [fontes por obra e limites](../docs/catalog-metadata.md). Piano descreve uma obra/edição com piano, sem garantir piano solo ou a gravação aberta por um link de busca. Ausência de etiqueta não prova ausência do instrumento/tema. Inclusão continua por afinidade de temas; exclusões removem itens com as etiquetas conhecidas.

No ranking local, a relevância total precede os desempates: gêneros explicitamente pedidos nos livros (incluindo detetive), atmosfera em CALM e diversidade de artistas/etiqueta cinematográfica em CINEMATIC. Depois se usa o título. Referências não recebem prioridade de gênero explícito e são removidas dos resultados; filtros e exclusões prevalecem.

[Avaliação v7 contra v6](../docs/eval-reports/2026-10-01-piano-detective.md): 45 consultas intactas, K=5/10, nenhuma perda agregada ou por consulta. Para proteger a etapa atual, execute `python -m app.evaluation.runner --baseline ../docs/eval-reports/local-v7-piano-detective-k5.json --fail-on-case-regression` e repita com `--k 10` e o relatório K=10. Revisão humana, conjunto reservado e avaliação online real continuam pendentes.

Também estão implementados `GET /api/v1/music/search`, `GET /api/v1/music/{id}` e `GET /api/v1/system/status`. O modo online usa MusicBrainz para busca musical, Open Library para livros e Groq opcional para interpretação/seleção. No iniciador use `GANDALF_ONLINE=1`; ao executar `uvicorn app.main:app` diretamente use `ONLINE_CATALOG=true`, banco migrado e configuração de ambiente. `python local.py` permanece offline por padrão.

Avaliação local reproduzível, sem rede: `python -m app.evaluation.runner --baseline ../docs/eval-reports/local-v3-baseline-k5.json`. Adicione `--k 10` e use `local-v3-baseline-k10.json` para comparar top-10. Veja [metodologia e resultados](../docs/eval-reports/2026-09-29-local-baseline.md).

Com `--baseline`, a CLI mostra também `comparison`: listas antes/depois, deltas de métricas e perdas por consulta, além das regressões agregadas. `--output caminho.json` salva o relatório completo, sem permitir sobrescrever dataset ou baseline. O padrão falha apenas por regressões agregadas; `--fail-on-case-regression` exige baseline e também retorna código 1 diante de qualquer perda individual. Código 2 indica argumentos ou entradas incompatíveis. [Detalhes e exemplo v4/v5](../docs/eval-reports/2026-09-30-case-comparison.md).

FastAPI com busca de livros, recomenda??es locais e autentica??o persistente.

## Modo local gratuito

```powershell
cd api
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\python.exe local.py
```

`local.py` gera um segredo em `.local/jwt-secret`, aplica migra??es em `.local/gandalf.db` e inicia em `127.0.0.1:8000`. Banco, segredo e provider s?o isolados do `.env` e de `DATABASE_URL`. N?o h? chamada externa nesse modo. `GANDALF_PORT` permite outra porta e `GANDALF_LOCAL_DATA` outro diret?rio de dados. Na raiz, `start-local.ps1` inicia API e interface juntas.

Swagger: http://127.0.0.1:8000/docs. Frontend: `VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1`. CORS local permite `localhost:5173` e `127.0.0.1:5173`.

## Endpoints implementados

| M?todo | Rota | Comportamento |
|---|---|---|
| GET | `/health` | Processo ativo |
| GET | `/health/ready` | Banco e todas as tabelas; pgvector exigido apenas no PostgreSQL |
| GET | `/version` | Versão da aplicação e `local-rules-v7` |
| GET | `/api/v1/books/search?q=Duna&limit=6` | T?tulo/autor local, ou Open Library se configurada |
| GET | `/api/v1/books/{id}` | Livro local ou catalogado pelo provider externo |
| POST | `/api/v1/recommendations/music` | Ranking musical local |
| POST | `/api/v1/recommendations/books` | Ranking de livros local |
| POST | `/api/v1/recommendations/read-with-music` | Sele??o musical por livro e modo |
| GET | `/api/v1/recommendations/{id}/items/{item_id}/explanation` | Crit?rios usados, por at? uma hora |
| POST | `/api/v1/auth/register` | Cadastro com Argon2id |
| POST | `/api/v1/auth/login` | JWT e refresh opaco |
| POST | `/api/v1/auth/refresh` | Rota??o; reuso revoga a fam?lia |
| POST | `/api/v1/auth/logout` | Revoga refresh da conta autenticada |
| GET | `/api/v1/auth/me` | Usu?rio do Bearer token |
| POST | `/api/v1/playlists` | Salva músicas do catálogo ou uma trilha de leitura na conta |
| GET | `/api/v1/playlists?limit=20&offset=0` | Resumos paginados somente da conta autenticada |
| GET | `/api/v1/playlists/{id}` | Playlist privada com faixas em ordem |
| DELETE | `/api/v1/playlists/{id}` | Exclui playlist e faixas; preserva catálogo compartilhado |
| POST | `/api/v1/users/me/favorites` | Salva snapshot de um item de recomendação válida; 201 novo/200 existente |
| GET | `/api/v1/users/me/favorites?type=MUSIC&limit=20&offset=0` | Favoritos privados paginados; filtro MUSIC/BOOK opcional |
| POST | `/api/v1/users/me/favorites/status` | Mapa item→favorito da conta/tipo, em lote de até 60 IDs |
| DELETE | `/api/v1/users/me/favorites/{id}` | Remove somente da conta; 204 inclusive se ausente |

Favoritos exigem a migração `0008_favorites` e autenticação. Criação aceita apenas `{recommendation_id, item_id}`; o servidor copia o item da origem, sem metadados arbitrários, consulta ou feedback. Deduplicação por conta/tipo/item conserva o primeiro snapshot. A origem precisa estar válida até para repetir o POST; salvo permanece acessível após expiração/reinício. Listagem/status/exclusão não dependem do cache de origem. [Contrato completo](../docs/05-API-Specification.md#83-favoritos-individuais--contrato-implementado) e [ADR-0016](../docs/adr/0016-owner-scoped-favorites.md).

## Recomenda??es

Descoberta recebe `query` (3?1.000 caracteres), `limit` (1?25, padr?o 10) e `filters` opcionais (`vocals`: `none`, `required`, `optional`; `energy`: `low`, `medium`, `high`, para m?sica).

```json
{"query":"M?sicas calmas para estudar","filters":{"vocals":"none","energy":"low"},"limit":10}
```

Leitura recebe `book_id`, `mode` (`FOCUS`, `IMMERSIVE`, `CINEMATIC`, `CALM`, `CUSTOM`), `context` (at? 500 caracteres, obrigat?rio em `CUSTOM`), `vocals` (`INSTRUMENTAL`, `MINIMAL`, `ANY`) e `target_duration_min` (15?120).

O ranking faz correspondência de temas editoriais, exclusões simples, filtros explícitos, remove títulos usados como referência e limita dois itens por artista/autor. Os critérios de desempate por gênero e modo estão descritos no início deste documento; o título é o último critério. `scores.context` é a fração de temas correspondentes, não similaridade de embeddings. Pedidos não reconhecidos retornam vazio com orientação.

`meta.mode=local` e `meta.hint` identificam os limites. S?o 18 livros e 25 m?sicas; links musicais abrem buscas, sem ?udio hospedado. A trilha estima cinco minutos por faixa (`playlist.duration_estimated=true`), sem atribuir dura??o real ?s grava??es. Pode haver menos itens que a dura??o ou limite pedidos.

Com banco configurado e migrado até `0007_recommendation_results`, resultados anônimos ficam no cache compartilhado por até uma hora, no máximo 256 resultados no banco inteiro. Explicações e origem para salvar trilhas sobrevivem a reinícios/trocas de instância durante essa validade. Snapshots conservam só identidade, itens e resumo da playlist; consulta/intenção/conta não são persistidas. Acessos não renovam TTL; remoção por capacidade pode ocorrer antes. Expirados são excluídos durante acessos/gravações; não há limpeza periódica sem tráfego. Sem banco, preserva cache em memória por processo e perda no reinício. Banco configurado indisponível/desatualizado retorna 503 para gerar/recuperar resultados. [Decisão e limites](../docs/adr/0015-shared-recommendation-cache.md). Histórico pessoal e feedback não estão implementados.

## Playlists persistentes

Playlists persistentes foram introduzidas na migração `0006_playlists`; o backend atual exige também `0007_recommendation_results` para o cache de origem. O iniciador local aplica as migrações automaticamente no próximo início. A interface já permite salvar trilha, listar, consultar e excluir playlists. Todas as quatro rotas exigem Bearer válido/conta ativa e filtram pelo proprietário; playlist de outra conta retorna o mesmo 404 de um ID ausente.

Criação manual: `{"name":"Minha trilha","music_ids":["UUID do catálogo musical"]}`. Para salvar uma trilha, enviar `{"name":"Minha leitura","source_recommendation_id":"UUID retornado por read-with-music"}`. Um subconjunto opcional `music_ids` deve pertencer à origem e conserva a ordem enviada. Nome 1–120 caracteres, descrição opcional até 1.000; criação manual aceita 1–25 faixas únicas, trilha de leitura aceita até 60. Metadados não são aceitos do cliente.

Descoberta: envie `excluded_music_ids` para música ou `excluded_book_ids` para livros (até 200 UUIDs já vistos), preservando `query`, `filters` e `limit` do pedido enviado. `offset` aceita 0–300 (padrão 0). IDs cumulativos são excluídos antes da IA e do fallback; não truncar a lista de vistos para continuar. Não há histórico persistente nem nova migração.

`meta.has_more` indica próxima página externa dentro do limite ou um resultado extra aceito após filtros/diversidade na amostra atual. `meta.next_offset` avança 15 quando a fonte permite; `null` mantém o último offset. Offline usa apenas exclusões e retorna `next_offset=null`. Aos 200 IDs excluídos, ambos encerram continuação. `has_more=false` encerra a amostra disponível; não significa ter esgotado todo o catálogo mundial. Um batch pode retornar menos itens ou nenhum após os filtros. Erros/avisos sozinhos não indicam novos candidatos.

Cada pedido online consulta uma página de 15 por termo (até dois termos) e uma amostra deduplicada de até 25 candidatos, com duas gravações por artista/autor. A IA pode classificar um item extra na mesma chamada para verificar continuação (até 25), sem ampliar a cota existente. Falha IA/provedor preserva o fallback por metadados/catálogo editorial real, identificado por `meta.degraded`, `meta.sources` e `meta.hint`; não inventa títulos, IDs ou durações. O cache Groq de Intent/Selection dura 24 horas e difere do cache de origem e dos IDs vistos efêmeros. [ADR-0017](../docs/adr/0017-ephemeral-discovery-reroll.md).

Trilhas online usam somente gravações MusicBrainz com duração conhecida de 90 segundos a 10 minutos, lançamentos oficiais e sem audiolivros/compilações DJ. Recuperam até oito páginas de 50 candidatos por termo (até três termos), com máximo de 60 faixas e quatro por artista. A IA ordena uma amostra; suas poucas escolhas ou indisponibilidade não limitam a duração. Não usam catálogo local nem estimativa de cinco minutos para completar uma trilha online. Sucesso exige a meta atendida (`target_met=true`, `duration_estimated=false`); insuficiência retorna `503 SOUNDTRACK_INCOMPLETE` com o total encontrado. A última faixa permanece inteira. Groq mantém o limite/retry já configurados.

Busca de livros consulta títulos de edições e prioriza português (`q`, `lang=pt`); descoberta filtra `language=por`. Quando a fonte informa edição portuguesa, o título/capa dessa edição são exibidos sem mudar o ID da obra. Há um alias de tradução verificado para a lacuna de indexação de “Quem é você, Alasca?”/“Looking for Alaska”, validado pelo autor John Green e pela editora; os registros continuam vindo do Open Library. Outros títulos sem edição portuguesa informada conservam o título da fonte, sem tradução inventada. Cache externo usa versão de idioma para não reutilizar listas antigas em inglês.

Faixas e ordem permanecem disponíveis após reinício/expiração da recomendação ou atualização do catálogo. Duração desconhecida usa estimativa no total, sinalizada por `duration_estimated`; os metadados não ganham uma duração real inventada. Origem deve ser uma trilha de leitura ainda válida no cache compartilhado do banco; descoberta musical pode ser salva por IDs pelo caminho manual. Não existe edição/exportação/reprodução nesta etapa. [Contrato completo](../docs/05-API-Specification.md#7-playlists-playlists) e [decisão de persistência/privacidade](../docs/adr/0014-owner-scoped-playlists.md).

## Provider externo opcional e PostgreSQL

O caminho anterior continua dispon?vel:

```powershell
Copy-Item .env.example .env
# Ajuste DATABASE_URL, POSTGRES_PASSWORD, JWT_SECRET e BOOK_PROVIDER=open_library
# O Docker Engine precisa estar dispon?vel
docker compose up -d db
.\.venv\Scripts\python.exe -m alembic upgrade head
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Compose usa PostgreSQL/pgvector na porta 5433. `BOOK_PROVIDER=local` ? o padr?o; `open_library` habilita busca externa de livros e requer internet. Recomenda??es continuam locais. Configure `OPEN_LIBRARY_CONTACT_EMAIL` para identificar chamadas. Essa integra??o n?o ? necess?ria para usar o sistema.

A busca externa tem intervalo m?nimo de um segundo, timeout de cinco segundos e cache em mem?ria; com banco, persiste cat?logo/cache (`BOOK_SEARCH_CACHE_TTL_SECONDS`, padr?o 300, zero desabilita). IDs s?o UUIDs determin?sticos, descri??es limitadas a 2.000 caracteres e assuntos a 12 entradas de 120 caracteres. Falhas externas retornam erros padronizados. `provider`, se informado na busca, precisa corresponder ao provider ativo.

Fora do iniciador local, auth exige banco migrado e `JWT_SECRET` de pelo menos 32 bytes; sem segredo responde 503. Registro exige e-mail v?lido, username de 3?32 caracteres e senha de 10?128. Access token dura 15 minutos e refresh sete dias. Mantenha tokens apenas em mem?ria no cliente. Rate limiting de auth ? por processo e n?o serve para m?ltiplas inst?ncias p?blicas.

## Verifica??o

```powershell
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app local.py alembic tests
.\.venv\Scripts\python.exe -m ruff format --check app local.py alembic tests
```

Testes cobrem migra??es SQLite, auth, cat?logo/cache externo com fakes, recomenda??es sem rede e rein?cio local com persist?ncia. `frontend/tests/live.mjs` sobe a API com banco tempor?rio. PostgreSQL/pgvector e concorr?ncia de refresh entre processos precisam de valida??o real antes de deploy.
