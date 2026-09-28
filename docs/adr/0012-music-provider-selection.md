# ADR-0012 — Seleção do provedor musical

**Estado:** Pendente de avaliação na Fase 2; nenhum provedor foi selecionado.

## Contexto

O fluxo de descoberta depende de metadados suficientes para buscas, embeddings e fatores de contexto como atmosfera, energia e vocais. O [roadmap](../12-development-roadmap.md) define a escolha do provedor musical como portão G1 antes de avançar no motor de recomendação. O [ADR-0004](0004-external-data-providers.md) já define o contrato de integração, mas não escolhe a fonte.

## Decisão a tomar

Avaliar MusicBrainz, Last.fm e outras fontes candidatas em dados e condições reais; escolher fonte primária e, se necessário, uma fonte complementar ou fallback. O resultado deve registrar o que cada serviço fornece diretamente, o que será inferido por regras ou enriquecimento ancorado, limites de uso e obrigação de atribuição. Spotify não é pressuposto como fonte do MVP: a integração de conta/exportação é pós-MVP.

## Critérios de comparação

| Critério | Evidência necessária |
|---|---|
| Disponibilidade e estabilidade | Testes de busca/ID, falhas e comportamento em indisponibilidade |
| Cobertura e qualidade | Amostra de faixas de estilos distintos; título, artista, tags, descrições, duração, links e identificadores |
| Adequação à recomendação | Capacidade de obter atributos para humor/energia/vocais, diretamente ou com proveniência e confiança |
| Limites e custo | Rate limits, quotas, chaves, cache permitido e custo no volume estimado do MVP |
| Termos de uso | Licença de metadados/imagens, atribuição, retenção e uso em produto público |
| Integração | Busca por texto/referência/tags, deduplicação, latência e fallback |

## Alternativas consideradas

- **Uma fonte só:** operação simples; pode deixar lacunas de tags ou cobertura.
- **Fontes complementares:** metadados mais ricos; aumenta deduplicação, latência e manutenção.
- **Catálogo local sem consulta externa:** rápido após aquecimento; falha no início frio e não sustenta a garantia de cobertura.

## Consequências e fechamento

Até a avaliação, os nomes citados nos documentos são candidatos, não escolhas finais. Para fechar este ADR, anexar uma matriz comparativa com exemplos e resultados de testes de contrato, declarar a fonte escolhida e fallback, e atualizar configuração, documentação e critérios de G1. Se nenhum candidato atender, revisar a estratégia de dados antes de prometer qualidade no MVP.

**Referências:** [Escopo §30](../00-Escopo-Detalhado.md#30-fontes-de-dados), [Development Roadmap §4](../12-development-roadmap.md#4-portões-de-qualidade-quality-gates), [Recommendation Engine Specification](../07-recommendation-engine-specification.md).
