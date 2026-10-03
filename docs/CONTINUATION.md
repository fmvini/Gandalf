# Ponto de retomada — 2026-10-03

## Etapa atual — integração local de deploy validada

Maestro coordenou Backend/Frontend/Banco com reservas exclusivas e consolidou o runner após liberação. [Receita executável](deployment-integration.md): Compose base+PostgreSQL, entrypoint `api/deploy.py` com ambiente explícito/migrations antes de servir, build estático Nginx e proxy com DNS dinâmico. CA de builder opcional via segredo BuildKit temporário; nenhum TLS desabilitado.

**Gate final ca-7 PASS/exit0:** UUID `d611ad28-dff0-4523-abc0-8b6c049891aa`; imagens atuais, PostgreSQL18.6/head0008/vector0.8.6/citext1.8, create7/verify6 checks e restart da mesma API. SQL2 contas/2 favoritos/1 playlist/11 faixas/3 caches, ownership e hashes antes/depois/verify exatos, AI0. Browser/console/externo0; aborts de logout classificados somente com Request204/UI/refresh401 comprovados. Sourcefreeze/cleanup verificados; recursos UUID/tmpfs removidos. Artefato ignorado `.impeccable/ci/deployment-gate.json`, hash `a909c28c4569410e3fcd54883a0459bc5c72598a7e4e02669106240684fce9d2`.

**Checks:** Backend38 testes, runner94 guards, Node67 guards/deadlines/proof, Ruff/format98/actionlint PASS. Nginx antes502/depois200 na troca de IP com URI/Nginx preservados. Não repetir suítes gerais ou gates aprovados sem mudanças/falhas novas. Dados/config/serviços existentes e quota IA não foram usados; nenhum push.

Próximos passos: executar os quatro jobs hospedados após push explicitamente autorizado; para deploy público, configurar HTTPS, segredos, backups e permissões de migrations/extensões do banco de destino. Gate aprovado cobre uma API offline/cold-start e restart; não certifica fontes online/G1, HTTP entre várias APIs, rollout pré-populado/mistura de versões ou zero downtime. Para continuar G1, seguir o checkpoint abaixo e seu requisito de coleta autorizada.

## Checkpoint anterior — avaliação G1 offline preparada

Maestro coordenou os mesmos três terminais: Backend implementou CLI/testes; Banco e Frontend revisaram identidade/proveniência em documentos exclusivos. Nova unidade: `api/scripts/music_provider_eval.py`, `api/tests/test_music_provider_eval.py`, [protocolo G1](music-provider-g1-evaluation.md) e três JSONs em `docs/evaluation/`. Sem alteração da aplicação, schema, dependências, CI, runtime ou dados existentes.

**Gates:**84 testes novos PASS em0,30s, Ruff/formatação2 arquivos PASS. CLI real executado pelo Maestro: fixture6 pares/5 observados/1 erro/1 vazio/3 não vazios/1 ausente/3 linhas, template24 ausentes/zero observações, contrato inválido exit1 e entrada stdin inválida exit2 sanitizados. g1_approved=false invariável, inclusive recorded. Mapas de identidade incluem registros com metadados inválidos; conflitos globais não escolhem vencedor. Duplicatas/reobservações/variantes e denominadores elegíveis explícitos. Não repetir suites gerais/auth/UI ou diagnósticos Banco aprovados sem novo motivo.

**Estado:** MusicBrainz permanece experimental. Plano12 casos/seis grupos é exploratório e ainda não coletado; Last.fm continua candidato sem novo adaptador/chave/integração. Consultadas somente páginas públicas de documentação, sem recordings/API8000/DB/LLM. Condições e licenças por campo registradas no protocolo; não são aprovação de publicação. O último snapshot de runtime é o checkpoint abaixo; esta unidade não reiniciou nem verificou os serviços.

Próximos passos específicos:

1. Revisar critérios prévios de aceitação e correspondência por gravação/revisão humana. O manifesto propõe24 chamadas de busca/zero retries/enriquecimento/LLM, mas `collection.authorized=false`: obter orçamento/escopo explícitos e resolver acesso/termos antes de executar coleta.
2. Conservar diário sanitizado, versões/horário/cache/orçamento/hash e pedidos/flags do manifesto. Alimentar snapshots recorded de mesma fase, executar CLI e revisar fatos/proveniência por atributo; não converter template vazio ou fixture em cobertura real.
3. Decidir fonte/fallback e atualizar ADR-0012 somente com evidência comparativa e condições de uso resolvidas. Latência/cache, descrições/gêneros e utilidade para embeddings exigem provas próprias; G1 permanece aberto. CI hospedada depende de push explícito; histórico/perfil/feedback exige contrato próprio.

Relatórios congelados: `backend-music-evaluation-2026-10-03.md`, `database-music-evaluation-2026-10-03.md`, `frontend-music-evaluation-2026-10-03.md`. Git local/docs compartilhados serializados pelo Maestro; nenhum push.

## Checkpoint anterior — MusicProvider inicial concluído e runtime atualizado

Terminais existentes coordenados com reservas exclusivas; entregas Backend/Banco congeladas e Frontend finalizado pelo Maestro após limite de uso do terminal. Commits locais `e5b4d75` (port/factory/proveniência/known) e `753a9c1` (links/tipos/fixtures), sem push. [Contrato](music-provider-contract.md), relatórios [Backend](backend-music-provider-2026-10-02.md), [Banco](database-music-provider-2026-10-02.md) e [Frontend](frontend-music-provider-2026-10-02.md).

**Entrega:** MusicProvider name/search/flags/envelope tipado, injetável somente online; default MusicBrainz e modo offline preservados. Adaptador mantém propriedade de recursos e responsabilidade de normalização/cache/persistência. Leitura valida adapter/envelope/item e duração real; textos/fontes dinâmicos. Tags preenchem apenas unknown com provider_tags; discovery preserva known e marca ai_estimate somente ao inferir atributo desconhecido válido. Interface conserva URLs/precedência; busca genérica usa Buscar faixa, YouTube somente para hostname correspondente. Duração null explícita nos tipos.

**Validação:**163 testes Backend focados PASS (29 novos+134 afetados),29 finais após lint equivalente; três reproduções reading FAIL antes/PASS depois. Ruff/formatação7/diff-check PASS. Banco executou diagnóstico SQLite descartável de duas tabelas: nove observações esperadas e três violações sintéticas admitidas pelo store, documentadas como precondições de adaptador confiável, não corrupção atual/schema patch. Frontend14 fixtures em dois lotes10+4 PASS/requests2/zero erros/rede externa; prova de rótulo FAIL antes/PASS depois,16 capturas e revisão320px/claro/escuro. TypeScript/build2050 módulos PASS, bundle504,22kB/gzip158,18kB, aviso>500 não fatal. Não houve repetição das suítes auth/geral, PG real ou recomendações externas/LLM nesta unidade.

**Runtime atual conferido:** API identificada launcher9084/worker20872 recarregada, agora launcher34864/worker31344 em127.0.0.1:8000; health/readiness/status200, database/schema ok, catálogo online e Groq configurado `openai/gpt-oss-20b`. `.env` e jwt-secret conferidos inalterados por hash, dados originais `api/.local` preservados. Frontend25716/localhost:5173 e PG10140/5432 preservados; módulo `/src/lib/api.ts` servido200 contém correção. Portas55432/55433 sem listener. PIDs são snapshot, verificar identidade antes de agir. Health/configuração não comprova busca real ou qualidade musical.

