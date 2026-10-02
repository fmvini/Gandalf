# Auditoria de persistência de capas — 2026-10-02

## Escopo e coordenação

- Auditoria somente leitura de catálogo/cache/snapshots `cover_url`. Backend reserva correção de `api/app/providers/open_library.py`; Frontend reserva componentes/páginas/imagens. Maestro valida suíte integral e serializa commits.
- Nenhum serviço, modelo, migration, TTL, catálogo, favorito ou processo alterado por Banco. Nenhuma suite API duplicada, stage/commit/push, instalação PostgreSQL ou pedido de credenciais.
- Documentos anteriores `docs/04-Data-Model.md` e `docs/database-session-2026-10-02.md` conferidos e preservados. O diff anterior de docs04 continua 3 linhas adicionadas/1 removida, com contrato upsert revisado e reroll efêmero. Maestro mantém os três documentos compartilhados.

## Evidências sanitizadas do banco existente

Banco confirmado pelo Backend: `api/.local/gandalf.db`, usado por `local.py` da API em 8000. Leitura com `sqlite3.connect(...?mode=ro, uri=True)`, `PRAGMA query_only=ON` e transação de leitura; **não** importado/executado `local_settings`/`prepare` nem iniciadas chamadas API capazes de persistir buscas. Snapshot principal em Unix ms `1790944774310`; schema `0008_favorites`.

| Dados inspecionados | Resultado |
|---|---|
| Catálogo `books` | 210 registros: 206 Open Library e 4 locais. |
| `cover_url` nulo/vazio | 32 Open Library + 4 locais = 36. Não foram encontrados outros domínios nas URLs preenchidas. |
| Capas preenchidas | 174 URLs `https://covers.openlibrary.org/b/id/{id}-M.jpg`, todas sem `default=false`. Formato válido não comprova imagem disponível. |
| IDs legados Open Library | **0** divergentes do UUID5 de `https://openlibrary.org/works/{external_id}`. Não há evidência de problema de ID no catálogo examinado. |
| Cache externo BOOK válido | 0 linhas. |
| Cache externo BOOK expirado | 5 linhas, todas com prefixo atual `pt-editions-v2:`; 15 itens, 2 sem capa, **0** URLs divergentes do catálogo correspondente. |
| `recommendation_results` | 0 linhas válidas/expiradas no snapshot. |
| Favoritos BOOK | 0 snapshots no snapshot consultado. Sem inferir ausência de favoritos em outros bancos/instantes. |

Exemplos públicos de catálogo: `OL8400950W` (The Blade Itself) com cover ID `14543422`; `OL5738154W` (The Hero of Ages) com `14658094`. Um exemplo sem capa é `OL1011083W` (Dunas). Esses metadados não comprovam falha HTTP nem equivalência com outra obra de título parecido. Não foram lidos/expostos usuários, tokens, senhas, consultas privadas ou chaves.

## Causas comprovadas e limites

