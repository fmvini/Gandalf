# Architecture Decision Records (ADRs)

Este diretório reúne as decisões de arquitetura do documento 15 previsto no [escopo detalhado, tópico 70](../00-Escopo-Detalhado.md#70-documentação-técnica). O estado de cada registro descreve **a decisão de desenho**, não uma implementação já concluída. A aplicação ainda está na fase de especificação.

| ADR | Assunto | Estado |
|---|---|---|
| [0001](0001-modular-monolith.md) | Monólito modular | Aceita no desenho |
| [0002](0002-llm-interprets-backend-ranks.md) | IA interpreta; backend ranqueia | Aceita no desenho |
| [0003](0003-pgvector-for-vector-search.md) | PostgreSQL + pgvector | Aceita no desenho; parâmetros pendentes |
| [0004](0004-external-data-providers.md) | Abstração de fontes externas | Aceita no desenho; fornecedores pendentes |
| [0005](0005-llm-and-embedding-provider-abstraction.md) | Abstração de LLM e embeddings | Aceita no desenho; modelos pendentes |
| [0006](0006-jwt-authentication-strategy.md) | JWT e rotação de refresh | Proposta; entrega do refresh pendente |
| [0012](0012-music-provider-selection.md) | Seleção do provedor musical | Pendente de avaliação |

A numeração 0012 preserva a referência já usada no [README](../../README.md) e no [roadmap](../12-development-roadmap.md). Os números 0007 a 0011 ficam livres para decisões futuras; não representam registros existentes.

## Quando criar ou atualizar um ADR

Registre uma escolha que afete fronteiras entre módulos, persistência, segurança, integração externa, qualidade das recomendações ou custo operacional. Alterações locais e facilmente reversíveis podem ficar apenas no PR. Consulte os itens em aberto da [SRS](../02-SRS.md), da [AI Architecture](../06-ai-architecture.md), da [Recommendation Engine Specification](../07-recommendation-engine-specification.md) e da [Security Specification](../09-security-specification.md).

Cada ADR deve conter:

1. **Estado:** proposta, aceita no desenho, implementada, substituída ou rejeitada; indique o que ainda falta validar.
2. **Contexto e forças:** requisito, restrições e risco que motivam a decisão.
3. **Decisão:** escolha específica, incluindo limites e exclusões.
4. **Alternativas:** opções consideradas e motivo para não adotá-las agora.
5. **Consequências e validação:** benefícios, custos, riscos e evidência necessária para fechar pendências.
6. **Referências:** links para documentos de requisitos e ADRs relacionados.

Use o próximo número livre em quatro dígitos e um nome curto em inglês, como `0013-cache-strategy.md`. Abra um PR para discutir a decisão. Se uma escolha aceita mudar, escreva um novo ADR e marque o anterior como **substituído**, preservando o histórico. Não reescreva retrospectivamente o motivo original.
