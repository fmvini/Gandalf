# ADR-0002 — IA interpreta; backend seleciona e ranqueia

**Estado:** Aceita no desenho; ainda não implementada.

## Contexto

O produto precisa recomendar obras reais, personalizadas e explicáveis. Uma lista livre gerada pelo LLM pode conter itens inventados e não oferece controle suficiente de filtros, preferência do usuário ou pesos do ranking.

## Decisão

O LLM transforma a consulta em intenção estruturada validada por schema. Providers e catálogo local fornecem candidatos identificáveis. O backend aplica filtros, similaridade, personalização, ranking e diversidade; guarda fatores do score. O LLM pode explicar esses fatores **sob demanda**, mas não escolhe nem adiciona itens à lista final. Saída inválida do parser aciona retry ou fallback controlado.

## Alternativas consideradas

- **LLM gera recomendações finais:** simples de demonstrar, porém sem garantia de existência ou ranking auditável.
- **Busca apenas por palavras-chave:** barata e determinística, mas fraca para descrições subjetivas e multilíngues.

## Consequências e validação

O pipeline tem mais componentes e precisa de dados externos confiáveis. Em troca, permite testes determinísticos e inspeção de cada resultado. O *golden set* deve medir qualidade, e testes devem exigir que 100% dos itens tenham origem válida em provider ou catálogo.

**Referências:** [Escopo §§19–21 e 27–29](../00-Escopo-Detalhado.md#19-sistema-de-recomendação), [AI Architecture](../06-ai-architecture.md), [Recommendation Engine Specification](../07-recommendation-engine-specification.md), [Testing Strategy §8](../10-testing-strategy.md#8-avaliação-offline-da-qualidade-das-recomendações).