1. **Defeito reproduzido na normalização, antes da correção do Backend:** `open_library.py:85` começa com `raw.cover_i`, mas substitui pelo `cover_i` da primeira edição portuguesa se for inteiro, sem exigir valor positivo. Obra com capa `123` e edição portuguesa `-1` ou `0` resulta em `cover_url=None`, descartando a capa válida da obra. Edição com `None` conserva a capa da obra. Reprodução pura com `normalize_book`, sem rede/banco/escrita. Backend confirmou o contrato: preferir edição portuguesa quando ID positivo; fallback à obra quando a edição não tem capa válida; ausência verdadeira permanece null. O UUID ficou igual em todos esses casos.
2. **Primeira edição portuguesa sem capa:** com obra sem capa, primeira edição PT `-1` e segunda PT `456`, o normalizador auditado também retorna null, pois escolhe a primeira edição. Isso é comportamento reproduzido; procurar outra edição válida envolve decidir se título/capa devem corresponder à mesma edição. Não improvisar essa regra nem misturar metadados sem critério.
3. **Imagem branca não aciona necessariamente `onError`:** URLs legadas sem `default=false` podem receber placeholder HTTP 200. A [documentação oficial da Covers API](https://openlibrary.org/dev/docs/api/covers) informa imagem branca por padrão quando a capa não existe e 404 com `?default=false`. Isso explica um mecanismo possível de capa vazia; **não confirma** que os 174 IDs observados retornam placeholders. Backend/Frontend estão comparando respostas reais e dimensões.
4. **Cache persistido antigo ativo não demonstrado:** não havia linhas BOOK válidas nem prefixos anteriores no snapshot examinado. Os cinco expirados não passam o filtro `expires_at > now` de `BookService._load_cached`. Não há base para expurgo global de cache como correção deste incidente. O cache em memória da instância e estado da rota/browser não foram inspecionados por Banco.
5. **Catálogo não expira com o cache:** `BookService.get_by_id` lê o registro persistido, sem consulta externa/TTL. Uma URL ausente ou inválida gravada anteriormente pode continuar aparecendo no seletor por ID. Nova busca com fonte acessível faz upsert dos metadados, incluindo capa, mantendo ID existente. Não foi possível atribuir os 32 nulls especificamente ao defeito de edição: o banco guarda URL resultante, não o payload original com todos os candidatos `cover_i`.
6. **Snapshots preservam a capa antiga por contrato:** caches de busca e origens serializam o item; favoritos copiam somente o item e deduplicação preserva o primeiro snapshot. Atualizar catálogo não reescreve origens/favoritos salvos. Embora não haja favorito BOOK nesta leitura, apagar/recriar ou alterar favoritos globalmente não é solução autorizada; não mudar o contrato de snapshots para corrigir imagens.

Frontend confirmou estaticamente, antes de suas correções: Discovery/Favorites têm fallback local limitado aos três títulos exatos e `provider=local`; estado de falha não está associado à URL. O seletor/selecionado de Ler com Música usa `cover_url` sem `onError` nem fallback local. Nenhum título de obra externa deve ser usado para atribuir capa local de um homônimo.

Arquivos locais de capa existem e têm assinatura JPEG e dimensões no cabeçalho: `dune.jpg` 30.520 bytes / 265×475; `hobbit.jpg` 36.051 / 330×500; `secret-garden.jpg` 44.404 / 361×500. Isso verifica arquivos/cabeçalho, **não** carregamento no browser. A tentativa opcional de decodificar com Pillow encontrou módulo ausente; nada instalado. Frontend verifica `img`/`naturalWidth` no ambiente real.

## Plano mínimo para dados legados

1. Backend corrigir validação de capa na normalização e política de URL ausente/404; Frontend tratar null, erro HTTP, placeholder e troca de URL de modo coerente nos três fluxos. Confirmar exemplos reais no browser e API antes de declarar causa única resolvida. Testes/commits dessas mudanças pertencem aos responsáveis/ Maestro.
2. Para novas buscas, usar a normalização corrigida e as chaves/cache existentes; sem alteração de schema. Aguardar expiração natural do cache em memória/persistido. Se o Backend mudar versão da chave por mudança de semântica, registrar motivo; Banco não mudou prefixo/TTL nem purgou linhas.
3. Para livro legado ainda afetado em `get_by_id`, confirmar identidade por `provider` + `external_id`/URL canônica e consultar fonte dessa obra. Preferir nova busca normal capaz de atualizar somente o catálogo envolvido, mantendo ID. Não parear por título nem recalcular UUID antigo.
4. Se for necessária correção de dados em lote, primeiro produzir **plano read-only** com IDs/URLs antigas e novas verificadas na mesma obra/edição, contagens e diferenças. Executar somente no escopo explicitamente autorizado, em transação e com preservação dos IDs/dados anteriores; nenhuma necessidade atual de migration. Não executar UPDATE/DELETE automático neste incidente.
5. Favoritos e origens antigas: primeiro usar fallback visual seguro sem mudar snapshot. Uma futura operação de atualizar metadados de favorito precisa contrato explícito de ownership/preservação da primeira gravação; não reinterpretar POST repetido como refresh de capa nem expurgar favoritos existentes.

## Entrega e gates

- Novo arquivo exclusivo: `docs/database-covers-session-2026-10-02.md`. Os dois arquivos entregues anteriormente permanecem liberados ao Maestro.
- Achado de edição inválida, contagens sanitizadas e limites reportados ao Backend/Frontend/Maestro via skill [maestri](C:/Users/vinic/.agents/skills/maestri/SKILL.md), usando os terminais existentes.
- Nenhuma URL HTTP problemática atual comprovada por esta auditoria de Banco; aguardar evidências de Backend/Frontend e registrar separadamente. Os nulls do catálogo são reais, mas a origem exata deles não é reconstruível só pela URL persistida.
- Gate PostgreSQL/pgvector real anterior permanece pendente; este diagnóstico SQLite read-only não o fecha. Nenhuma suite integral/API/UI declarada aprovada aqui. Nenhum stage/commit/push por Banco; Maestro integra relatório no checkpoint autorizado.
