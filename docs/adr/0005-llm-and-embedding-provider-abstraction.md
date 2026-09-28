# ADR-0005 — Abstrair LLM e serviço de embeddings

**Estado:** Aceita no desenho para as interfaces; fornecedores, modelos e política de dados pendentes.

## Contexto

Parsing estruturado, embeddings e explicações têm perfis distintos de custo, qualidade e latência. A escolha inicial de fornecedor pode mudar, e o modelo de embeddings afeta o banco e a avaliação de qualidade.

## Decisão

Expor `LLMClient` para saída estruturada e texto, e `EmbeddingService` para vetores individuais e em lote. Injetar implementações concretas, versionar prompts e schemas, validar saídas e usar fakes nos testes padrão. Configurar fornecedores no backend por ambiente; nunca enviar chaves ao frontend. Registrar modelo e dimensão de cada embedding.

## Alternativas consideradas

- **SDK de um fornecedor em toda a aplicação:** implementação inicial menor, mas amplia o custo de troca e dificulta testes.
- **Um único modelo para todas as etapas:** configuração simples, mas pode elevar custo ou reduzir qualidade em parsing, explicação ou similaridade.

## Consequências e validação

As interfaces acrescentam código, mas limitam dependência do fornecedor. A seleção concreta exige comparar conformidade do JSON, qualidade PT/EN, dimensão, latência, custo, disponibilidade e política de retenção/treinamento. Uma troca de modelo vetorial exige re-embedding e possível migração do `vector(N)`; coordenar com o [ADR-0003](0003-pgvector-for-vector-search.md). Registrar a escolha final e seus resultados de avaliação nesta decisão ou em um ADR substituto.

**Referências:** [AI Architecture §13](../06-ai-architecture.md#13-decisões-em-aberto-registrar-em-adrs), [SRS §11](../02-SRS.md#11-itens-em-aberto), [Security Specification §9](../09-security-specification.md#9-segurança-da-camada-de-ia).
