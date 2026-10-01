# ADR-0014 — Playlists por proprietário com cópia das faixas

## Estado

Implementado e testado em SQLite em 2026-10-01. SQL PostgreSQL gerado e conferido; execução real, concorrência nesse banco e interface de playlists pendentes.

## Contexto

Cadastro/login já funcionam na interface. O próximo passo do ponto de retomada é persistir playlists/salvos antes de integrá-los à conta. Recomendações públicas ainda são anônimas e mantidas somente no cache do processo por até uma hora/256 resultados. O catálogo musical local usa IDs estáveis em código; os itens externos conhecidos ficam em `music_catalog`, como JSON.

## Decisão

- Criar `playlists` com `user_id` obrigatório e `playlist_tracks` com posição, FK para `music_catalog` e uma cópia JSON dos metadados. Consultar/listar/excluir sempre com filtro do proprietário derivado do JWT. Recursos de outra conta e recursos ausentes têm o mesmo 404.
- Oferecer POST/GET/GET por ID/DELETE autenticados. Criação manual aceita 1–25 músicas únicas do catálogo; criação por origem aceita somente trilha de leitura ainda disponível, inteira ou um subconjunto ordenado. Nenhuma chamada externa ocorre ao salvar/listar/consultar/excluir.
- Validar toda a seleção antes de escrever e gravar playlist, catálogo local necessário e faixas na mesma transação. Falhas no banco revertem tudo. Exclusão da playlist conserva o catálogo compartilhado.
- Cópias de metadados e durações preservam o resultado salvo, mesmo após mudanças do catálogo/reinício. Duração desconhecida continua desconhecida na faixa; o total pode ser estimado e é identificado por `duration_estimated`. Total usa bigint, pois a soma de 25 durações válidas pode exceder integer no PostgreSQL.
- `source_recommendation_id` é proveniência sem FK. Não constitui histórico pessoal nem comprova propriedade da consulta: o resultado é público/anônimo, e seu UUID imprevisível permite usá-lo enquanto disponível, assim como as explicações públicas. Depois de salvo, o novo recurso fica privado à conta que o criou. Nenhum endpoint de playlist devolve query/contexto da origem.
- Ler a cópia do cache no event loop antes de enviar a transação ao pool de threads. Não estender TTL nem recuperar uma recomendação expirada a partir de músicas enviadas no corpo.
- Habilitar FKs nas conexões SQLite da aplicação para aplicar CASCADE e RESTRICT também no modo local.

## Alternativas

Persistir todo o histórico/recomendações antes das playlists ampliaria a etapa para contratos de privacidade e personalização ainda pendentes. Referenciar apenas o catálogo faria playlists antigas mudarem silenciosamente quando o provider atualizasse os dados. Aceitar metadados enviados pelo cliente impediria validar a existência das faixas.

## Consequências e validação

Mais armazenamento por faixa, limitado a 25 faixas manuais e 60 por trilha de leitura (ampliação de 2026-10-01 para comportar trilhas longas); listas paginadas retornam resumos sem carregar as cópias. Não há edição, exportação, reprodução, favoritos nem personalização nesta etapa. O salvamento por origem precisa acontecer no processo que conserva o resultado; múltiplas instâncias exigirão cache compartilhado ou recomendações persistentes com autorização própria.

Testes cobrem acesso entre contas, JWT inválido/expirado e conta inativa, persistência após reinício, ordem/subconjuntos, TTL/origem inválida, duração real/estimada, preservação de metadados, rollback completo, cascatas/restrição de catálogo e upgrade/downgrade. Migração real PostgreSQL e refresh concorrente continuam como gates de infraestrutura.

## Referências

- [Contrato HTTP](../05-API-Specification.md#7-playlists-playlists)
- [Modelo de dados](../04-Data-Model.md#412-playlists-e-playlist_tracks)
- [ADR-0006 — autenticação](0006-jwt-authentication-strategy.md)
- [ADR-0013 — modo local](0013-free-local-mode.md)
