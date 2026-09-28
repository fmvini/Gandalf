# ADR-0013 — Modo local sem serviços pagos

- Data: 2026-09-28
- Estado: aceito para execução local

## Contexto

O usuário solicitou um sistema funcional sem gastar dinheiro. A interface dos três fluxos públicos já existia, mas os endpoints de recomendação não estavam implementados. Docker estava indisponível e autenticação exigia configuração manual de banco e segredo.

## Decisão

Usar SQLite, migrações automáticas, segredo gerado uma única vez, catálogo editorial embarcado e ranking determinístico de temas. Não chamar LLM, embeddings ou providers externos nesse modo. Executar em loopback.

O catálogo inicial contém 18 livros e 25 músicas reais, com descrições e etiquetas editoriais. Links apontam para buscas nas fontes, sem simular IDs externos nem hospedar mídia. A interpretação em português usa vocabulário limitado, exclusões simples e referências por título; não equivale a compreensão semântica por modelo.

Duração de trilha é uma estimativa de cinco minutos por faixa. O catálogo não identifica gravações específicas, portanto não fornece duração exata das faixas. API e interface informam essa limitação.

Manter Open Library e PostgreSQL opcionais. O ADR-0012 sobre provider musical externo permanece pendente e não bloqueia o modo local. Recomendações permanecem locais mesmo se a busca de livros usar Open Library.

## Consequências

- Os três fluxos públicos funcionam sem rede após instalação. Abrir links externos exige conexão.
- Nenhuma despesa de API, hospedagem ou assinatura é introduzida.
- Consultas desconhecidas retornam vazio; referências precisam estar no catálogo e etiquetas são subjetivas.
- Contas/cache persistem em SQLite. Resultados anônimos e explicações expiram em uma hora ou no reinício, até 256 buscas por processo.
- Histórico, feedback, salvos, UI de conta, embeddings, áudio e deploy permanecem pendentes.
- Próximo passo: expandir catálogo e avaliar ranking. Novas integrações devem preservar a ausência de cobrança.
