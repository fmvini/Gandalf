# Fase 2 MusicProvider — revisão frontend, 2026-10-02

## Entrega final Maestro — 2026-10-03

Unidade concluída: `frontend/src/lib/api.ts`, `frontend/src/lib/format.ts`, `frontend/tests/music-metadata.mjs` e este relatório. Maestro assumiu a reserva congelada após o terminal Frontend atingir o limite de uso da sessão. Nenhuma alteração CSS, dependência ou nova integração.

- **Antes:** execução escalada na porta62690 demonstrou `Accurate search/source label for Alternativa por tags`: actual Buscar no YouTube, expected Buscar faixa. Dez linhas renderizadas, uma resposta mockada, zero erros/runtime/requestfailed/origens externas. Evidência ignorada preservada em `.impeccable/review/music-metadata-before-fix.json`.
- **Correção:** `links.search` mantém href; hostname youtube.com ou seu subdomínio usa Buscar no YouTube, outros destinos usam Buscar faixa. Hostname que apenas contém o texto YouTube não recebe atribuição falsa. Prioridade spotify/youtube/provider/search/fallback preservada. `duration_ms` e helper duration aceitam null explicitamente, sem alterar formatação.
- **Depois:** `node tests/music-metadata.mjs` escalado PASS, porta59552:14 fixtures em dois lotes10+4, requests2 exatas, ordem/metadata/vocais/energia/proveniência/duração/links/nome acessível/target/rel preservados. Zero erros, requests falhas ou origens externas. O endpoint API foi interceptado integralmente; nenhum acesso API8000/Groq/fonte real.
- **QA:**16 capturas atuais em `.impeccable/review/music-metadata-batch-*.png`; oito variantes por lote, 1440/390/320px, temas claro/escuro e movimento reduzido/normal. Fonte>=14px, contraste>=4,5:1 e overflow por parágrafo/página aprovados. Maestro inspecionou batch1/320/light e dark/reduce: conteúdo e rótulos legíveis, duração desconhecida vazia, sem sobreposição. `music-metadata-evidence.json` contém métricas e fixtures, não credenciais.
- **Build final único:** `npm.cmd run build` escalado PASS; `tsc -b`,2050 módulos, JS504,22kB/gzip158,18kB. Aviso chunk>500kB não fatal permanece. Sintaxe/diff-check PASS. Não houve nova suíte auth/geral/Node independente.

Falhas intermediárias do harness não contam como provas do produto: lote14 violava o limite10 do consumidor; timeout load na porta60667 não reproduziu rótulo; seletor h3 abrangente também coletava títulos de Explanation. Corrigido seletor para `.result-heading > h3`, mantendo a asserção exata de ordem e todos os14 casos. Probe ignorado, com API/rede externa bloqueadas, confirmou readiness/load local em aproximadamente1,3s; causa do timeout transitório não foi determinada. Não aumentamos timeouts nem alteramos produto para acomodar o harness.

Limites: fixtures aprovam consumo do contrato e apresentação, não cobertura/licença/áudio de outro provider, disponibilidade online ou G1. API atual deve ser recarregada pelo Maestro após serialização; nenhuma chamada externa é necessária para conferir health/configuração.

## Checkpoint histórico — fixtures e rótulo search (então em andamento)

Maestro autorizou ampliar somente `frontend/tests/music-metadata.mjs`, este documento e, após prova, o label de `musicDestination` em `frontend/src/lib/api.ts`. Reserva comunicada antes da edição. Sem CSS/redesign/dependências, mudanças de precedência/URL/fallback ou gates Node/auth/gerais.

- Harness agora tem14 fixtures: dez anteriores preservadas e quatro de provider alternativo conhecido/provider_tags/ai_estimate/unknown; provider+search simultâneos verificam precedência, search YouTube conserva rótulo, search genérico e hostname que só contém YouTube devem usar Buscar faixa. href/accessibility/target/rel verificados sem visitar os links. Fixture unknown inclui duration_ms:null; demais durações conhecidas permanecem180000/3:00. Assertions exigem duração null vazia, sem preencher valor inventado.
- Todos os dados API são mocks; listener HTTP middleware port0 real, assert diferente5173. Rota abrangente bloqueia outras origens; nenhuma chamada externa/LLM/API8000 autorizada.
- Sintaxe `node --check tests/music-metadata.mjs` PASS. Execução normal `node tests/music-metadata.mjs` bloqueou **spawn EPERM** no esbuild antes de browser/testes. Isso **não é reprodução funcional** do defeito nem aprovação de fixtures.
- Primeira execução escalada Maestro, porta51122, falhou em nth(13)/10000ms **antes da asserção do rótulo**. Não é prova de label. Causa encontrada: `Discovery.tsx:105` chama `freshSuggestions`, cujo defaultlimit10 em `lib/discovery.ts:21–26` corta a resposta14; erro era o modelo do harness, não limitação indevida do produto.
- Corrigido **somente harness** para duas buscas independentes, queries distintas, lotes10+4. Primeiro lote inclui todos os casos alternativos, inclusive search genérico; ranking reindexado por lote. Asserções mantêm contagem exata por lote, total14 fixtures/ordem/rótulos, body `{query,filters:{},limit:10}`, requests2 exatas e queries/snapshots distintos. Nenhuma asserção removida e timeout permanece10000ms. Matriz anterior de oito variantes se aplica a cada lote (16 capturas quando aprovar), com fonte/contraste/overflow completos.
- Em falha, observabilidade registra somente fixtures: query/filtros/limit, quantidade entregue, número de linhas, estado do painel, erros de runtime e path/type/error de requestfailed; nunca headers/Authorization/cookies/storage/credenciais. Saída e `.impeccable/review/music-metadata-failure.json` ignorado. Guard de outras origens permanece.
- Harness corrigido congelado para Maestro reexecutar prépatch: `cd frontend; node tests/music-metadata.mjs` escalado. Esperado: **Accurate search/source label for Alternativa por tags**, Buscar no YouTube versus Buscar faixa, sem timeout de14 numa única seleção. **api.ts ainda sem patch**. Liberação adicional de tipos duration_ms:number|null / duration(ms?:number|null) registrada; assinaturas serão alinhadas junto à unidade final, após a prova préfix, sem alterar comportamento de formatação.
- Não houve tsc/build/capturas novas nesta unidade até este checkpoint. Gate final tsc/build será único após freeze/correção, coordenado com Maestro; não alegar resultados antes de executar.