Próximos passos específicos:

1. Fechar desenho da avaliação G1 a partir de ADR-0012 e `music-provider-contract.md`: amostra por gravação, metadados conhecidos versus unknown, instrumental estrito, relevância e revisão humana. Definir orçamento explícito antes de chamadas externas/LLM; não ativar uma segunda fonte apenas por existir injeção.
2. Revisar termos/licenças por campo/uso comercial e coordenação de rate limit por IP entre processos antes de publicar/ampliar operação. Matriz e limitações atuais não certificam G1.
3. CI hospedada só após push explicitamente autorizado. Gates auth ampliados (HTTP entre duas apps, rollout e logout/refresh) continuam pendentes conforme checkpoint anterior. Histórico/perfil/feedback exige contrato próprio antes de schema/API/UI.

Registros abaixo são históricos; seguir esta etapa e o topo de DEVELOPMENT_LOG para retomada.

## Checkpoint anterior — autenticação corrigida, gates aprovados e commits locais

Maestro coordenou os terminais existentes Frontend, Backend e Banco de Dados, com reservas exclusivas e Git/docs compartilhados serializados. Entregas auth encerradas e versionadas; nenhum push. Commits locais: `e6278dd` headers/logs/limitador, `7192c54` hash/SQL/refresh SQLite, `290eb69` submit/cancelamento frontend, `5b7f17a` serialização PG por família e `2f00bc1` regressão PG versionada/CI.

**Validação:** 470 testes passaram na rodada integral inicial; os três casos multiprocessos bloqueados antes das asserções passaram depois, com aprovação específica, sem alterar asserções. São 473 casos originais aprovados em rodadas complementares, não uma nova execução monolítica. Subset auth/security final52 PASS; headers/logs/limitador14 PASS; novo gate20 testes offline/12 recusas CLI PASS. Ruff/formatação e actionlint PASS. Frontend Node/session/form/TypeScript, auth browser/continuation/live SQLite temporário e build2050 módulos PASS; aviso não fatal de chunk504,06kB. Suítes já aprovadas não foram duplicadas.

**PostgreSQL real:** Banco reproduziu bug ancestral/descendente antes (200/401, espera observada, um refresh ativo); advisory lock da família antes de row locks e releitura após espera corrigiram para zero ativos. Gate ignorado pós-patch e script versionado passaram em instâncias distintas descartáveis PostgreSQL18.6/READ COMMITTED: quatro grupos, seis constraints/digests, mesmo-token200/401/zero ativos e ownership/logout/expiração/cascata. Terceira instância validou também o trecho literal da CI que cria outro DBUUID vazio. Todas removidas por ID/identidade conferidos; PG5432 preservado. Script: `api/scripts/postgres_auth_gate.py`; execução opt-in só em DBUUID vazio, conforme `CI.md`. Evidências before/after/versioned ignoradas separadas.

**Runtime conferido após commits:** API8000 estava ausente e foi restaurada em modo online, usando `api/.local`/config/modelo originais. Launcher9084/worker20872; `/health`, `/health/ready` e `/api/v1/system/status`200, database/schema ok, catálogo online, Groq configurado `openai/gpt-oss-20b`. Isso verifica configuração, sem chamada externa/LLM nem nova cota consumida por esta retomada auth. Frontend25716 em5173 e PostgreSQL10140 em5432 preservados; portas descartáveis55432/55433 livres na consulta final. PID é snapshot, conferir antes de qualquer ação futura.

Próximos passos:

1. Após **push explicitamente autorizado**, observar os três jobs/artefatos da CI; execução hospedada/deploy ainda pendentes. Sem push automático.
2. Antes de ampliar garantia PG, criar gate próprio para HTTP entre duas apps, rollout pré-populado/mistura de versões e corrida logout/refresh/desativação/exclusão. Não tratar os quatro grupos atuais como stress/segurança integral.
3. Continuar seleção musical a partir do checkpoint v7 abaixo: definir matriz/revisão humana para instrumental estrito e re-roll externo, respeitando orçamento autorizado. Health/config não comprova fontes/qualidade online.
4. Histórico/perfil/feedback exigem contrato próprio antes de schema/API/UI; não usar favoritos como eventos de feedback implícitos.

Relatórios: `backend-auth-session-2026-10-02.md`, `frontend-auth-session-2026-10-02.md`, `database-auth-session-2026-10-02.md`. Contratos API/security/ADR0006 e `DEVELOPMENT_LOG.md` refletem as correções. Registros abaixo preservam checkpoints históricos; os bloqueios então vigentes foram superados nos gates acima.

## Checkpoint anterior — auditoria auth com gates então bloqueados

Maestro retomou os terminais existentes Frontend, Backend e Banco de Dados. Código/testes e entregas estão congelados para revisão; a unidade de autenticação tem gates pendentes antes de conclusão integral. Cada agente reserva seus arquivos; Maestro serializa Git e documentos compartilhados.

Headers privados (`no-store`/`no-cache`), logs sanitizados de exceções auth e limitador com recuperação de chaves expiradas/capacidade limitada: 14 testes aprovados. Backend corrigiu hash inválido, refresh SQLite concorrente e falhas SQL com rollback/503: 48 testes auth/security aprovados. Frontend corrigiu envio duplicado e cancelamento antes/depois do refresh; testes Node/session/form, TypeScript, sintaxe e detector aprovados. Banco: 12 guards e dois checks de freeze por hash offline aprovados; nenhuma integração auth PG.

**Gate final Maestro:** suíte API completa 470 PASS/3 FAIL de ambiente em75,63s. Falhas antes das asserções, em multiprocessing.Pipe/CreateFile WinError5: `test_favorites.py::test_concurrent_processes_deduplicate_atomically`, `test_favorites.py::test_concurrent_repeated_create_and_delete_return_detached_snapshots`, `test_recommendation_cache.py::test_concurrent_sqlite_processes_enforce_global_capacity`. Não marcar suíte verde nem modificar esses testes para eliminar o bloqueio. Ruff `app tests scripts`/formatação79 PASS. Build frontend tentou `tsc -b && vite build`: tipos aprovados, Vite EPERM; live/continuation não executados por pré-requisitos bloqueados.

Bloqueios comprovados naquele checkpoint: browser `node tests/auth.mjs` falhou antes dos testes em `spawn EPERM` do esbuild; Banco não acessava o pipe Docker. Política então vigente `approval never` impedia elevar/contornar. **Git também estava bloqueado**: `git add -- <arquivos relevantes>` falhou ao criar `.git/index.lock` (`Permission denied`). Nenhum commit/push novo, container, restart ou alteração de dados existentes naquela fase. A retomada autorizada seguinte resolveu os gates específicos descritos no topo.

Próximos passos:

1. Ler os três relatórios `backend-auth-session-2026-10-02.md`, `frontend-auth-session-2026-10-02.md` e `database-auth-session-2026-10-02.md`; revisar diffs congelados. Não repetir gates aprovados sem motivo.
2. Em sessão com subprocessos/pipes permitidos, executar os três node IDs pytest acima e `node tests/auth.mjs`, `node tests/continuation.mjs`, `npm.cmd run build` e `node tests/live.mjs` em `frontend`, preservando serviços existentes e dados temporários exclusivos. Não interpretar testes Node sem DOM como QA browser.
3. Executar gate auth PostgreSQL em UMA instância descartável verificada; testar refresh concorrente/reuso e replay ancestral versus rotação descendente em READ COMMITTED. Esse último risco foi identificado por análise, ainda não reproduzido; não declarar resolvido nem aprovado.
4. Quando `.git` puder ser escrito, revisar `git diff`, rodar testes restantes e fazer commits seletivos coerentes com o log; não usar `git init`, `git add .` nem push automático.

