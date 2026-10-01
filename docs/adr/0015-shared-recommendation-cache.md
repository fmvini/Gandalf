# ADR-0015 — Cache compartilhado de resultados anônimos

## Estado

Implementado e validado em SQLite em 2026-10-01, sobre o schema `0007_recommendation_results`. Substitui a dependência do cache por processo descrita no ADR-0014. Execução e concorrência reais PostgreSQL continuam pendentes.

## Contexto

Salvar uma trilha ou abrir uma explicação podia retornar 404 quando a requisição chegava a outro processo ou após reiniciar a API, mesmo antes da validade de uma hora. O frontend usa os endpoints atuais de playlists; esse problema precisa ser resolvido sem transformar recomendações públicas em histórico pessoal ou exigir afinidade de sessão no balanceador.

## Decisão

- Com banco configurado, armazenar em `recommendation_results` somente a identidade original, `items` e `playlist`, quando presente. Não persistir consulta, intenção interpretada, contexto, metadados da requisição ou conta. Publicar somente após finalizar filtros, paginação e resumo de duração.
- Compartilhar snapshots entre instâncias que usam o mesmo banco. Expirar após 3.600 segundos UTC, sem renovar ao consultar ou atualizar o mesmo resultado ainda válido. Limitar a 256 resultados no banco inteiro, removendo os mais antigos; empate usa UUID. A gravação recém-publicada é conservada mesmo se timestamps empatam.
- Gravar/limitar em uma transação: SQLite usa seu bloqueio de escrita; PostgreSQL usa `pg_advisory_xact_lock` com chave exclusiva desta aplicação antes da limpeza/upsert/evicção. Não há lock mantido durante consultas externas ou gravação de uma playlist.
- Usar o banco como fonte única, sem segundo cache em memória que permita acessar um resultado expirado/removido. Carregar cópias independentes para explicação/salvamento; I/O de banco roda no pool de threads, com sessões próprias.
- Expirados são excluídos durante acessos/gravações ou `prune()`. Sem tráfego, linhas podem permanecer em disco, mas não são acessíveis após o TTL. Não há job periódico nem eliminação automática em backups.
- Sem banco configurado, preservar o modo público em memória: uma hora, 256 resultados por processo, sem persistência após reinício. Com banco configurado mas indisponível/desatualizado, criação de resultados, explicações e salvamento por origem retornam `503 SERVICE_UNAVAILABLE`, sem fallback de memória nem detalhes SQL. Aplicar `alembic upgrade head` antes de iniciar; `local.py` faz isso automaticamente.
- Manter endpoints, corpos e isolamento por proprietário das playlists. ID desconhecido/expirado/removido continua 404. A origem pública não comprova propriedade: sua identidade imprevisível permite acesso temporário, como antes. A playlist salva pertence à conta autenticada e sobrevive à expiração/evicção do cache, sem FK para ele.

## Alternativas

Afinidade de sessão não resolve reinício nem compartilha resultados. Redis adicionaria infraestrutura e outra política de disponibilidade ao modo local. Persistir consultas com usuário exigiria um contrato próprio de histórico/privacidade; armazenar o corpo integral da recomendação reteria dados desnecessários. O banco já disponível permite resolver esta etapa com snapshots mínimos e limite explícito.

## Consequências e validação

Mais escritas e transações curtas no banco; consultas do cache também removem expirados. Instâncias precisam do mesmo banco e relógios UTC sincronizados. A configuração com banco passa a exigir o schema 0007 para gerar/recuperar recomendações. Não altera ranking, provedores, chaves, cotas ou duração de trilhas.

Testes cobrem duas aplicações com conexões independentes, salvar/explicar após mudança de instância, reinício, isolamento entre contas, expiração exata sem renovação, cópias independentes, payload mínimo, evicção global sem ressurreição, publicação com timestamps empatados, falha de banco e três processos SQLite gravando simultaneamente. Migrações preservam contas/playlists. PostgreSQL real e CI hospedada ainda exigem validação própria.

## Referências

- [ADR-0014 — playlists](0014-owner-scoped-playlists.md)
- [Modelo do cache](../04-Data-Model.md)
- [Contrato HTTP](../05-API-Specification.md#7-playlists-playlists)
- [PostgreSQL — bloqueios consultivos por transação](https://www.postgresql.org/docs/current/explicit-locking.html#ADVISORY-LOCKS)