## Resultado da inspeção inicial (histórico)

**Nenhum defeito atual de atribuição hardcoded MusicBrainz a item de provider diverso encontrado por inspeção estática.** A descoberta decide a origem pelo campo literal de cada item; Reading, favoritos e playlist salva usam destinos genéricos. Nenhum patch UI necessário demonstrado nesta rodada. Há uma convenção de links a preservar/decidir antes de admitir adaptadores alternativos: `links.search` é rotulado como busca no YouTube, não busca genérica.

Revisão somente leitura de fontes/fixtures, com escrita exclusiva deste relatório autorizada. Sem execução de testes, capturas, build, API8000, rede/provedores/Groq, alterações de frontend/Backend, stage/commit/push ou documentos compartilhados. Resultados históricos de gates não foram reexecutados nem tratados como prova nova.

Consultados `docs/DEVELOPMENT_LOG.md`, ADR-0004 e ADR-0012. O primeiro exige itens normalizados/proveniência/URLs validadas no adaptador, sem acoplar interface à fonte; o segundo mantém MusicBrainz experimental e seleção comparativa/G1 pendentes. Este relatório avalia dependências da UI, não escolhe fonte ou certifica licença/cobertura.

## Evidências com arquivo/linha

| Local | Comportamento observado | Conclusão |
| --- | --- | --- |
| `frontend/src/lib/format.ts:3–14` | MusicBrainz somente para `provider === 'musicbrainz'`; local somente para `provider === 'local'`; outro valor vira `Fonte: <valor>`; null/ausência não ganha origem | Não infere MusicBrainz/local por ai_used, tags ou URL |
| `frontend/src/lib/format.ts:7–13` | ai_estimate → Estimativa por IA; provider_tags → Tags da fonte; classificação diferente/ausente sem rótulo inventado. Vocais false/true → instrumental/com voz; null/ausência → não informados. Energia low/medium/high conhecida; demais valores → não informada | Null/unknown não viram instrumental/energia conhecida; nenhuma alegação de medição |
| `frontend/src/pages/Discovery.tsx:53–56` | MusicResult usa helper de metadados e musicDestination; título/artista/álbum/tags/duração vêm do item | Não usa MBID/raw provider ou metadados agregados para preencher classificação |
| `frontend/src/pages/Discovery.tsx:200,203` | meta.hint e parsed_query são textos da resposta; itens vazios também usam hint | Hint servidor que diga MusicBrainz será exibido literalmente; correção de atribuição indevida no serviço é ponto Backend, não inferência adicional da UI |
| `frontend/src/lib/api.ts:61–70` | Prioridade spotify, youtube, provider, search; sem links constrói busca YouTube a partir de título/artista | `links.provider` tem rótulo Ver fonte, independente do provider do catálogo. Fonte de metadados e destino de reprodução não são equiparados |
| `frontend/src/pages/ReadWithMusic.tsx:106–111` | Hint servidor, duração agregada/estimada, título/artista/duração da faixa, links pelo helper | Nenhum MusicBrainz hardcoded; não exibe provider/classificação/vocais/energia por faixa. Isso é diferença de cobertura da UI existente, não falsificação de origem; não ampliar incidentalmente |
| `frontend/src/pages/Playlist.tsx:60–61` | Item usa musicDestination; duração ausente vira travessão; total estimado explicitado | Não exige MusicBrainz ou duração individual completa |
| `frontend/src/pages/Favorites.tsx:68–75` | Título/artista/arte e musicDestination | Não exige campo provider para link/renderização; também não exibe classificação por faixa |
| `frontend/src/lib/api.ts:1–6` | id/title/artist obrigatórios; restante opcional. provider/classificação/vocais/energia aceitam null | Contrato UI não exige campos exclusivos de MusicBrainz |
| `frontend/src/lib/format.ts:17–22` | Duração falsy retorna vazio; número positivo é formatado em minutos/segundos | duration_ms null é tolerado em runtime, mas tipo TS atual declara só número opcional. Lacuna de tipagem a coordenar se normalizador passar null explicitamente, sem crash demonstrado |