## Checkpoint anterior — PostgreSQL real e seleção musical com metadados

Commits locais, sem push: `c13b552` gate PostgreSQL/pgvector e CI; `97b07b6` metadados conhecidos no seletor MUSIC; `89e2387` origem/classificação por faixa no frontend. Maestro coordenou Backend, Frontend e Banco, reservando Git e documentos compartilhados. As seções abaixo são checkpoints históricos; disponibilidade do Docker e PID/cota antigos não descrevem o runtime atual.

**PostgreSQL:** duas execuções reais aprovadas em Docker oficial PostgreSQL18.6/pgvector0.8.6/citext1.8, cada uma sobre banco vazio exclusivo. Script versionado `api/scripts/postgres_gate.py` verifica destino/identidade/schema vazio antes de migrar; 17 testes de proteção passaram. Cobertura: migrations/metadata/extensões/readiness, upserts e criar/excluir favoritos concorrentes, isolamento/primeiro snapshot, cache concorrente/TTL/limite256/cascata e roundtrip até base. Container UUID/label/tmpfs/loopback55432 removido após conferência de identidade; nenhum volume/dado existente alterado. Job PostgreSQL separado em CI usa imagem por digest e JSON final sanitizado; actionlint passou. **CI hospedada ainda não executada**, e HTTP autenticado entre instâncias PG, refresh concorrente, constraints negativas completas e rollout sobre dados existentes não foram cobertos. Receita, comandos e limites: [relatório Banco](database-docker-session-2026-10-02.md) e [CI](CI.md).

**Seleção/UI:** payload MUSIC transmite bool exato/null, energia válida/null e origem somente quando informada. Instrução preserva unknown e distingue classificação de medição; BOOK/Intent/filtros/índices/duração/modelo/chave/cota/TTL mantidos. Frontend apresenta fonte, estimativa/tags e valores desconhecidos por faixa, sem inferir origem de tags/ai_used. Backend: 134 testes do subset e 14 novos finais; Ruff/formato global86 passou. Frontend: módulo focado com dez fixtures/oito capturas, reroll completo afetado, TypeScript e build2050 módulos passaram (aviso não fatal de bundle503,70kB). Suítes integrais não repetidas nesta unidade; histórico permanece abaixo.

**Gate real após carregamento do commit:** exatamente duas POST limit3. “Jazz instrumental” retornou200, IA ativa/sem degradação, zero itens/next15. Controle “Jazz” retornou200, IA ativa/sem degradação, **três itens MusicBrainz** com vocais/energia nulos. Aprovação pontual de entrega externa, sem avaliação auditiva/gênero independente nem prova de melhora causal do ranking. Não converter desconhecido em instrumental; caso estrito segue pendente. Consumo **9→12/50**, três novas tentativas de orçamento seis, Intent live com expiry idêntico; nenhum retry manual/query extra. Relatório: [gate MUSIC real](backend-music-selection-live-session-2026-10-02.md). BOOK/capa externa e re-roll MUSIC local da etapa anterior continuam evidências separadas.

**Runtime atual:** única API online `127.0.0.1:8000`, worker **42664**, launcher40364, mesmo `api/.local` e modelo `openai/gpt-oss-20b`, status/readiness200 ao final. Substituiu somente o worker identificado31444 após porta livre confirmada. Frontend **25716** em `http://localhost:5173` (::1), PostgreSQL existente **10140**/5432 preservados. Confirmar identidade antes de qualquer restart; não presumir PIDs permanentes. Docker foi autorizado pelo usuário e ficou acessível fora do sandbox; indisponibilidade anterior é histórica.

Próximos passos:

1. Investigar offline o caso instrumental com fixtures públicas próprias: avaliar evidência vocal disponível, perda/ausência de classificação e seleção antes de propor alteração. Não relaxar filtros nem tratar null como instrumental; revisar gênero/relevância dos três itens do controle com avaliação humana.
2. Auditar separadamente `classification_source` de saída: MusicBrainz selecionado recebe `ai_estimate` inclusive quando classificação é nula/valor conhecido. UI preserva o literal; não corrigir proveniência incidentalmente nem alegar medição.
3. Validar re-roll BOOK externo/MUSIC externo e qualidade da trilha em amostras específicas, com orçamento coordenado e consumo antes/depois; duas POST desta etapa não testaram esgotamento/re-roll externo ou fecharam G1/G2.
4. Observar job PostgreSQL hospedado após envio explicitamente autorizado; ampliar HTTP/auth entre instâncias PG, constraints e refresh concorrente em DB descartável. O gate exige destino exclusivo; DATABASE_URL não converte fixtures SQLite.
5. Ler log/status, conferir Git/processos/cota ao retomar e manter commits seletivos sem push automático. Scripts/capturas de diagnóstico em `.impeccable/` são ignorados e podem não existir em outro checkout.

## Checkpoint anterior — fontes reais, capa externa e aviso de renovação

Retomada sobre `ffdd6a6`, com Backend/Frontend/Banco existentes e Git/documentos compartilhados serializados pelo Maestro. Fix de aviso no commit local `949f642`: re-roll vazio degradado explica a limitação da tentativa e preserva a seleção/retry. Módulo reroll afetado, TypeScript e 14 capturas por fixtures passaram; Maestro aprovou build de 2.050 módulos e revisou capturas mobile. Nenhuma nova suíte geral foi duplicada.

Cliente real `app.core.http.external_client` validou TLS/fontes: Open Library e MusicBrainz HTTP200, três itens normalizados por fonte; Groq interpretou o pedido público com sucesso. O probe inicial usou certifi padrão e falhou verify_code20; essa evidência não representava a aplicação, que já usa confiança do SO. Sem patch TLS, nova chave, troca de modelo/provider ou mudança da cota.

API real: “Músicas calmas para estudar” retornou dois lotes de três itens, IA ativa/sem degradação, cursor 0→15→30 e seis UUIDs sem repetição, **somente catálogo local**. “Livros de fantasia e aventura em portugues” retornou três obras Open Library em português com IA ativa/sem degradação. “Jazz instrumental” retornou vazio, IA ativa/sem degradação/next_offset15. MusicBrainz direto200 não comprova entrega musical externa no ranking; esse gate continua aberto. Uso observado **2→9/50** ao longo da etapa; nenhum retry manual para perseguir resultado.

Replay offline da consulta pública Jazz encontrou 15 candidatos MusicBrainz + três locais, filtro vocal instrumental e Selection da IA com **zero escolhas**. Não houve rejeições por filtro/score/diversidade; não foi ausência de candidatos. Somente hashes derivados dessa consulta/dados públicos, rede/reserva/escrita proibidas e nenhuma chamada efetivada. Motivo da omissão não vem no schema; metadados insuficientes são hipótese, não causa comprovada. Evidência ignorada `backend-online-jazz-offline-funnel-20261002.json` e relatório Backend.

Capa real de “O Hobbit” (`OL27482W`, cover14849956): BackendGET200/JPEG25.626bytes/180×285 e Maestro confirmou uma única GET200 no Chromium, imagem visível na descoberta em 390 px, mesmas dimensões e zero erros. No navegador, API foi simulada com os metadados públicos normalizados; não houve nova recomendação/LLM. Isso valida uma amostra de imagem externa/componente, não todas as capas do catálogo.

