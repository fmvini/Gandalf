# MusicProvider — auditoria de persistência e cache, 2026-10-02

## Resultado e escopo

Auditoria de aplicação/modelos/migrations **somente leitura**, iniciada sobre HEAD `d5c9b45`. Nenhuma necessidade de migration confirmada para protocolo/injeção inicial MusicProvider. Cache de busca já isola fontes; catálogo JSON depende da identidade normalizada entregue pelo adaptador. Foram reproduzidas três violações **sintéticas** admitidas pelo store; nenhuma leitura de dados existentes nem evidência de corrupção real/legado.

Reserva de escrita: somente este documento. Diagnóstico ignorado permitido, com duas tabelas reais em **SQLite novo em memória**, sem aplicar migrations nem iniciar app. Nenhum Docker/PG/API8000/Groq/rede, suíte auth, Git ou documento compartilhado. Backend reserva provider base/musicbrainz, main, recomendações/trilha online e testes próprios; Banco não os editou nem duplicou seus testes.

Escopo/achados iniciais enviados primeiro ao Maestro via maestri ask; Backend recebeu riscos/contrato e resultados do diagnóstico. Este registro é evidência do store e baseline, **não aprovação de um adaptador externo novo nem dos patches Backend em elaboração**.

## Persistência implementada

| Componente | Contrato atual e limite |
|---|---|
| `music_catalog`, model online / migration0005 | Apenas `id VARCHAR36 PK` e `data JSONB NOT NULL` (JSON SQLite). Não há colunas provider/external_id, UNIQUE(provider,external_id), validação UUID ou CHECK das propriedades/proveniência no JSON. |
| `OnlineStore.save_music` | Upsert por **id**, atualizando todo o data; transação única por lote. Metadados posteriores da mesma gravação substituem os anteriores. Não impede mudança de provider/external_id sob o mesmo id. |
| `OnlineStore.music_by_id` | Busca `str(item_id)` na PK. A rota detalhe recebe UUID e produz sua representação canônica; ID armazenado com representação incompatível pode não ser encontrado. |
| `external_search_cache`, model / migration0004 | Chave UNIQUE(entity_type,provider,query,result_limit), colunas NOT NULL, expires_at bigint indexado. Não existe uma tabela separada chamada provider_cache: nesta unidade o cache lógico de fontes usa essa tabela. |
| `OnlineStore.get/put` | Tipo ONLINE; provider é parâmetro genérico, sem dependência MusicBrainz. Read somente enquanto expires_at > agora; não renova TTL. Put atualiza response/expiry e remove entradas expiradas globalmente; não valida provider declarado no corpo/items. |
| Playlist / detalhe | `PlaylistTrack.music_id` FK RESTRICT→music_catalog.id; playlist também guarda snapshot do item. Playlist manual e GET detalhe consultam catálogo; favoritos/snapshots de recomendação não devem redefinir a identidade da fonte. Nenhuma mudança desses contratos proposta. |

Model e migration concordam nas estruturas auditadas. A tabela genérica JSON pode comportar adaptadores sem mudar schema **desde que a fronteira garanta identidade e proveniência**. O UNIQUE(provider,external_id) descrito para Music no modelo de dados de referência não é constraint implementada em music_catalog; não confundir desenho de catálogo tipado com esta implementação mínima. O trecho de docs04 que diz que só buscas de livros usam external_search_cache também está historicamente desatualizado. Documento compartilhado não foi editado; Maestro decide sua consolidação.

## Identidade, normalização e paginação MusicBrainz no baseline

