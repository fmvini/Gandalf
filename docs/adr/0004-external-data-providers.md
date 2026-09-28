# ADR-0004 — Portas para fontes externas de música e livros

**Estado:** Aceita no desenho para a abstração; escolha final das fontes pendente.

## Contexto

As recomendações só podem incluir itens reais, mas APIs externas variam em cobertura, metadados, limites e termos de uso. O catálogo local precisa receber objetos normalizados sem acoplar ranking ou interface ao formato de cada serviço.

## Decisão

Definir contratos `MusicProvider` e `BookProvider` e adaptadores por serviço. Cada adaptador valida e normaliza identificadores, metadados e URLs; o retriever reúne resultados externos e do catálogo local, remove duplicatas e mantém proveniência. Timeouts, cache, rate limits e fallback entre fontes pertencem à camada de integração, não ao ranking. Open Library e Google Books são candidatos para livros; MusicBrainz e Last.fm são candidatos para música, sem escolha final nesta etapa.

## Alternativas consideradas

- **Chamar APIs diretamente em services ou rotas:** reduz código inicial, mas espalha formatos e falhas externas.
- **Usar uma fonte única fixa:** simplifica integração, porém aumenta dependência de cobertura e disponibilidade.

## Consequências e validação

Novos adaptadores ficam localizados e testáveis por contrato, ao custo de um modelo normalizado e política clara de deduplicação. Antes de ativar uma fonte, verificar disponibilidade, busca, campos necessários, limites, estabilidade, atribuição e licença. A decisão específica sobre música será registrada no [ADR-0012](0012-music-provider-selection.md).

**Referências:** [Escopo §§29–31](../00-Escopo-Detalhado.md#30-fontes-de-dados), [Arquitetura §§6 e 9](../03-System-Architecture.md#6-componentes-principais), [Testing Strategy §6.10](../10-testing-strategy.md#610-providers-externos).
