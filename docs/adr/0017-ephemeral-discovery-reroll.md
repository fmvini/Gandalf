# ADR-0017 — Renovação efêmera de descobertas

## Estado

Backend implementado em 2026-10-02; testes com fontes simuladas aprovados. Commits locais bloqueados pelo sandbox; frontend e avaliação online real possuem validações separadas.

## Contexto

Livros já permitiam renovar o mesmo pedido, mas música não aceitava IDs vistos. A disponibilidade de livros considerava avisos e candidatos rejeitados, podendo prometer continuação no limite de páginas ou após filtros eliminarem toda a amostra.

## Decisão

- Música aceita `excluded_music_ids`; livros conserva `excluded_book_ids`. Até 200 UUIDs cumulativos e offset 0–300; query/filtros/limite preservados do pedido submetido. Vistos ficam somente no cliente; sem modelo, migração, histórico automático ou feedback. IDs retornados pelos serviços reais são preservados, inclusive reconciliação de catálogo legado.
- Online consulta uma página de 15 por termo, até dois termos, reutilizando cache por consulta/página/limite. Excluir vistos e referências antes da IA e das regras; deduplicar por UUID e título/autoria. Preservar filtros/relevância/diversidade de dois itens por criador em cada batch.
- Classificar um candidato extra, no máximo 25, na mesma chamada IA; entregar apenas `limit`. `has_more` indica esse excedente aceito ou página externa permitida até offset 300. Rejeições/avisos sozinhos não contam. `next_offset=null` conserva a página atual; no local, somente exclusões fazem avançar. Aos 200 vistos enviados, encerrar indicação de continuação.
- Preservar o limite/cooldown/contabilização Groq existente. Cache IA de 24 horas guarda Intent/Selection por hash; não é cache de origem sem consulta/intenção nem histórico de vistos. Aumentar a amostra na mesma chamada pode alterar tokens dentro dos limites existentes, sem aumentar chamadas ou cota.
- Fallback identificado por fontes, hint e degraded, usando metadados externos ou catálogo editorial real. Não criar títulos/IDs/durações. Falha do banco/cache de origem configurado permanece 503; fonte/IA indisponível pode produzir batch degradado vazio. A lista anterior é responsabilidade do cliente durante espera/cancelamento/erro/fim.
- Trilha online continua isolada em `online_soundtrack.py`/`generate_soundtrack`, com meta de duração real obrigatória. O re-roll de descoberta não altera sua paginação, quantidade, duração ou fallback.

## Consequências

`has_more` descreve a amostra limitada, não o catálogo global; resultados podem ser curtos/vazios após filtros ou decisões IA. IDs de outras gravações/edições podem surgir em outro batch: o contrato cumulativo exclui UUIDs e a deduplicação de título/autoria é dentro da amostra atual, sem armazenar histórico global de obras. Busca nova reinicia vistos; mudanças no catálogo/LLM podem mudar ranking entre pedidos. PostgreSQL, E2E frontend e disponibilidade externa real precisam de evidências próprias.

## Referências

- [Contrato implementado](../05-API-Specification.md#61-post-recommendationsmusic)
- [MusicBrainz — paginação por limit/offset](https://musicbrainz.org/doc/MusicBrainz_API/Search)
- [Open Library — busca paginada](https://openlibrary.org/dev/docs/api/search)
- [Groq — códigos de erro HTTP](https://console.groq.com/docs/errors)