- external_id é MBID validado/canonizado com UUID; id público é **UUID5(NAMESPACE_URL, URL canônica https://musicbrainz.org/recording/{MBID})**. Título, artista e tags não entram na identidade. Preservar exatamente esses IDs e dados legados; não recalcular com novo namespace de nome/display da fonte.
- Normalize exige título e artist-credit úteis; trunca título/artista, filtra tags e duração. duration_ms é int positivo ou **None**; has_vocals/energy começam **None**. Não converter desconhecido em false/low, duração0 nem dado medido. Links provider/search são metadados públicos, não chaves persistentes de lookup.
- Busca retorna items, total=len(items normalizados), provider e has_more. total não é necessariamente a contagem remota; has_more representa continuação da página remota mesmo se itens forem descartados pela normalização/filtros.
- Cache usa text/tag + query strip/casefold; reading-v2 inclui instrumental, offset entra quando não zero e limit é outra coluna da chave. O adaptador deve distinguir qualquer outro parâmetro que altere resultados e versões de normalização, sem reaproveitar chave de outra semântica.
- No baseline MusicBrainz.search salva itens no catálogo e publica cache; em cache hit retorna o corpo existente. O protocolo de search sozinho não persiste itens. Um adaptador alternativo injetado que omita save_music pode retornar busca útil, mas deixar GET detalhe/playlist manual sem catálogo. Persistência precisa ser responsabilidade explícita, não efeito implícito da factory.

## Dependências MusicBrainz identificadas em leitura

1. `providers/base.py` tinha somente BookProvider; main construía diretamente MusicBrainzProvider quando online. Faltava seam de protocolo/injeção musical na partida; isso pertence à unidade Backend.
2. `online_soundtrack.py` descartava qualquer item cujo provider != musicbrainz, mesmo com duração real compatível; fontes/hint/explanation também fixavam MusicBrainz. Esse gate impede leitura de outra fonte normalizada. Identificado estaticamente; Banco não duplicou o teste de trilha do Backend.
3. `online_recommendations.py` preenchia vocais/energia desconhecidos usando escolhas da IA para qualquer fonte, mas marcava classification_source=ai_estimate somente quando provider era MusicBrainz. Essa marca também era incondicional dentro do ramo MB, mesmo sem inferência concreta. A provenance precisa acompanhar **o campo efetivamente inferido**, preservando known/provider_tags; não depender do nome da fonte.

Os textos/rótulos específicos de MusicBrainz dentro do próprio adaptador são adequados; não confundir com condições hardcoded em consumidores genéricos. O cache base e o schema não exigem MusicBrainz e não são impedimento para a injeção inicial.

## Reprodução mínima offline do store

Script ignorado `.impeccable/runtime/music_provider_store_audit.py`; saída `.impeccable/runtime/music-provider-store-audit-result.json`. Execução em memória com somente MusicCatalog/ExternalSearchCache criadas via metadata, usando OnlineStore real, normalizador MusicBrainz real e clock mockado. Não importou/iniciou app, não chamou AIUsage/reserve_ai_call e não enviou requisições. `alternate_fixture` é **apenas fixture sintética**, não fonte implementada.

**Nove checks de comportamento esperado observados:** isolamento provider; separação limit/offset; read não renova TTL; expiração na fronteira; purga mantém outro provider LIVE; vazio é cache hit; IDs com namespaces distintos coexistem; campos desconhecidos None sobrevivem ao JSON; MB mantém ID quando título muda.

| Condição sintética deliberada | Reprodução e resultado observado | Conclusão limitada |
|---|---|---|
| Duas fontes com mesmo UUID | Salvar MB, depois alternate_fixture usando exatamente seu id. music_by_id desse UUID devolve data.provider=alternate_fixture. | Store admite sobrescrita de proveniência se o adaptador violar unicidade global. Não demonstrado com dois IDs corretamente namespaced. |
| UUID em maiúsculas | Salvar string UUID uppercase e consultar com UUID(...), que canoniza para lowercase. Lookup retorna None. | Contrato precisa exigir representação canônica antes de persistir; não exigir migration por essa entrada inválida. |
| Cache com fonte divergente | put(partição musicbrainz, corpo provider=alternate_fixture); get(musicbrainz,mesma chave/limite) retorna esse corpo divergente. | Chave isola partições; store não garante coerência interna do payload. Não é vazamento entre chaves distintas de providers corretos. |

Saída OBSERVATIONS_COMPLETE, zero network_calls, três linhas sintéticas no catálogo após as operações. Os flags true nesses três casos indicam **a exposição reproduzida**, não aprovação dos inputs inválidos. Nenhum assertion fail da aplicação nem suite executada. Isso não prova comportamento concorrente PostgreSQL, corrupção do catálogo existente, dois adaptadores reais colidindo, nem falha do normalizador MusicBrainz atual.

Ruff check/format do diagnóstico passaram. Comando offline, se necessária reprodução futura autorizada:

```powershell
.\api\.venv\Scripts\python.exe .impeccable/runtime/music_provider_store_audit.py
```

Snapshot às **22:57:18 UTC**, fontes iguais antes/depois:

| Fonte / artefato | SHA256 |
|---|---|
| `api/app/services/online_store.py` | `BE39C47EE16EE8C44C6C250E75E0671D704598721075D4BACC50CF4D2A140300` |
| `api/app/models/online.py` | `66CF5123DD81D94A0FCB980B72E66C6C8E2CA7CB77C7159ECD7E8FE4EF6E7EB0` |
| `api/app/models/external_search_cache.py` | `83DBAD5F6D4B57C3BB587D270A598F3A8EB1A7A11805FDC55A38307E17EBF4A5` |
| `api/app/providers/musicbrainz.py` | `98400F42CE8497526A2CB11573FD8F6C8F9E88859464DC6A159156F691598977` |
| Diagnóstico ignorado | `721006DFB5AF0CBFA3654265F53D6A02AA278EDEFC121A7FF97199A690D95A87` |
| Resultado ignorado | `8D46195C8B36CF144FC629BECEC1BB87F7D7DA29C6485321FA374F59DCF02DAD` |

## Contrato proposto pelo Backend e continuidade mínima

Backend informou MusicProvider name + search(query,limit=20,*,by_tag,offset,reading,instrumental), com resultado normalizado items/total/provider/has_more; UUID canônico determinista por fonte/external_id, MB UUID5 URL preservado; duração/vocais/energia nullable e classification_source opcional. Name deve coincidir com provider do resultado/itens externos, diferentes de local. Reading verificará coerência antes de aceitar, mantendo durações90–600s e filtros. Persistência/cache OnlineStore serão responsabilidade explícita do adaptador para suportar GET detalhe; factory não fecha recursos alheios. Sem detalhe/similar, novo provider concreto, schema/dados/config.

Backend também comunicou correção planejada de ai_estimate somente ao inferir unknown de qualquer fonte, preservando known/provider_tags; seus testes serão sintéticos. **Isso é contrato/escopo informado, não validação Banco do código final Backend.** Não há patch Banco proposto em OnlineStore/model/migration nesta unidade. Caso seja desejado endurecer admissão de payload/UUID no futuro, coordenar uma unidade própria de validação antes do store, com regressões desses inputs e definição de resposta segura; não reescrever catálogo/cache/IDs legados automaticamente.

Maestro/Backend devem fechar os testes de protocolo/injeção/consistência/persistência fake e provenance em suas reservas. Sucesso de mocks não aprova disponibilidade/qualidade de fonte alternativa online. Banco entrega este documento e evidências ignoradas; **freeze/liberado**, sem novos testes/probes/edições após envio sem solicitação. Maestro serializa docs compartilhados/Git; nenhum push Banco.