Serviços preservados: API online PID31444/8000, mesmo banco/config/modelo original, status/readiness200; frontend existente localhost:5173 preservado, sem restart/servidor persistente duplicado. PostgreSQL/pgvector real continua pendente: Docker sem daemon normal/elevado; PG18/5432 e volume do compose intocados. Harness local ignorado preparado/verificado apenas por import/guards, sem integração PG nem inclusão em Git.

Relatórios: `backend-online-session-2026-10-02.md`, `frontend-online-session-2026-10-02.md`, `database-postgres-session-2026-10-02.md`. Artefatos/scripts/capturas de diagnóstico ficam ignorados em `.impeccable/`; se ausentes em outro checkout, reconstruir a verificação antes de executá-la.

Próximos passos:

1. Priorizar qualidade da seleção musical: o funil Jazz já confirmou 18 candidatos/zero escolhas da IA. Avaliar o payload/metadados de voz/energia e amostras públicas antes de alterar prompt/fallback; não mudar filtros ou classificar desconhecido como instrumental para obter sucesso. Reconstruir fixtures próprias se caches expirarem, sem ler consultas privadas.
2. Validar seleção externa MUSIC e re-roll BOOK externo com orçamento explícito de testes/cota, preservando query/filtros/IDs/cursor. Amostras atuais não fecham G1/G2 nem avaliação musical/trilha completa.
3. Para PG, seguir preflight/receita do relatório Banco em um único container descartável com imagem local/porta55432 ou55433/bancoUUID/tmpfs; não usar compose/volume existente. Somente após execução real decidir integração versionada de testes/CI; não exportar DATABASE_URL esperando converter fixtures SQLite.
4. Manter commits locais seletivos e atualizar DEVELOPMENT_LOG; nenhum push automático. Confirmar Git/processos/cache/cota ao retomar, sem inferir disponibilidade permanente pelos HTTP200 desta etapa.

## Checkpoint anterior — commits, re-roll e capas

Ler primeiro as entradas recentes de `DEVELOPMENT_LOG.md`. Maestro coordenou os terminais existentes Frontend/Backend/Banco de Dados e serializou Git/documentos compartilhados; os registros de 01/10 e do sandbox inicialmente bloqueado são históricos. Todos os arquivos da entrega foram revisados e incluídos em commits locais seletivos, sem push.

Commits: `318d97a` favoritos backend; `f2adc7c` re-roll backend; `1663c2c` auditoria Banco; `ef0c284` normalizador de capas; `137d492` integração frontend favoritos/re-roll/componentes; `03a51e9` capas/responsividade frontend. Schema `0008_favorites` preservado; sem migração para vistos efêmeros. O commit final de documentação deve ser consultado em `git log`.

Validação: Maestro aprovou **366 testes backend**, inclusive três multiprocessos antes bloqueados; **38 testes de livros/capas** após fix; Ruff/formatação (84 arquivos) e gates v7 K=5/10 intactos. Dez módulos frontend aprovados em rodadas coordenadas: helper/smoke/components/auth/continuation/playlists/favorites da primeira suíte, reroll após correção Tab, covers pelo Frontend; Maestro reexecutou continuation/favorites/live após freeze. Live usa API real/SQLite temporário/duas contas e cobre persistência/isolamento/mobile/temas. Build final PASS, 2.050 módulos, aviso não fatal de bundle 502,97 kB. Não houve uma nova execução monolítica de npm test após as correções; resultados por rodada estão no log/relatórios.

Favoritos/renovação funcionam na integração testada. Re-roll MUSIC/BOOK conserva pedido/filtros enviados, vistos cumulativos, cursor e seleção durante erro/espera/cancelamento; limite de 200, sem histórico/feedback/autosave. Alert público oficial shadcn listado no 21st.dev e AnimatedContent React Bits adaptado para Motion existente, créditos/licença/movimento reduzido; impeccable/taste aplicados. MCP21st autenticado indisponível, sem afirmar cota/recuperação autenticada.

Capas: edição PT com `cover_i` inválido não apaga capa válida da obra; URLs novas usam `default=false`. BookCover compartilhado trata null/erro/1×1 e troca de URL; URL de metadado tem prioridade, asset local exige `provider=local`. Corrigidos seletor/selecionado de Ler com Música e dois defeitos a 320 px (margem do link em favoritos e texto dos modos). Frontend aprovou 60 capturas dark/light, 1440/390/320, movimento normal/reduzido; Maestro revisou capturas atuais e Duna visível no E2E com API/SQLite isolado. Home/JPEGs locais já funcionavam. Capa externa real/status/dimensões e catálogo online persistente pós-fix não comprovados por esses testes; diagnóstico de busca pós-fix não confirmou o alvo `provider=local`. Não expurgar cache/reescrever catálogo/snapshots: auditoria não demonstrou cache BOOK ativo legado.

Runtime: API antiga PID 37452/sessão 27472 encerrada via Ctrl+C após identidade confirmada. **Única API online em 127.0.0.1:8000, PID 31444**, launcher 39748, mesmo `api/.local`/config; status/readiness 200, modelo Groq original `openai/gpt-oss-20b`. Novo filho sem proxies HTTP/HTTPS/ALL, ambiente global intacto; nenhum incremento de cota pelo restart. Primeira interpretação falhou antes de HTTP; diagnóstico posterior recommendations/books pode ter reservado tentativa. Leitura RO final de `ai_usage` em 2026-10-02: **2/50**, sem troca de chave/modelo/limite. Sem evidência de chave inválida.

**Frontend existente: http://localhost:5173**, listener IPv6 `::1`, PID 25716, processo Vite do Gandalf confirmado; GET da página e BookCover transformado retornam 200, com verificação de `naturalWidth` e rastreamento de falha servidos. 127.0.0.1:5173 pode recusar por bind IPv6, sem indicar queda de localhost. Não foi criado servidor persistente duplicado. Confirmar identidade/portas antes de reiniciar; manter modo online e dados existentes.

Próxima sessão:

1. Conferir Git e processos; consultar os relatórios backend/frontend/database de sessão e capas em `docs/` para comandos e limites.
2. Quando transporte público estiver acessível, consultar uma obra/edição PT e sua cover_url/status/dimensões reais, sem LLM para diagnosticar capa.
3. Validar uma interpretação/recomendação externa dentro da cota existente, registrando fonte/ai_used/degraded e avisando usuário antes de mudar API/chave/modelo.
4. Retomar PostgreSQL/pgvector em instância descartável: Docker sem daemon; PG18 existente exige autenticação/vector não encontrado. Nenhum servidor/dado alterado. Não concluir gates online/PG por fixtures.

## Encerramento do dia — favoritos backend validados, frontend WIP

