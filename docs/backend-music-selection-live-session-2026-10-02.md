# Backend — gate real da seleção MUSIC — 2026-10-02

## Estado final e limites

Gate limitado autorizado pelo Maestro executado sobre **`97b07b647ad8441ab3c3c88a036550141c9cf588`**. Exatamente duas POST MUSIC, sem reroll, queries extras, retries manuais ou alteração de filtros para forçar resultado. Consumo confirmado **9 → 12/50**, três tentativas contabilizadas de um orçamento máximo de seis. Nenhuma nova chamada externa/LLM após essas duas POST.

O controle **Jazz** entregou três itens MusicBrainz reais pelo pipeline de seleção, com IA ativa e sem degradação. É aprovação pontual de entrega musical externa, não de qualidade geral do ranking. **Jazz instrumental** permaneceu vazio: o gate instrumental estrito continua pendente; vocais desconhecidos não foram convertidos em instrumental. O gate anterior de BOOK/capa e os testes com fakes são evidências separadas.

## Runtime autorizado

- Identidade anterior revalidada imediatamente antes de parar: único listener `127.0.0.1:8000`, worker PID **31444**, parent/launcher **39748**, ambos `local.py`, launcher `api/.venv/Scripts/python.exe`.
- Não havia sessão/console interativo controlável para shutdown por interrupção. `Stop-Process -Id 31444` encerrou somente o worker identificado; nenhum comando de parada foi dirigido ao launcher, frontend ou PostgreSQL. Porta livre confirmada antes do lançamento.
- Uma única API oculta iniciada com `api/.venv/Scripts/python.exe local.py`, cwd `api`, ambiente próprio copiado, `GANDALF_ONLINE=1`, host `127.0.0.1`, porta `8000` e diretório existente **`api/.local`**. Nenhuma alteração de ambiente global, chave/modelo/provider/cota/TLS.
- Fora do sandbox, a cópia do ambiente não possuía HTTP/HTTPS/ALL proxy; nenhum valor foi removido. O script permitiria retirar somente proxy sem credenciais para `127.0.0.1:9`; nenhum proxy real foi removido.
- Novo worker **42664**, launcher **40364**, único listener `127.0.0.1:8000`, `local.py` e parent confirmado. Instância permanece ativa.
- Status/readiness locais antes, após iniciar e após o gate: **HTTP200**. Catálogo `online`, Groq configurado, modelo original `openai/gpt-oss-20b`; database/schema `ok`, pgvector `not_required` nessa instância SQLite.
- Frontend **25716** e PG existente **10140** ainda presentes ao final, sem restart/stop pelo Backend. Nenhuma interferência com Docker/gate PostgreSQL do Banco. HEAD confirmado inalterado ao final.

## Pedidos e respostas reais

Início do gate: **2026-10-02 18:05:51 UTC**. Endpoint de ambas as POST: `/api/v1/recommendations/music`. Corpos exatos: `{"query":"Jazz instrumental","limit":3}` e `{"query":"Jazz","limit":3}`; sem filtro vocal artificial no controle e sem reaproveitar/alterar o filtro do primeiro pedido.

| Pedido | HTTP | Itens/fontes efetivas | ai_used/degraded | has_more/next_offset | Uso |
| --- | --- | --- | --- | --- | --- |
| Jazz instrumental | 200 | 0 / `[]` | `true` / `false` | `true` / `15` | 9 → 10 |
| Jazz | 200 | 3 / `["musicbrainz"]` | `true` / `false` | `true` / `15` | 10 → 12 |

Primeira resposta declarou nenhum item compatível; segunda declarou metadados MusicBrainz e energia/vocais estimados pela IA quando informados. Ambos os pedidos completaram dentro do orçamento; nenhuma condição de cancelamento foi atingida.

Metadados públicos entregues no controle:

| Título / artista | UUID público | MBID / duração |
| --- | --- | --- |
| Single‐O / Ella Fitzgerald | `608fc08a-2831-5fb5-ad6d-db3a4731cb23` | `0fa79135-1d44-4d5e-92ac-e059af8c11f0` / 199293 ms |
| April Showers / Al Jolson | `bf649379-d9b3-5041-afc0-705c659af192` | `2b2cf0dd-32b4-4e44-b372-2264a9fff3e0` / 187000 ms |
| J’ai longtemps contemplé / Alain Bashung | `521e2651-2f02-5806-9cbf-f05de7335cbe` | `43139caf-d35f-4f10-825a-b20cb793936c` / 237866 ms |

Os três UUIDs são distintos. Todos os itens informaram `provider=musicbrainz`, **`has_vocals=null`**, **`energy=null`** e `classification_source=ai_estimate`. O rótulo de origem é o comportamento de saída preexistente, mantido fora do escopo desta unidade; não significa que uma classificação não nula foi obtida, que a faixa é instrumental ou que houve medição acústica. Não houve reprodução/avaliação auditiva nem verificação independente de gênero de cada gravação nesta janela.

## Cache, contrato e evidências

- Consulta SQLite de cota em `mode=ro`/`query_only`: baseline **9**, após primeiro pedido **10**, após segundo **12**. Nenhum reset, aumento de limite ou ajuste de contagem.
- Apenas `expires_at`/existência do Intent da consulta pública exata foi consultado; nenhum corpo privado/cache alheio lido. Intent permaneceu live e com o mesmo **`expires_at=1791048353191`** antes/depois, cerca de 84001 segundos restantes no início. Nenhuma renovação manual ou expurgo.
- Seleção MUSIC usa o novo payload/instrução commitados; BOOK/Intent/schema/filtros/duração/retries/TTL não foram editados na janela. Não houve novo gate BOOK: preservação literal de instrução/payload foi testada na unidade anterior.
- Os **134 testes do subset**, **14 novos revalidados**, Ruff e revisão antes do commit constam em `docs/backend-music-selection-session-2026-10-02.md`. Não repetidos como suíte geral nesta janela real.
- Artefatos/scripts/logs ignorados em `.impeccable/runtime`: `backend-music-selection-restart-20261002.py`, `backend-music-selection-runtime-20261002.json`, `backend-music-selection-real-gate-20261002.py`, `backend-music-selection-real-gate-20261002.json`, `backend-music-selection-local-after-20261002.json`, `backend-music-selection-api.stdout.log` e `.stderr.log`.

Comando do gate, fora do sandbox, cwd raiz do projeto:

```powershell
& api/.venv/Scripts/python.exe .impeccable/runtime/backend-music-selection-real-gate-20261002.py --maestro-authorized --expected-head 97b07b647ad8441ab3c3c88a036550141c9cf588 --api-pid 42664
```

O script salvou o JSON completo e só depois falhou ao imprimir um título Unicode em stdout cp1252 (`UnicodeEncodeError`, exit code 1). Isso não foi falha HTTP/API: o arquivo registra ambas as respostas200 e `two_predefined_posts_completed`. Foi feita somente leitura do JSON salvo com impressão ASCII escapada; **nenhuma POST foi repetida**.

## Freeze e continuidade

Gate encerrado. Código/testes/relatório anterior commitados intactos; somente este novo relatório versionável é entregue ao Maestro para commit documental seletivo. Sem stage/commit/push pelo Backend. Nova API **42664/8000** deve permanecer ativa.

Próxima investigação, se autorizada, deve distinguir relevância da seleção e falta de classificação vocal para o caso instrumental; não converter desconhecido em instrumental nem ampliar cotas/queries para perseguir aprovação. Qualquer replay novo deve permanecer restrito aos dados públicos derivados destes pedidos. Nenhuma investigação adicional/probe/restart foi iniciada nesta entrega.