## Convenção de busca — limite demonstrável por código

Em `frontend/src/lib/api.ts:65`, qualquer `links.search` ganha **Buscar no YouTube**, sem checagem da plataforma. Contramodelo estático, não executado: `{provider: 'outro', links: {search: 'https://example.com/search?q=faixa'}}` levaria a example.com com rótulo YouTube. O provider atual produz realmente URL YouTube nesse campo (`api/app/providers/musicbrainz.py:54–60`), portanto **não foi demonstrada resposta atual válida com rótulo errado**.

Para manter compatibilidade sem patch UI: normalizar `links.search` como busca YouTube; usar `links.provider` para página/link genérico da fonte alternativa. Caso a decisão de contrato torne search genérico, Maestro pode autorizar ajuste estreito de rótulo + fixture em unidade própria. Não modificar agora por hipótese de um adaptador ainda não entregue.

## Contrato mínimo efetivamente consumido

- **Identidade:** `item.id` string estável/única no catálogo normalizado, `title` e `artist` strings reais. UI não parseia MBID nem usa external_id; IDs vão a favoritos, explicação e exclusões cumulativas. Respeitar UUID normalizado da API e evitar colisões entre fontes é responsabilidade do adaptador/Backend, não enviar IDs brutos reutilizados por providers distintos.
- **Apresentação opcional:** album, image_url, tags, duration_ms. Arte ausente/erro tem fallback; tags só são exibidas, sem inferir vocais/energia. Duração deve ser número finito positivo em ms quando conhecida; ausência não é preenchida com duração inventada por faixa. Se null for contrato explícito, alinhar tipo TS em escopo posterior.
- **Proveniência opcional literal:** provider string/null, classification_source string/null, has_vocals bool/null, energy low/medium/high/null. Não exige novo enum fechado de provider. Para fonte desconhecida, a UI preserva identificador; novo significado de classificação precisa ser acordado, sem inferência automática por fonte/ai_used.
- **Links opcionais normalizados:** spotify/youtube/provider/search URLs válidas conforme política do adaptador; as três primeiras chaves têm significados próprios, search segue ressalva acima. Nenhum link Spotify, streaming, imagem, tag ou descrição é obrigatório para renderizar.
- **Envelope de descoberta:** items em ordem com item normalizado, recommendation_id string/null; posição fornecida no tipo mas ordem visual segue array. meta.hint é texto React seguro; degraded/has_more/next_offset controlam aviso/retry/página. parsed_query é opcional. ai_used/sources agregados não definem a origem/classificação por item no frontend.
- **Reading:** items acima, playlist.total_duration_ms/tracks_count e flags duration_estimated/target_duration_ms/target_met/shortfall_ms são necessárias para resumo honesto da meta de duração online. Não substituir faixas reais conhecidas por estimativas sem flag. SavePlaylist exige recommendation_id e itens; explicação/favoritos também são condicionais a essa origem, não ao provider.
- **Continuação:** identidade preservada para exclusões UUID cumulativas, snapshot de query/filtros, cursor e has_more; não muda contrato por provider. Limite200 e cursor0–300 existentes, sem reset/transcodificação frontend de IDs durante troca de fonte.

## Fixtures existentes e limites da cobertura

- `frontend/tests/music-metadata.mjs:17–26` já descreve known/ai_estimate/provider_tags/null/ausência, local, fonte ausente e provider alternativo `fonte-de-fixture`/classificação desconhecida. A última espera `Fonte: fonte-de-fixture · Com voz · Energia não informada`.
- `frontend/tests/music-metadata.mjs:47–48,65–69` inclui ai_used/sources agregados MusicBrainz/local enquanto itens têm fatos próprios; asserções verificam não inferir origem/estimativa de tags/ausência/agregado. Não prova consistência/licença de todos os provedores do lote.
- `frontend/tests/smoke.mjs:102–109,119–129`, `frontend/tests/playlists.mjs:15,117` usam links.provider MusicBrainz mas esperam **Ver fonte**, não nome MusicBrainz. Não cobrem página/link search de outra plataforma.
- `frontend/tests/continuation.mjs:120–121` inclui Reading sem provider/classificação e duração conhecida; não demonstra Reading exibindo rótulos por faixa nem lote misto de fontes. Não executar nem ampliar fixtures nesta revisão.

## Handoff

Relatório liberado ao Maestro. Pode manter frontend intacto durante protocolo/injeção Backend desde que payload normalizado e semântica de links/envelope acima permaneçam. As únicas decisões apontadas são convenção search, null explícito de duration_ms e eventual atribuição/classificação por faixa fora da descoberta; nenhuma justifica redesign ou nova dependência nesta unidade. Aguardar escopo do Maestro antes de qualquer patch/teste/QA novo.