Usuário encerrou por hoje. Schema `0008_favorites` entregue em `bfa418b`; backend de favoritos implementado e validado: 346 testes, Ruff/formatação e gates v7 K=5/10 sem regressões. Contrato [8.3](05-API-Specification.md#83-favoritos-individuais--contrato-implementado): POST IDs `recommendation_id`/`item_id` (201 novo/200 existente), GET paginado/tipo, POST status em lote até 60 IDs e DELETE por proprietário (204 inclusive ausente/terceiro). Snapshot do servidor conserva primeira gravação, sobrevive a cache/reinício e não gera histórico/feedback/ranking. Revisão corrigiu falha SQL ao validar conta (503) e janela de DELETE concorrente usando upsert com RETURNING do snapshot. [ADR-0016](adr/0016-owner-scoped-favorites.md); PostgreSQL real permanece pendente.

**Retomar pelo frontend WIP antes de nova feature.** O agente Frontend reservou `frontend/**`, mantém mudanças modificadas/não rastreadas e não fez stage/commit. Build aprovado (2.045 módulos, aviso não fatal de bundle 500,83 kB) e teste isolado `node tests/favorites.mjs` completo aprovado; 36 capturas `favorites-*` em `.impeccable/review/`. `npm test`/live e seis demais módulos da árvore atual não foram executados/validados nesta etapa: autorização foi interrompida pelo pedido de encerramento. Não declarar interface de favoritos concluída nem incluir WIP no commit backend. Os documentos compartilhados foram liberados para este checkpoint, preservando registros anteriores.

Na próxima sessão, conferir `git status` e ler a entrada mais recente do log, combinar com Frontend via Maestri e executar `npm test` em `frontend` (sete módulos, API/SQLite temporários). Enviar falhas com stack ao agente, repetir casos afetados após correção e revisar capturas simuladas/reais nos dois temas/1440/390/320 px. Validar favoritos de música/livro, filtros/remoção/isolamento e retorno do login sem autosave. Só então documentar e fazer commit frontend seletivo/local. Não alterar visual, chaves/cotas/modo ou servidores existentes incidentalmente. Migração 0008 obrigatória no banco correto; `local.py` aplica automaticamente. Sem push, sem histórico automático. Nenhuma tarefa nova foi iniciada após o encerramento.

## Cache compartilhado de origens e explicações — backend validado

Schema `0007_recommendation_results` entregue pelo agente de banco em `54e13c2`; frontend de playlists em `d2359c2`. Backend agora usa o banco como cache único dos resultados públicos: snapshots de identidade/itens/resumo, sem consulta/intenção/conta. Origem para salvar e explicações sobrevivem a reinício/troca de instância durante o TTL de 3.600 segundos; limite global de 256, sem renovação ao consultar. Expiração/evicção retorna 404; banco configurado indisponível/desatualizado retorna 503, sem fallback de memória. Sem banco configurado, fluxos públicos mantêm o cache por processo. [ADR-0015](adr/0015-shared-recommendation-cache.md) registra limites e concorrência.

302 testes backend, Ruff/formatação e gates v7 K=5/10 aprovados, sem mudanças/regressões; sete testes novos cobrem inclusive três processos SQLite concorrentes e duas aplicações salvando/explicando a mesma origem. Compatibilidade online sem banco revalidada (43 testes). Build e seis módulos frontend aprovados com API/SQLite temporários, incluindo duas contas e revogação; visual aprovado preservado pelo agente frontend.

Antes de iniciar o backend atualizado em um banco existente, aplicar `alembic upgrade head` no banco correto; `local.py` aplica automaticamente. Não ampliar chaves/cotas nem mudar o modo online do usuário incidentalmente. Validar PostgreSQL real/migrações/concorrência com instância descartável antes de fechar esse gate; SQL gerado não basta. CI hospedada, lock Python, mypy, histórico/favoritos com contrato próprio e avaliações online amplas continuam pendentes. Os três agentes estão conectados pelo Maestri (Maestro/backend, Frontend, Banco de Dados); combinar arquivos/documentos e serializar commits. Não fazer push.

## Playlists na interface — entrega validada

Salvamento da trilha completa, login/cadastro com retorno à trilha e seus controles, lista paginada em `/account`, detalhe em `/account/playlists/:id` e exclusão com confirmação implementados. Cliente tipado reutiliza sessão/refresh em memória, cancela requisições privadas ao sair/trocar de conta e trata falhas e origem expirada. Endpoints existentes preservados; schema paralelo `0007` está no commit `54e13c2`, e integração backend/cache pertence à entrega separada do Maestro.

Build e todos os módulos da suíte frontend aprovados: smoke, componentes, auth, continuação, playlists e E2E com API real/SQLite temporário. Duas contas validaram isolamento GET/DELETE 404, persistência das mesmas 11 faixas após logout/troca, exclusão e refresh revogado com 401. Esperas de rotas, dados, logout e foco corrigidas nos testes, sem enfraquecer asserções. 24 capturas de salvar/lista/detalhe/confirmação em 1440/390/320 px nos dois temas revisadas; reviewer retornou `ship` no escopo visual/código. O sistema visual aprovado foi preservado; sidecar desatualizado preexistente não foi reparado incidentalmente. Validação/commit coordenados pelo Maestri com Maestro porque subprocessos/escrita Git estão bloqueados no terminal frontend.

Próximo passo: após o commit frontend, Maestro registra e commita separadamente seu cache compartilhado e libera os documentos. Depois, definir contrato/persistência de favoritos individuais e histórico por conta antes da integração de botões/listas na interface. Não reutilizar playlists como feedback, não inventar endpoints, não fazer push. Edição/exportação e PostgreSQL real permanecem pendentes. Validar também uma trilha online pela interface, sem alterar cotas/chaves e preservando os contratos de duração/fonte insuficiente. Os registros abaixo preservam o histórico anterior; suas instruções de integrar playlists já foram atendidas nesta entrega.

## Correção de trilhas reais e títulos em português

Leitura online agora exige a meta atendida apenas com durações conhecidas do MusicBrainz: faixas de 90 segundos a 10 minutos, até 60 faixas/quatro por artista; oito páginas de 50 candidatos por termo, até três termos. A IA ordena uma amostra sem limitar a quantidade. Falha/cota da IA continua por metadados. Sem músicas locais/estimativas para completar online; fonte insuficiente retorna `503 SOUNDTRACK_INCOMPLETE` e a interface apresenta erro. Offline mantém comportamento limitado anterior. Implementação isolada em `api/app/services/online_soundtrack.py`.

Busca Open Library usa `q`/`lang=pt`, com títulos/capas das edições portuguesas; descoberta filtra português. Alias verificado em `api/app/providers/portuguese_titles.py` resolve “Quem é você, Alasca?”/“Looking for Alaska” de John Green quando a edição não está indexada. Demais títulos sem edição portuguesa informada permanecem na língua da fonte. Alias não cria registros locais; conservar ID/autor reais e adicionar novos aliases somente com fonte editorial verificada. Cache externo versionado evita listas antigas em inglês.

293 testes backend, Ruff, build/suíte frontend e comparação estrita v7 K=5/10 aprovados. API online reiniciada na porta 8000, frontend 5173 preservado. Pedido exato do usuário: Alasca, Foco, instrumental, chuva/drama, 90 minutos → 20 faixas MusicBrainz, 5.517.572 ms (91 min 57 s), duração conhecida, IA ativa e sem degradação. Buscas reais por Alasca, Addie LaRue, O Problema dos Três Corpos e Devoradores de estrelas passaram. Este é um teste pontual, não garantia de disponibilidade futura. Evidência ignorada em `.impeccable/runtime/live-request-v2.json`.

Continuar pela integração de playlists na conta abaixo; validar consultas online variadas e afinidade musical sem ampliar cotas. Não reinstalar a versão anterior que aceitava 20 minutos como sucesso de um pedido de 90.

## Renovação de livros

“Ver outros livros” mantém o pedido enviado e exclui IDs já exibidos; conserva lista durante espera/erro/cancelamento/esgotamento. API de livros aceita `excluded_book_ids`/`offset`, informa `meta.has_more`/`next_offset`, e pagina Open Library com cache por página. Histórico somente na página atual, sem feedback persistente.

`playlist` informa meta/duração; o contrato online vigente está acima. Groq 429 respeita Retry-After curto uma vez por chamada e contabiliza cada tentativa. Salvamento por origem aceita até 60 faixas; manual continua 25.

Verificações estão na entrada mais recente do log. API online e frontend preservados nas portas 8000/5173. Reiniciar só a instância identificada e usar `start-local.ps1 -Online`; não alterar chaves/cotas.

Próxima entrega de produto continua sendo integração de playlists na conta, abaixo. Testar a renovação e trilhas de 90/120 minutos com consultas do usuário; falta de material suficiente agora gera erro no modo online.

## Instância online ativada a pedido do usuário

Sistema em execução para testes reais: interface `http://127.0.0.1:5173`, Swagger `http://127.0.0.1:8000/docs`. API offline anterior foi substituída por `local.py` com `GANDALF_ONLINE=1`; frontend existente preservado. `/system/status` confirma catálogo online e Groq `openai/gpt-oss-20b` configurado, limite existente de 50 chamadas/dia; readiness 200 com schema migrado. Logs ignorados em `.impeccable/runtime/online-api.*.log`.

Busca real de músicas (GoGo Penguin/MusicBrainz) e livros (Project Hail Mary/Open Library) passou. Descobertas musicais/literárias finais retornaram fontes externas com `ai_used=true`, `degraded=false`. Primeira tentativa teve fallback por indisponibilidade transitória; não confundir essas amostras com aprovação completa dos gates online. Catálogo local permanece como fallback/complemento. Ler a entrada mais recente do log.

Verificar processos/portas antes de retomar: este é um registro pontual, não garantia de que ainda estejam ativos. Para reiniciar preservando internet, usar `./start-local.ps1 -Online` após encerrar somente a instância identificada do projeto; o comando sem `-Online` volta ao modo offline. Chaves ficam em `api/.env`, sem exposição no frontend/Git. A próxima entrega de código continua sendo integrar playlists à interface, conforme abaixo.

## Atualização após persistir playlists na API

POST/GET/GET por ID/DELETE em `/api/v1/playlists` implementados com Bearer e filtro por proprietário. Criação manual aceita 1–25 IDs únicos do catálogo; origem aceita somente trilha de leitura pública ainda no cache do processo, inteira ou um subconjunto ordenado. Metadados/ordem ficam copiados em banco; duração real e estimada continuam distintas. Não há telas de playlists, favoritos, histórico ou edição nesta etapa.

Ler [contrato HTTP](05-API-Specification.md#7-playlists-playlists), [ADR-0014](adr/0014-owner-scoped-playlists.md) e a entrada mais recente do log. Migração `0006_playlists` é aplicada pelo iniciador local no próximo início; fora dele usar `alembic upgrade head` no banco correto. Conexões SQLite da aplicação agora habilitam FKs; testes cobrem isolamento, rollback, cascata e restrição de exclusão do catálogo. Origem efêmera não equivale a histórico pessoal nem tem proprietário; a playlist criada pertence exclusivamente à conta autenticada. Validação: 258 testes backend, Ruff/formatação, gate K=5/10 contra v7 sem mudanças/regressões, build e suíte frontend aprovados. Integração online testada com provedores simulados, sem chamadas adicionais ao salvar/consultar/excluir.

Próxima entrega de produto: integrar botão de salvar em `frontend/src/pages/ReadWithMusic.tsx`, gestão de playlists na conta (lista paginada/detalhe/exclusão) e cliente tipado. Usar sessão/refresh existentes, cancelar requisições ao sair ou trocar de conta, oferecer retry e tratar 401/404/503 e origem expirada. Testar com duas contas/API real/SQLite temporário e revisar estados responsivos nos dois temas, preservando o visual/animações aprovados. Favoritos de livros/músicas exigem um contrato próprio; não reutilizar playlists como feedback do ranking.

Servidores/dados locais preexistentes foram preservados; o E2E iniciou sua própria API migrada. Reiniciar a instância de desenvolvimento identificada antes de experimentar as novas rotas. PostgreSQL real, cache entre instâncias, revisão humana do ranking e CI hospedada permanecem pendentes. Fazer commits locais coerentes; não fazer push.

## Atualização após integrar autenticação na interface

Registro histórico da entrega anterior: o usuário confirmou autenticação como próxima entrega. Cadastro `/register`, login `/login`, dados da conta e logout `/account` agora usam os endpoints existentes. Sessão somente em memória conforme ADR-0006; navegar entre rotas preserva acesso, reload/fechamento exige login. Refresh rotativo compartilhado, logout aguarda rotação e revoga o token ativo; erros de rede permitem retry. Os três fluxos públicos permanecem acessíveis sem conta.

Build, suíte frontend (smoke/componentes/auth/E2E com cadastro e revogação reais), 220 testes backend e Ruff/formatação aprovados. Capturas `auth-*` em `.impeccable/review/` cobrem 1440/390/320 px nos dois temas; dados fictícios e SQLite temporário. Servidores locais existentes preservados. Não há histórico, salvos, playlists persistentes, recuperação de senha ou edição de conta nesta entrega. Ler a entrada mais recente do log; próximo passo de produto: desenhar contratos e persistência de playlists/salvos antes de ligá-los à conta. CI foi preservada no commit separado `ccffe39`; execução hospedada ainda pendente e nenhum push autorizado.

## Atualização após preparar a CI

Workflow inicial em `.github/workflows/ci.yml`: API/Ruff/pytest, comparação estrita K=5/10 contra v7 e build/E2E dos três fluxos. Actionlint, 220 testes da API, gates locais, build e suíte frontend aprovados. Corrigida somente a espera do teste responsivo, com autorização do usuário; esta etapa não altera componentes, estilos ou animações. Execução hospedada ainda pendente, sem push automático. Ler [CI.md](CI.md) e a entrada mais recente do log para continuar. A integração de interface foi concluída separadamente em `beb7569`; novas alterações de autenticação do outro terminal foram preservadas fora desta etapa.

## Atualização após a integração de UI

Accordion/Toggle Group/Skeleton foram concluídos após o commit backend `f120676`, com dependências, explicações compartilhadas, testes, créditos e revisão desktop/mobile nos dois temas. As referências abaixo a frontend pausado são históricas. A partir daqui, ler a entrada mais recente de `docs/DEVELOPMENT_LOG.md` e [HANDOFF_MAESTRI.md](HANDOFF_MAESTRI.md); não repetir o script de integração.

## Atualização após concluir piano/detetive

A etapa `local-rules-v7` foi validada nesta continuação. O checkpoint abaixo é histórico: suas pendências de piano/detetive, falha de versão e formatação já foram resolvidas. Leia a entrada mais recente de `DEVELOPMENT_LOG.md` e a matriz atual antes de seguir instruções antigas.

- Fontes e limites formalizados em `docs/catalog-metadata.md`; sete obras com piano e um livro de detetive, sem mudar itens/IDs. Saman continua sem nova etiqueta.
- 220 testes da API, Ruff e formatação aprovados. Relatórios `local-v7-piano-detective-k5.json` e `local-v7-piano-detective-k10.json` em `docs/eval-reports/` com gate estrito contra v6: zero perdas agregadas ou por consulta. Apenas b03/m06 mudam; corpus/julgamentos preservados.
- Build, smoke e E2E passaram usando uma cópia isolada da interface aprovada do commit `3732389` com o backend atual. Capturas desktop/mobile foram inspecionadas; o visual e animações aprovados permanecem a referência.
- Existem alterações frontend de outro terminal em andamento na árvore de trabalho, além de documentação local não versionada (`docs/HANDOFF_MAESTRI.md`). Elas foram preservadas e excluídas do commit v7. O estado continua mudando: o frontend da árvore de trabalho não foi validado por esses testes. Conferir Git/dependências/testes e ler o handoff local, se presente, antes de retomá-lo.
- Instâncias existentes em 8000/5173 preservadas; API local confirmou v7/readiness e consultas de piano/detetive com exclusões. O E2E iniciou uma nova instância isolada com SQLite temporário. Não encerrar processos sem identificar sua origem.

### Próxima instrução

> Leia a entrada mais recente de `docs/DEVELOPMENT_LOG.md` e `docs/IMPLEMENTATION_STATUS.md`. Piano/detetive v7 já está validado; use seus relatórios como baseline. Confira alterações locais e `docs/HANDOFF_MAESTRI.md`, se presente, antes de retomar componentes pausados da interface. Preserve o visual/animações aprovados. Para o ranking, obter revisão humana, conjunto reservado e evidência por obra antes de ampliar metadados. Gates online, PostgreSQL/pgvector e CI seguem abertos. Documente, teste e faça commits locais coerentes; não faça push.

## Checkpoint anterior (histórico)

Este documento transfere o contexto para outro terminal. Foi conferido no repositório em `C:\Users\vinic\Documents\Gandalf`, branch `main`, a partir do commit `39a7395`. O pedido desta sessão foi registrar o estado, sem continuar a implementação incompleta.

## Instrução pronta para o próximo terminal

> Continue o desenvolvimento do Gandalf. Leia primeiro `docs/CONTINUATION.md`, a entrada mais recente de `docs/DEVELOPMENT_LOG.md` e `docs/IMPLEMENTATION_STATUS.md`. Preserve o visual aprovado e suas animações. Conclua a etapa incompleta de piano/detetive do commit `39a7395`, documente as fontes, teste e compare com v6 antes de aceitar v7. Siga as regras de commits locais e documentação; não faça push. Confira o Git e os processos locais antes de alterar qualquer coisa.

## Direção combinada com o usuário

- Desenvolver em unidades coerentes, validar, atualizar `docs/DEVELOPMENT_LOG.md` e fazer commits locais explicativos. Não enviar ao remoto sem pedido explícito.
- O usuário escolheu **“Descoberta imersiva, com capas e movimento discreto”**, aprovou a composição corrigida e pediu animações nos conteúdos. Preservar essa aprovação.
- Manter os três fluxos: música, livros e trilha de leitura. O modo local deve continuar disponível sem serviço pago.
- Mensagens e documentação em português. As especificações numeradas incluem funcionalidades futuras; não confundir o roadmap com o que já funciona.
- O usuário tentou ajustar o agente para `gpt-6-astra medium` por último. Essa escolha pertence ao terminal/aplicativo; não foi confirmada como alteração desta sessão nem exige mudança no projeto.

## O que foi entregue

| Commit | Entrega |
|---|---|
| `837ab84` | CALM desempata por atmosfera, preservando relevância; ranking v4 e avaliação offline. |
| `1f15778` | CINEMATIC considera diversidade de artistas e etiqueta cinematográfica; ranking v5. |
| `5b40091` | Repaginação aprovada, capas, carrossel, escolhas animadas e animações acessíveis. |
| `2feacf6` | Comparação de avaliações por consulta, deltas e gate estrito opcional. |
| `b698eb3` | Livros favorecem gêneros explicitamente pedidos em empates; ranking v6, última etapa integralmente validada. |
| `39a7395` | Salvamento da etapa **incompleta** de piano/detetive; código declara v7, mas ainda não é uma entrega validada. |

O diretório de trabalho estava limpo antes deste registro. As alterações de v7 já estão no último commit, não apenas em arquivos pendentes. Preservar esse histórico.

### Interface concluída

- Home com busca e carrossel de capas, sugestões acionáveis e convite para ler com música; temas claro/escuro e identidade ametista.
- Componentes adaptados de Animated Tabs (Chetan Verma) e 3D Carousel (Cult UI), disponíveis no 21st.dev. A CLI exigia autenticação; foram usadas fontes públicas com licença MIT.
- Animações com Motion: entradas discretas, transições e feedback de interação; respeitam movimento reduzido e não avançam o carrossel automaticamente.
- Fontes Manrope/Newsreader e capas locais. Capas de apoio em resultados se aplicam apenas ao provedor local, evitando homônimos externos.
- Créditos e limites em `frontend/THIRD_PARTY_NOTICES.md`; licenças em `frontend/public/licenses/`. As capas não são cobertas pelas licenças MIT dos componentes.
- Arquivos de referência: `frontend/src/pages/Home.tsx`, `frontend/src/pages/Discovery.tsx`, `frontend/src/components/ui/`, `frontend/src/lib/showcase.ts`, `frontend/src/showcase.css`, `PRODUCT.md` e `DESIGN.md`.
- Smoke/E2E e build passaram na entrega visual. Houve revisão visual direta em desktop/mobile e tema claro. A revisão por subagente não concluiu por limite de uso; não existe parecer independente aprovado.

### Backend já disponível

FastAPI/SQLAlchemy, migrações, autenticação JWT com refresh rotativo, catálogo local de 18 livros e 25 músicas, filtros/exclusões/referências, explicações e cinco modos de leitura. Open Library, MusicBrainz e Groq são integrações online experimentais, opcionais. A interface ainda não tem login, histórico, salvos, feedback ou perfil. Não há reprodução de áudio, exportação Spotify nem deploy público.

O corpus offline contém 45 consultas. Os baselines v3–v6 estão em `docs/eval-reports/`. A comparação por caso fica em `api/app/evaluation/runner.py`; `--fail-on-case-regression` detecta perdas individuais que médias podem esconder. O experimento v5 possui perdas individuais históricas registradas: não apagar nem reclassificar esse histórico como ausência total de perdas.

## Etapa incompleta: piano e detetive

O commit `39a7395` altera somente estes três arquivos:

| Arquivo | Alteração já salva |
|---|---|
| `api/app/providers/local_catalog.py` | Etiqueta `detetive` em O Cão dos Baskervilles e `piano` em sete músicas existentes; sem novos itens/IDs. O comentário aponta para `docs/catalog-metadata.md`, que **ainda não existe**. |
| `api/app/services/recommendation_service.py` | Versão `local-rules-v7`, reconhecimento de piano e detetive; detetive deixa de ser apenas um alias de mistério e integra os gêneros explícitos de livros. |
| `api/app/services/online_recommendations.py` | Traduções `piano` e `detective fiction` para os novos termos no fallback online. |

As sete obras marcadas são Gymnopédie No. 1, Clair de lune, Spiegel im Spiegel, Ambre, Avril 14th, River Flows in You e Comptine d'un autre été, l'après-midi. Saman permanece sem essa etiqueta: não foi obtida evidência específica suficiente para a faixa. A cobertura é parcial. Piano descreve uma obra/edição com piano, não garante piano solo nem a instrumentação de toda gravação que um link de busca possa abrir.

### Fontes pesquisadas na sessão anterior

Referências de trabalho para concluir `docs/catalog-metadata.md`; consulta anterior em 2026-09-30. Não foram reabertas nesta sessão de transferência. Registrar a evidência específica de cada etiqueta e seus limites antes de aceitar a etapa.

| Obra | Fonte e evidência disponível |
|---|---|
| Gymnopédie No. 1 | [Alfred — Satie: 3 Gymnopédies & 3 Gnossiennes](https://www.alfred.com/products/satie-3-gymnopedies-3-gnossiennes-00-2501), edição para piano. |
| Clair de lune | [Henle HN 391](https://www.henle.de/Clair-de-lune/HN-391), piano solo, Claude Debussy. |
| Ambre | [Faber Music](https://www.fabermusic.com/shop/ambre-d50458), piano solo, Nils Frahm, coleção Sheets Eins. |
| Avril 14th | [Faber Music](https://www.fabermusic.com/shop/avril-14th-d44637), edição para piano solo, Aphex Twin. |
| Comptine d'un autre été, l'après-midi | [Hal Leonard — Contemporary Piano Masters](https://www.halleonard.com/product-family/PC28241/contemporary-piano-masters-2nd-edition), obra listada na coleção para piano. |
| River Flows in You | [Catálogo Hal Leonard em PDF](https://www.halleonard.com/bin/PromoEducationalKeyboardFall40offpno2012.pdf), resultado pesquisado identifica piano e Yiruma; conferir a passagem no PDF ao formalizar a proveniência. |
| Spiegel im Spiegel | [Catálogo Universal Edition em PDF](https://www.universaledition.com/media/f4/97/a0/1751447474/Paert_Jubilaeumskatalog_Webversion.pdf), contém versões com piano; localizar a versão/página exata. Existem outros arranjos, inclusive sem piano. |
| O Cão dos Baskervilles | [Penguin](https://www.penguin.co.uk/books/34513/the-hound-of-the-baskervilles-by-doyle-arthur-conan/9780241455296), sinopse de investigação por Holmes e Watson. |

### Avaliação preliminar existente

Os arquivos locais `.impeccable/evaluation-v7-k5.json` e `.impeccable/evaluation-v7-k10.json` foram conferidos nesta sessão. São artefatos ignorados pelo Git: podem não existir em outro checkout e devem ser regenerados antes da aceitação.

- Ambos comparam v7 contra v6, sinalizam mudança de catálogo e registram zero regressões agregadas ou por consulta.
- Apenas `b03` (mistério de detetive) e `m06` (piano acolhedor) mudaram.
- `b03`: nDCG passa de aproximadamente 0,5261 para 1,0 em K=5/10.
- `m06`: P@5 passa de 0,8 para 1,0; P@10 de 0,5 para 0,6. nDCG também melhora.
- Isso não substitui testes novos, revisão humana ou conjunto reservado. Não alterar julgamentos do corpus para favorecer o experimento.

## Verificação feita em 2026-10-01

| Verificação | Resultado |
|---|---|
| API: `python -m pytest -q --tb=short` | **191 passaram, 1 falhou**: `tests/test_books.py::test_health_version_and_readiness_are_honest` ainda espera `local-rules-v6`, mas o código retorna v7. |
| Ruff check | Aprovado. |
| Ruff format --check | Pendente: `api/app/providers/local_catalog.py` precisa ser formatado; outros 60 arquivos aprovados. |
| Frontend | Última validação aprovada na entrega visual; não reexecutada nesta sessão, que apenas registra continuidade. |
| HTTP da interface | `http://127.0.0.1:5173/` respondeu 200. |
| API | `/version` retornou `local-rules-v7`; `/health/ready` retornou banco/schema `ok` e pgvector `not_required`. |

A primeira execução do pytest sofreu bloqueio de acesso aos temporários do Windows. Repetida com permissão adequada, resultou nos 191 testes aprovados e uma falha acima; os 49 erros iniciais de setup eram ambientais. Permanece um aviso de depreciação Starlette/httpx. Nenhum código foi corrigido nesta sessão de documentação.

## Como retomar

1. Conferir `git status`, últimos commits e estes documentos. Não reimplementar o visual aprovado nem tratar v7 como concluído.
2. Concluir a proveniência em `docs/catalog-metadata.md`, distinguindo etiquetas editoriais e informações sustentadas pelas fontes.
3. Acrescentar testes de interpretação/negação de piano e detetive, exclusões, referências e fallback online com IA indisponível. Atualizar a expectativa de versão somente junto da validação da etapa. Formatar o catálogo.
4. Executar a suíte e comparar v7 contra v6 em K=5/10 com gate estrito. Preservar corpus e relatórios anteriores. Se aprovado, versionar novos relatórios e acrescentá-los à proteção de regressão em `api/tests/test_evaluation.py`.
5. Atualizar `api/README.md`, `docs/05-API-Specification.md`, `docs/IMPLEMENTATION_STATUS.md` e `docs/DEVELOPMENT_LOG.md`, indicando resultados e limitações reais. Os README da raiz/API têm trechos antigos com `??` e afirmações desatualizadas; a revisão completa pode ser uma etapa documental separada.
6. Revisar o diff, adicionar apenas arquivos relacionados e fazer commit local convencional com resumo e corpo explicativos. Não fazer push.
7. Após mudanças no backend, reiniciar a instância local e verificar versão/readiness e consultas de exemplo. O backend iniciado por `local.py` não tem recarga automática.
8. Prosseguir pelos gates da matriz e `docs/12-development-roadmap.md`: revisão humana, avaliação online, cobertura/termos dos provedores, PostgreSQL/pgvector e CI continuam pendentes. Não concluir esses gates apenas pelos testes offline.

### Comandos de validação

Executar a partir da raiz, mudando para a pasta indicada:

```powershell
Set-Location api
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\python.exe -m ruff check app local.py alembic tests
.\.venv\Scripts\python.exe -m ruff format --check app local.py alembic tests
.\.venv\Scripts\python.exe -m app.evaluation.runner --k 5 --baseline ../docs/eval-reports/local-v6-genres-k5.json --fail-on-case-regression
.\.venv\Scripts\python.exe -m app.evaluation.runner --k 10 --baseline ../docs/eval-reports/local-v6-genres-k10.json --fail-on-case-regression
Set-Location ../frontend
npm.cmd test
npm.cmd run build
Set-Location ..
```

### Execução local

A interface e API estavam disponíveis por volta das 07h00 de 2026-10-01, horário de São Paulo. Esse é um registro pontual; verificar novamente no novo terminal. Identificadores de sessões de ferramentas do chat anterior não são portáveis.

Na raiz, `./start-local.ps1` inicia API e Vite; `-Install` instala dependências se necessário. O padrão é offline. Swagger em `http://127.0.0.1:8000/docs`. Não iniciar outra cópia enquanto as portas 8000/5173 estiverem ocupadas; identificar os processos antes de encerrá-los. Ctrl+C no terminal supervisor encerra sua instância. Não apagar `api/.local`, que contém banco e segredo locais, nem versionar esses dados ou `.env`.

Arquivos `.impeccable/review/` contêm capturas e revisão local, se ainda presentes. A pasta é ignorada, mas `.impeccable/design.json` já é rastreado. Dependências estão em `api/.venv` e `frontend/node_modules`; não são parte do Git.
