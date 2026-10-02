# Contrato inicial de MusicProvider — 2026-10-02

**Estado:** Backend implementado e congelado, 163 testes focados aprovados; gate Frontend em curso. Não certifica G1 nem ativa uma fonte alternativa em produção. [ADR-0004](adr/0004-external-data-providers.md), [avaliação G1](adr/0012-music-provider-selection.md).

## Superfície do port

`api/app/providers/base.py` define `name: str` e `search(query, limit=20, *, by_tag=False, offset=0, reading=False, instrumental=False)`. A busca assíncrona devolve `MusicSearchResult`: `items`, `total`, `provider`, `has_more`. O contrato inicial cobre as chamadas já usadas; lookup externo, similares, embeddings e novas fontes/configurações continuam futuros.

O item normalizado contém UUID canônico em string, título, artista, tags, links, provider e external_id. `duration_ms`, `has_vocals` e `energy` podem ser null; desconhecido não equivale a zero, ausência de voz ou energia baixa. `classification_source` é opcional e informa proveniência explícita. Valores conhecidos prevalecem sobre sugestões da IA; `ai_estimate` identifica preenchimento efetivo de atributo desconhecido por estimativa válida, independentemente da fonte.

## Identidade e persistência

- O adaptador atribui IDs deterministas em namespace da fonte/identidade externa; `str(UUID(id)) == id`. MusicBrainz conserva o UUID5 derivado da URL canônica recording e não recalcula IDs existentes.
- `result.provider`, `item.provider` e `adapter.name` devem ser consistentes. Nome externo estável, não vazio/diferente de local, compatível com provider varchar32 do cache. IDs e links vêm da fonte/adaptador, nunca da Selection da IA.
- Cache, normalização, rate limit, TTL e persistência dos itens via OnlineStore pertencem ao adaptador. A injeção não acrescenta automaticamente save_music nem um get_by_id remoto; GET detalhe continua consultando o catálogo persistido.
- `music_catalog` tem PK string36 e JSON: não há colunas/constraints próprias de provider/external_id. O store não valida o namespace ou a coerência do payload. Estes são requisitos para adaptadores confiáveis, não proteções novas do banco. Um adaptador que reutilize UUID de outra fonte pode sobrescrevê-la; o diagnóstico sintético não demonstra corrupção nos dados atuais.
- `external_search_cache` já isola tipo/provider/chave/limite. O adaptador inclui modalidade/página na chave e não renova o TTL apenas por ler. Não há tabela provider_cache separada.

## Integração e leitura

`create_app(..., music_provider=adapter)` injeta a instância no modo online. Sem injeção, continua MusicBrainz; no modo offline, continuam catálogo/ranking locais sem ativar esse adaptador. O caller conserva propriedade dos recursos do adaptador injetado; a factory fecha apenas os recursos que ela própria abre no lifespan.

Leitura online exige item da fonte externa correspondente ao adaptador, nunca `local`, com duração inteira informada de 90–600 segundos. Meta.sources e textos identificam a fonte efetiva. Tags só preenchem vocais/energia desconhecidos, com proveniência provider_tags; não substituem atributos conhecidos. Filtros, referências/exclusões, oito páginas, limite60/quatro por artista e duração-alvo continuam obrigatórios; uma trilha insuficiente retorna SOUNDTRACK_INCOMPLETE. O port não transforma tags em medição acústica nem permite completar tempo com duração inventada.

Links preservam a precedência da interface: spotify, youtube, provider, search e fallback. `links.provider` abre a fonte de metadados. A revisão da semântica genérica de `links.search` e dos rótulos está em validação; links de reprodução não provam que o catálogo oferece áudio.

## Gates e limites

Backend:163 PASS no subset MusicProvider/online/continuation/reroll/ai_selection/music_filters (29 novos +134 existentes);29 PASS finais após ajuste de lint equivalente. Três reproduções reading falharam antes do patch e passaram depois. Ruff/formatação7 arquivos/diff-check PASS. Banco: nove observações esperadas e três violações sintéticas de precondições em SQLite novo, sem migration/dados reais/rede. [Relatório Backend](backend-music-provider-2026-10-02.md), [relatório Banco](database-music-provider-2026-10-02.md). Frontend em curso; fixtures e mocks não medem disponibilidade, cobertura musical, gênero ou qualidade auditiva de fontes externas.

| Critério G1 | Estado / próxima prova |
|---|---|
| Desacoplamento | Port inicial/injeção nesta unidade; não constitui seleção final da fonte |
| Identidade/cache/proveniência | Contrato e diagnóstico offline; uma nova implementação deve provar conformidade antes de ativação |
| Instrumental estrito | Unknown continua unknown; matriz por gravação e revisão humana pendentes |
| Cobertura de metadados | MusicBrainz experimental; amostra maior de tags/duração/atributos e comparação com outra fonte pendentes |
| Termos/atribuição | Conferir campos usados, retenção, uso comercial e licenças antes de publicar; revisão completa pendente |
| Operação | Rate limit distribuído por IP/egress e avaliação real de latência/falhas pendentes |

Na documentação oficial consultada em 2026-10-02, o [rate limit público MusicBrainz](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting) é medido por IP de origem, em média uma requisição por segundo, além de controles de aplicação/carga. O intervalo1,1s por instância do Gandalf não coordena múltiplos processos compartilhando IP. A [FAQ](https://musicbrainz.org/doc/MusicBrainz_API/FAQ) distingue acesso não comercial gratuito e planos/contato para uso comercial, e exige User-Agent identificável. A página Data License recusou a leitura direta com HTTP429; a revisão de licenças por campo não é declarada concluída. Nenhuma busca de recordings, nova recomendação ou chamada LLM foi executada por essa consulta documental.
