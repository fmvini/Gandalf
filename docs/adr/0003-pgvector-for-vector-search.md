# ADR-0003 — PostgreSQL com pgvector para busca vetorial

**Estado:** Aceita no desenho para banco e extensão; modelo, dimensão e parâmetros do índice ainda dependem de validação.

## Contexto

O sistema precisa persistir usuários, interações, catálogo e embeddings, além de combinar filtros relacionais com similaridade semântica. O MVP tem volume inicialmente pequeno e busca simplicidade operacional.

## Decisão

Usar PostgreSQL como banco principal e a extensão pgvector para consultas vetoriais, com migrações Alembic. Manter a origem, o modelo e a dimensão de cada vetor rastreáveis. O [Modelo de Dados](../04-Data-Model.md) propõe uma tabela `embeddings` separada e índice HNSW com distância cosseno; esta proposta requer benchmark e alinhamento com o modelo escolhido antes de fixar o schema.

## Alternativas consideradas

- **Banco vetorial separado:** pode oferecer recursos específicos, mas acrescenta sincronização e operação a um catálogo ainda pequeno.
- **Embeddings apenas em memória ou busca exata permanente:** simplifica o início, mas não atende ao crescimento nem à persistência compartilhada.
- **IVFFlat em vez de HNSW:** pode ter custo de memória menor; comparar recall, latência e manutenção com dados representativos.

## Consequências e validação

Uma única base reduz a complexidade do MVP, mas o campo `vector(N)` vincula o esquema à dimensão do modelo. Antes da migração inicial, escolher modelo/dimensão em conjunto com o [ADR-0005](0005-llm-and-embedding-provider-abstraction.md), medir busca com catálogo representativo e documentar re-embedding e reindexação para trocas futuras. Não tratar o HNSW ou a tabela separada como decisão já implementada.

**Referências:** [Escopo §§33 e 36](../00-Escopo-Detalhado.md#33-stack-principal), [Modelo de Dados §4.6](../04-Data-Model.md#46-embeddings), [Deployment Guide §8](../11-deployment-guide.md#8-banco-de-dados).
