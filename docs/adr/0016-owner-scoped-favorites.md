# ADR-0016 — Favoritos individuais por conta

## Estado

Implementado e validado em SQLite em 2026-10-01, sobre `0008_favorites` (`bfa418b`). PostgreSQL real continua pendente.

## Contexto

Usuários precisam salvar músicas e livros individualmente e consultar/remover sua coleção na conta. Playlists representam uma sequência de músicas; feedback pertence a outro contrato e pode influenciar ranking. O cache público resolve origens entre instâncias, mas expira e não representa uma coleção pessoal.

## Decisão

- Criar coleção própria em `/api/v1/users/me/favorites`, sempre autenticada e filtrada por conta ativa. Não persistir automaticamente consultas, nem emitir `SAVE` no feedback ou alterar ranking/playlist.
- POST aceita apenas `recommendation_id` e `item_id`. Resolver origem no cache compartilhado, validar pertencimento ao resultado e derivar MUSIC/BOOK dos metadados confiáveis da fonte. Salvar cópia do objeto item, sem score, explicação ou contexto da solicitação. Não buscar provedores adicionais nem aceitar snapshot enviado pelo cliente.
- Preservar metadados/links originais e distinguir duração conhecida de estimada. Guardar UUID de proveniência sem FK para o cache; item UUID sem FK polimórfica para catálogo. Favoritos sobrevivem à expiração/evicção e alterações/ausência do catálogo.
- Impor UNIQUE `(user_id, type, item_id)` no banco e usar `ON CONFLICT DO UPDATE` sem mudança de valores (`id = favorites.id`) com `RETURNING` do snapshot. Evita a janela entre conflito/SELECT e DELETE concorrente sob READ COMMITTED; locks duram até o commit. Retornar 201 quando o UUID candidato foi inserido/200 quando já existe, conservando identidade, snapshot, proveniência e data da primeira gravação. Todos os POSTs exigem origem válida; repetir com origem expirada retorna 404 sem alterar o favorito existente.
- Listar por `created_at DESC, id DESC`, com tipo opcional, limit 1–50 e offset até 100.000. Oferecer `POST /status` com tipo e até 60 IDs únicos para estado de botões em lote; retornar apenas mapa item→favorito da conta. Não depender do cache para operações privadas já salvas.
- DELETE filtrado por conta retorna 204 inclusive para ID ausente/de outra conta. Resultado idempotente não revela existência de dados privados. Exclusão da conta no banco faz cascata dos favoritos; endpoint de exclusão de conta ainda é roadmap.
- Falha de banco/cache retorna 503 genérico, sem fallback local nem detalhes SQL; origem/item ausente 404, entrada inválida 422, autenticação ausente/inválida 401. I/O de banco fora do event loop, com snapshot da origem destacado antes da transação de salvamento.

## Alternativas

Reutilizar feedback confundiria coleção com sinal de preferência. Reutilizar playlists não representa livros ou itens independentes. Aceitar metadados do cliente permitiria conteúdo arbitrário e divergência da origem. FK para cache/catálogo impediria salvar fontes externas ou perderia salvos quando a origem expira. Atualizar snapshot em repetição contrariaria a expectativa de conservar o item salvo.

## Consequências e validação

Dados explicitamente salvos ficam vinculados à conta, com snapshot persistente e proveniência até exclusão. Não há histórico de consultas; política de exportação/eliminação de conta requer etapa própria. Origem expirada exige buscar novamente antes de salvar; os já salvos continuam acessíveis. Concorrência usa unicidade do banco, sem mutex por processo. PostgreSQL tem suporte de modelo/migração/SQL; exige execução real em ambiente descartável para fechar o gate.

Validação final: 346 testes backend aprovados, incluindo 31 de favoritos e 17 de migração, Ruff/formatação e gates v7 K=5/10 sem mudanças/regressões. Casos incluem música/livro/trilha, snapshot original sem renovação, tipo/conta separados, estado em lote, filtros/paginação/desempate, reinício entre aplicações, expiração, entrada/autenticação inválida, cache/tabela indisponíveis, falha SQL ao validar conta com resposta 503, rollback após falha de commit e concorrência de criar/excluir com três processos SQLite. O teste multiprocessos do cache bloqueado por named pipe no sandbox do agente de banco também passou no terminal Maestro. Revisão independente detectou os caminhos de falha de autenticação e da antiga consulta após conflito; ambas corrigidas e reavaliadas sem novos bloqueadores. PostgreSQL real segue pendente; a correção READ COMMITTED é sustentada pelo contrato SQL/documentação e ainda exige execução nesse banco.

## Referências

- [Contrato HTTP](../05-API-Specification.md#83-favoritos-individuais--contrato-implementado)
- [Modelo de dados](../04-Data-Model.md#415-favorites)
- [ADR-0015 — cache de origens](0015-shared-recommendation-cache.md)
- [ADR-0014 — playlists](0014-owner-scoped-playlists.md)
- [PostgreSQL — isolamento READ COMMITTED e ON CONFLICT](https://www.postgresql.org/docs/current/transaction-iso.html#XACT-READ-COMMITTED)
