# Registro de desenvolvimento

## 2026-10-02 — Fontes online e capa externa verificadas

### Implementado
- Backend validou fontes públicas Open Library/MusicBrainz e interpretação Groq com o cliente real da aplicação. API BOOK entregou três obras externas em português com IA ativa/sem degradação.
- API MUSIC/re-roll devolveu dois lotes locais, seis UUIDs únicos, cursor 0→15→30 e IA ativa/sem degradação. Consulta adicional de jazz retornou vazia; seleção musical externa continua pendente, sem perseguir novas queries.
- Replay offline restrito aos hashes/dados públicos dessa consulta encontrou 15 gravações MusicBrainz + três candidatos locais, mas Selection da IA com zero escolhas. Não houve rejeições por filtros/score/diversidade; motivo da omissão não consta no schema. Zero rede/reserva/escrita no replay, sem bug API demonstrado.
- Capa “O Hobbit” real respondeu200/JPEG25.626bytes/180×285. Maestro confirmou uma única GET externa no Chromium e imagem visível em 390 px, usando API simulada com metadados públicos reais; zero erros/requests inesperados e nenhuma LLM nessa verificação.
- Banco preparou receita/harness PostgreSQL descartável, sem executar integração nem alterar o servidor existente. Fix de mensagem frontend já registrado em `949f642`.

### Arquivos principais alterados
- `docs/backend-online-session-2026-10-02.md`, `docs/database-postgres-session-2026-10-02.md`
- `docs/DEVELOPMENT_LOG.md`, `docs/CONTINUATION.md`, `docs/IMPLEMENTATION_STATUS.md`

### Decisões técnicas
- Probe inicial HTTPX padrão/certifi falhou issuer20; não representava o cliente da aplicação, que já usa `ssl.create_default_context()`/raízes do sistema. Rodada corrigida passou com TLS validado; sem patch, nova chave ou mudança de modelo/provider/cota. Contextos explícitos são documentados por [HTTPX](https://www.python-httpx.org/advanced/ssl/) e [Python SSL](https://docs.python.org/3.12/library/ssl.html#ssl.create_default_context).
- `ai_used`/`sources` das respostas efetivas distinguem ordenação por IA de itens externos; fonte200 direta ou cache agregado não prova seleção externa. Limites por rodada e consumo registrados, sem retries manuais.
- Harness PG permanece ignorado até execução real. Fixtures existentes são SQLite e teste PG só gera SQL: DATABASE_URL não converte a suíte. Não integrar CI como gate verde antes de executar instância descartável.

### Estado atual
- Uso Groq **2→9/50** na etapa; modelo original, configurações/dados/processos preservados, nenhuma evidência de chave inválida. API PID31444/8000 e frontend existente localhost:5173 mantidos, status/readiness200 e build de 2.050 módulos PASS.
- BOOK externo/IA, interpretação real e uma capa externa/componente comprovados pontualmente; re-roll MUSIC comprovado com seleção local. Não afirmar aprovação ampla de ranking musical, trilha, todas as capas ou PostgreSQL.
- Docker indisponível normal/elevado; PG18/5432 e volume persistente não tocados. Guard/import/13 recusas do harness passaram sem conexão; gate real continua pendente.

### Próximos passos
- Priorizar qualidade da seleção MUSIC: funil Jazz já diagnosticado offline (18 candidatos/zero escolhas da IA). Avaliar informação disponível no payload/voz/energia e amostras públicas antes de mudar prompt/fallback; futura validação externa precisa de orçamento próprio, preservando restrições e IDs reais.
- Validar re-roll BOOK externo e ampliar amostras/revisão humana sem ampliar cotas incidentalmente. Seguir receita Banco para PostgreSQL descartável quando ambiente estiver acessível.
- Consolidar commit documental seletivo e conferir Git limpo/serviços preservados, sem push. Evidências ignoradas e limites estão nos relatórios de sessão; não tratá-las como artefatos disponíveis em outro checkout.

## 2026-10-02 — Aviso claro para renovação limitada

### Implementado
- Re-roll MUSIC/BOOK vazio e degradado informa a limitação da tentativa, a preservação da seleção anterior e a possibilidade de tentar novamente. Retry/esgotamento sem degradação mantêm mensagens próprias.
- Regressões verificam variantes com/sem hint/has_more, snapshot pelo login, seleção/metadados anteriores e pedido/filtros/IDs/cursor preservados. Servidor do teste usa porta efêmera real, sem ocupar o frontend existente.

### Arquivos principais alterados
- `frontend/src/pages/Discovery.tsx`, `frontend/tests/reroll.mjs`
- `docs/frontend-online-session-2026-10-02.md`, `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- `degraded` pode limitar apenas uma etapa/fonte; não afirmar indisponibilidade de todas as fontes ou da IA. Hint anterior continua descrevendo a seleção preservada.
- Auditoria dos três fluxos com fixtures, skills impeccable/taste e correção restrita ao problema reproduzido. Sem alteração de contrato, estado, dependências ou quotas.

### Estado atual
- Frontend aprovou módulo reroll completo afetado, TypeScript, detector e 14 capturas dark/light em 1440/390/320, movimento reduzido/normal; zero erros de runtime. Maestro revisou capturas mobile e aprovou build final de 2.050 módulos (aviso não fatal de bundle 503,12 kB).
- Sem duplicar suíte geral ou chamadas externas no Frontend/Maestro. Backend conduz validação online limitada; seus resultados e o gate PostgreSQL são evidências separadas deste fix.

### Próximos passos
- Serializar commit local desta unidade e consolidar evidências Backend/Banco nos documentos de continuidade, distinguindo fontes externas de complemento local.
- PostgreSQL/pgvector real ainda requer instância descartável; não usar o servidor/volume existente nem considerar fixtures como aprovação desse gate.

## 2026-10-02 — Retomada da validação online coordenada

### Implementado
- Usuário solicitou continuar o desenvolvimento; checkpoint `ffdd6a6` e árvore limpa conferidos. Terminais Backend/Frontend/Banco existentes receberam escopos separados via Maestri; Maestro reserva Git e os três documentos compartilhados.
- Backend valida transporte com uma consulta pública por fonte e, somente se fontes responderem, uma interpretação Groq dentro da cota existente. Frontend audita degradação dos três fluxos por fixtures, sem chamadas reais de recomendação. Banco verifica gate PostgreSQL e prepara harness/receita se Docker indisponível.

### Arquivos principais alterados
- `docs/DEVELOPMENT_LOG.md`
- Relatórios exclusivos previstos: `docs/backend-online-session-2026-10-02.md`, `docs/frontend-online-session-2026-10-02.md`, `docs/database-postgres-session-2026-10-02.md`.

### Decisões técnicas
- Uma única origem de probes externos/LLM: Backend. Não duplicar chamadas, suites gerais ou processos; manter configuração/modelo/chave/cota e snapshots.
- Banco confirmou Docker indisponível também elevado. Harness PostgreSQL permanece ignorado até execução real; sem container/pull/instalação ou alteração do PostgreSQL18 existente.

### Estado atual
- Etapa em andamento, sem nova funcionalidade declarada concluída. Gates anteriores de código/testes permanecem registrados nas entradas abaixo.
- Backend/Frontend iniciaram diagnóstico e auditoria; correções relevantes serão autorizadas por escopo, testadas, documentadas e commitadas localmente pelo Maestro. Nenhum push.

### Próximos passos
- Receber evidência de transporte e uma proposta concreta de resiliência UX; implementar apenas escopo que resolva defeito reproduzido.
- Revisar receita/harness PostgreSQL e limitações, validar alterações específicas e consolidar documentos/commits da nova etapa.

## 2026-10-02 — Checkpoint final de commits e serviços

### Implementado
- Todas as unidades liberadas pelos terminais Backend/Frontend/Banco revisadas e registradas em commits locais seletivos, incluindo documentação por etapa. Nenhum push.
- Consolidado estado final em CONTINUATION/IMPLEMENTATION_STATUS, distinguindo evidência atual de checkpoints históricos e validação local/fixtures de provedores externos.

### Arquivos principais alterados
- `docs/DEVELOPMENT_LOG.md`, `docs/CONTINUATION.md`, `docs/IMPLEMENTATION_STATUS.md`

### Decisões técnicas
- Commits da entrega: `318d97a` favoritos backend; `f2adc7c` re-roll backend; `1663c2c` auditoria Banco; `ef0c284` normalizador de capas; `137d492` integração frontend; `03a51e9` capas/responsividade frontend. Consolidação documental em commit próprio; nenhum snapshot/artefato ignorado incluído.
- Usado snapshot pré-capas para separar hunks sobrepostos sem descartar WIP. Testes repetidos apenas nos fluxos afetados após correções; módulo covers aprovado pelo Frontend sem duplicação no Maestro.

### Estado atual
- Backend: 366 testes integrais aprovados antes do fix isolado de capas; 38 testes de livros/capas após fix, Ruff/formato84 e gates v7 K=5/10 aprovados. Frontend: dez módulos aprovados em rodadas coordenadas; rodada final continuation/favorites/live com API real/SQLite/duas contas/temas/mobile e build2050 PASS. Capturas atuais revisadas; covers60, sem erros de runtime. Não houve nova execução monolítica de npm test após os fixes.
- Runtime carregado: única API online `127.0.0.1:8000`, PID31444/launcher39748, mesmo banco/config, status/readiness200. API antiga37452/sessão27472 encerrada por Ctrl+C após identidade confirmada; nenhuma alteração de chave/modelo/limite ou dados no restart.
- Frontend existente `http://localhost:5173`, IPv6 `::1`, PID25716/Vite do Gandalf; GET página e módulo BookCover200, guard1×1/rastreamento de falha servidos. Bind IPv6 explica recusa em 127.0.0.1; nenhum servidor persistente duplicado.
- Capas locais verificadas, inclusive Duna no E2E real/SQLite isolado. Capas/fontes externas atuais e LLM real não comprovados, por falha de transporte nas consultas; Groq original configurado, cota RO observada2/50, sem evidência de chave inválida. PostgreSQL/pgvector real continua pendente.

### Próximos passos
- Conferir Git/processos ao retomar; manter modo online, configuração/cota e snapshots existentes.
- Com transporte acessível, validar uma obra/edição PT/capa real e uma interpretação/recomendação externa limitada; registrar fonte/ai_used/degraded e avisar usuário antes de trocar API/chave/modelo.
- Retomar PostgreSQL/pgvector em instância descartável com contexto próprio; não instalar/alterar o servidor existente incidentalmente. Comandos/evidências nos seis relatórios de sessão/capas em `docs/`.

## 2026-10-02 — Capas consistentes nos fluxos de livros

### Implementado
- `BookCover` compartilhado por descoberta, favoritos e lista/livro selecionado de Ler com Música. Corrigida ausência da capa local no seletor; URL de metadados tem prioridade e asset por título exige `provider=local`.
- Erro de carregamento e imagem branca 1×1 usam placeholder; falha vinculada à URL permite carregar uma fonte diferente no mesmo componente montado, sem loops de retry.
- Corrigida sobreposição de Cinematográfica/Calma em 320 px com quebra do texto dentro do cartão, preservando fonte/tamanho; regressão mede retângulos de cada linha, além do overflow da página.

### Arquivos principais alterados
- `frontend/src/components/BookCover.tsx`, `frontend/src/lib/showcase.ts`, `frontend/src/pages/Discovery.tsx`, `frontend/src/pages/Favorites.tsx`, `frontend/src/pages/ReadWithMusic.tsx`, `frontend/src/styles.css`
- `frontend/tests/covers.mjs`, `frontend/tests/fixtures/book-cover.tsx`, `frontend/package.json`, `frontend/README.md`
- `docs/frontend-covers-session-2026-10-02.md`, `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Preservar identidade/título/autoria e snapshots. Nenhum enriquecimento/requisição adicional, novo asset/dependência ou reescrita de banco.
- Tratamento de capas separado do commit de integração `137d492`; nove módulos anteriores conservados, novo módulo `covers` e comando `test:covers`.

### Estado atual
- Frontend: **covers PASS**, 60 capturas em 1440/390/320, dark/light, movimento normal/reduzido; regressões de HTTP404, GIF200 1×1, troca de URL montada, prioridade de metadado e homônimo externo; zero erros de runtime.
- Maestro: **continuation/favorites/live PASS** após freeze; build **PASS**, 2.050 módulos. Capturas atuais revisadas, inclusive Duna visível na seleção do E2E com API real/SQLite temporário e cartão320 sem sobreposição.
- Home/assets locais já funcionavam antes do fix. Diagnóstico sobre catálogo online persistente pós-fix não confirmou Duna local; capa externa real/status/dimensões continua pendente. Diagnóstico inicial também chamou recommendations/books; leitura RO posterior observou **2/50** tentativas Groq, sem mudança de limite/chave/modelo.

### Próximos passos
- Consolidar commits/runtime/validações nos documentos de continuidade e verificar árvore Git limpa, sem push.
- Quando transporte estiver disponível, validar uma amostra externa real sem ampliar cotas ou reescrever snapshots; PostgreSQL/pgvector real continua gate separado.

## 2026-10-02 — Favoritos e renovação de sugestões na interface

### Implementado
- Favoritos individuais de música/livro/faixas de leitura: estado em lote, salvar/remover, coleção paginada/filtrada na conta e retorno do login sem salvar automaticamente.
- Renovação MUSIC/BOOK conserva pedido/filtros enviados, seleção durante espera/erro/cancelamento, vistos cumulativos e cursor; limite de 200 e retorno de autenticação preservados.
- Alert da fonte pública shadcn listado no 21st.dev e AnimatedContent React Bits adaptado para Motion, sem nova dependência, com créditos/licença e movimento reduzido. Skills impeccable/taste aplicadas pelo Frontend.
- Corrigido overflow320 de Favoritos: link dentro das ações não herda margem mobile de 89 px. Teste de foco usa Tab real e conserva asserção de outline visível.

### Arquivos principais alterados
- `frontend/src/App.tsx`, `frontend/src/main.tsx`, `frontend/src/pages/Account.tsx`, `frontend/src/pages/Authentication.tsx`
- `frontend/src/pages/Discovery.tsx`, `frontend/src/pages/ReadWithMusic.tsx`, `frontend/src/pages/Favorites.tsx`
- `frontend/src/components/FavoriteControls.tsx`, `frontend/src/lib/favorites.ts`, `frontend/src/favorites.css`
- `frontend/src/lib/discovery.ts`, `frontend/src/components/RerollControls.tsx`, `frontend/src/components/ui/alert.tsx`, `frontend/src/components/ui/animated-content.tsx`, `frontend/src/components/ui/components.css`
- `frontend/tests/discovery-state.mjs`, `frontend/tests/favorites.mjs`, `frontend/tests/reroll.mjs`, `frontend/tests/live.mjs`, `frontend/tests/playlists.mjs`
- `frontend/README.md`, `frontend/package.json`, `frontend/THIRD_PARTY_NOTICES.md`, `frontend/public/licenses/react-bits.txt`, `docs/frontend-session-2026-10-02.md`

### Decisões técnicas
- Integração frontend versionada como unidade coerente de favoritos/renovação/componentes, separada da correção de capas pelo snapshot pré-capas. Nenhuma dependência nova, histórico de vistos ou autosave.
- MCP21st autenticado não respondeu; componente veio da fonte pública oficial. Não afirmar consumo/cota ou recuperação autenticada atual.

### Estado atual
- Nove módulos anteriores/novos de estado e UI aprovados em rodadas coordenadas: primeira suíte passou helper/smoke/components/auth/continuation/playlists/favorites; reroll aprovado após ajuste de foco; rodada final **continuation/favorites/live aprovada**, API real/SQLite temporário/duas contas, filtros/remoção/isolamento e responsividade nos dois temas.
- Build final **PASS**, 2.050 módulos, aviso não fatal de bundle 502,97 kB. Capturas atuais de favoritos/re-roll revisadas pelo Maestro; títulos e erros visíveis. Teste novo de capas/60 capturas aprovado pelo Frontend e registrado na unidade seguinte, sem duplicação concorrente.
- Provedores/capas externas e PostgreSQL real continuam gates independentes pendentes; API online carregou patch de capas e status/readiness200 foram confirmados.

### Próximos passos
- Registrar unidade de capas frontend com BookCover, busca/selecionado de leitura e regressões de erro/1×1/troca de URL.
- Consolidar hashes, runtime e limitações nos documentos compartilhados; nenhuma alteração de chave/modelo/cota ou push automático.

## 2026-10-02 — Correção de capas na normalização Open Library

### Implementado
- Edição portuguesa só substitui a capa da obra quando `cover_i` é inteiro estrito positivo. IDs 0/-1 ou inválidos deixam de apagar a capa válida da obra; ausência verdadeira continua `null`.
- Novas URLs de capa incluem `?default=false`, permitindo 404 e fallback visual quando a imagem não existe, em vez de imagem branca HTTP 200.

### Arquivos principais alterados
- `api/app/providers/open_library.py`, `api/tests/test_book_covers.py`, `api/tests/test_books.py`
- `docs/backend-covers-session-2026-10-02.md`, `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Preservar UUID, título e autoria da edição escolhida; sem requisições extras por capa, mudanças de schema/TTL ou reescrita de catálogo/snapshots.
- Correção da interface e carregamento em runtime são etapas separadas deste commit do provedor.

### Estado atual
- Maestro: **38 testes de livros/capas aprovados**, 1 aviso já existente; Backend: Ruff e formato dos três arquivos aprovados. Suíte anterior de 366 testes permanece evidência de favoritos/re-roll.
- API existente PID 37452 ainda não carregou o patch. Consultas públicas falharam no transporte mesmo fora do sandbox e com `trust_env=False`; capa externa atual/status/dimensões ainda não comprovados. Nenhuma chamada LLM ou troca de chave/modelo/cota nesta correção.

### Próximos passos
- Backend carregar patch em uma única API após verificar identidade do processo/porta, preservando modo online, banco e configuração; verificar status/readiness locais.
- Frontend concluir tratamento de imagens ausentes, erro/1×1 e troca de URL; validar busca e livro selecionado em Ler com Música e registrar testes/QA.

## 2026-10-02 — Auditoria de persistência e capas legadas

### Implementado
- Banco revisou ownership, upsert e estabilidade de UUIDs das fontes reais; documentação do modelo agora reflete `DO UPDATE`/`RETURNING` e vistos efêmeros do re-roll, sem nova migração.
- Auditoria de capas somente leitura: 210 livros, 206 Open Library (32 sem capa), quatro locais (sem capa no JSON) e 174 URLs externas antigas sem `default=false`. Cinco caches BOOK estavam expirados; nenhum cache ativo ou divergência com catálogo demonstrado nesse snapshot.

### Arquivos principais alterados
- `docs/04-Data-Model.md`
- `docs/database-session-2026-10-02.md`, `docs/database-covers-session-2026-10-02.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Preservar IDs, snapshots salvos e TTL; sem expurgo, atualização em lote ou migração incidental. Metadados do catálogo podem ser atualizados pelo fluxo normal de busca com fonte acessível, mantendo identidade.
- Ausência de capa não comprova falha do provedor; imagens brancas HTTP 200 são um mecanismo possível. Correção do normalizador e fallback da interface são unidades próprias.

### Estado atual
- Backend de favoritos e re-roll registrado em `318d97a` e `f2adc7c`. Maestro aprovou os 366 testes, incluindo os três multiprocessos que a auditoria inicial não conseguiu executar no sandbox.
- PostgreSQL/pgvector real segue pendente: Docker sem daemon acessível; PostgreSQL 18 existente exige autenticação e extensão vector não foi encontrada nos diretórios examinados. Nenhum servidor/dado alterado.

### Próximos passos
- Concluir e validar correções de capas/overflow com Frontend e Backend, sem reescrever favoritos ou origens.
- Retomar gate PostgreSQL em instância descartável com pgvector disponível; testes SQLite e SQL compilado não substituem esse gate.

## 2026-10-02 — Renovação musical validada e favoritos versionados

### Implementado
- Backend de favoritos consolidado no commit local `318d97a`, com snapshot seletivo anterior ao re-roll; frontend, banco e renovação excluídos desse commit.
- Backend de renovação MUSIC/BOOK validado na suíte completa de 366 testes; contratos de UUIDs cumulativos, filtros, paginação limitada e disponibilidade após seleção preservados. Ruff83 e gates v7 K=5/10 sem regressões.
- Reteste frontend de renovação aprovado após substituir foco JavaScript por Tab real no teste, conservando asserções de elemento ativo e outline. E2E live encontrou overflow em Favoritos a 320 px no tema escuro, encaminhado ao Frontend; capas seguem investigação/correção própria.

### Arquivos principais alterados
- `api/app/schemas/recommendation.py`, `api/app/routes/recommendations.py`
- `api/app/services/recommendation_service.py`, `api/app/services/online_recommendations.py`, `api/tests/test_reroll.py`
- `api/README.md`, `docs/05-API-Specification.md`, `docs/adr/0017-ephemeral-discovery-reroll.md`, `docs/adr/README.md`
- `docs/backend-session-2026-10-02.md`, `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Vistos apenas no cliente; sem migração/histórico/feedback. Renovação de descoberta não altera duração ou seleção da trilha online.
- Commit da renovação separado de favoritos e da correção de capas; stage seletivo e nenhum push.

### Estado atual
- Backend de favoritos e renovação testado integralmente; commit local de renovação em preparação. A aprovação de frontend/live/QA é registrada separadamente.
- Identificado bug puro do normalizador de capas: ID inválido 0/-1 da edição pode apagar capa válida da obra. Backend/Frontend/Banco coordenam a correção, sem reescrever snapshots ou dados existentes.

### Próximos passos
- Concluir commit seletivo de renovação e enviar os hashes aos agentes.
- Finalizar live/QA e correção de capas com testes próprios; consolidar frontend e relatórios/documentos em commits locais separados.

## 2026-10-02 — Validação completa e retomada dos commits

### Implementado
- Usuário habilitou aprovações e autorizou retomar os três terminais, registrar commits locais e investigar capas de livros que não carregam. Escopos mantidos; Maestro reserva documentos compartilhados e Git.
- Suíte backend executada sem adaptações de fixtures fora do sandbox: **366 testes aprovados**, inclusive os três casos multiprocessos anteriormente bloqueados; 1 aviso Starlette/httpx, 74,80 s.
- Build frontend aprovado (2.049 módulos); aviso não fatal de bundle de 502,65 kB. Suíte frontend confirmou smoke, componentes, autenticação, continuação de livros, playlists e favoritos; re-roll musical encontrou uma falha de asserção de foco visível em `tests/reroll.mjs:81`, encaminhada ao Frontend. E2E live ainda não foi alcançado nessa rodada.

### Arquivos principais alterados
- `docs/DEVELOPMENT_LOG.md`
- Alterações funcionais de favoritos/re-roll e relatórios permanecem nas listas da entrada anterior; novos arquivos da correção de capas serão registrados depois da reprodução/validação.

### Decisões técnicas
- Executar testes/build com aprovação de execução fora do sandbox quando EPERM/TEMP/named pipe impedirem verificação, sem alterar código/asserções para aprovar artificialmente.
- Commit backend de favoritos usa snapshot seletivo pré-re-roll; alterações sobrepostas de README/Spec/índice ADR serão separadas do commit de renovação. Nenhum push.

### Estado atual
- Backend de favoritos/re-roll agora aprovado integralmente; commits locais em serialização pelo Maestro. Frontend aguarda correção/reteste de foco e execução live/QA atual.
- Capas em investigação read-only nos três terminais: URLs/provedor, estado da imagem no cliente e catálogo/cache/snapshots. Nenhuma migração/limpeza de dados ou troca de chave LLM autorizada incidentalmente.
- API online existente em 8000 preservada; frontend identificado em 5173. PostgreSQL/pgvector real continua gate independente pendente.

### Próximos passos
- Registrar commits backend separados com diff/stage seletivos, incluindo registros de progresso; enviar hashes aos agentes.
- Frontend corrigir causa da asserção de foco sem enfraquecê-la; Maestro executar re-roll e live, repetir somente os casos afetados após correções.
- Reproduzir e corrigir capas, testar trocas/falhas/fallbacks e links reais; revisar capturas atuais e consolidar os relatórios exclusivos de capas antes dos commits frontend/fix/documentação.

## 2026-10-02 — Re-roll musical e retomada online coordenada

### Implementado
- Consultados log, ponto de retomada, matriz de implementação e Git; preservados os WIPs de favoritos da sessão anterior. Terminais existentes Frontend, Backend e Banco de Dados coordenados por Maestri, sem recrutar duplicatas.
- Confirmado re-roll de livros já implementado na sessão anterior. Adicionado contrato musical `excluded_music_ids`/offset e metadados de continuação nos dois modos; corrigido `has_more` para não contar avisos/candidatos rejeitados como disponibilidade. Frontend implementa renovação nos dois tipos, sem repetir IDs, preservando pedido/filtros enviados, lista e estado de retorno do login.
- Frontend orientado a usar as skills `impeccable` e `design-taste-frontend`, API já configurada do 21st.dev e componentes React Bits, preservando a direção visual aprovada e acessibilidade.
- Revisão backend de favoritos sem novos bloqueadores, Ruff/check de formato aprovados (82 arquivos). TypeScript da árvore frontend e sintaxe dos testes favoritos/live aprovados pelo Maestro.
- Integrados Alert da fonte pública oficial shadcn (componente listado no 21st.dev) e AnimatedContent do React Bits adaptado para Motion existente, sem GSAP/dependências novas. Créditos e licença específica do React Bits preservados; validação visual atual permanece pendente.
- Auditoria de Banco concluída, com normalizadores UUID5 reais verificados sem rede e contrato documental de upsert corrigido para refletir `DO UPDATE`/`RETURNING`. Nenhuma migração nova.

### Arquivos principais alterados
- `docs/DEVELOPMENT_LOG.md`
- `docs/CONTINUATION.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `api/app/schemas/recommendation.py`, `api/app/routes/recommendations.py`, `api/app/services/recommendation_service.py`, `api/app/services/online_recommendations.py`, `api/tests/test_reroll.py`
- `frontend/src/pages/Discovery.tsx`, `frontend/src/lib/discovery.ts`, `frontend/src/components/RerollControls.tsx`, `frontend/src/components/ui/alert.tsx`, `frontend/src/components/ui/animated-content.tsx`, `frontend/src/components/ui/components.css`
- `frontend/THIRD_PARTY_NOTICES.md`, `frontend/public/licenses/react-bits.txt`
- `frontend/tests/discovery-state.mjs`, `frontend/tests/reroll.mjs`, `frontend/tests/favorites.mjs`, `frontend/package.json`
- `api/README.md`, `docs/05-API-Specification.md`, `docs/adr/0017-ephemeral-discovery-reroll.md`, `docs/adr/README.md`
- `docs/04-Data-Model.md`, `docs/backend-session-2026-10-02.md`, `docs/database-session-2026-10-02.md`, `docs/frontend-session-2026-10-02.md`

### Decisões técnicas
- Maestro reserva estes três documentos compartilhados e serializa commits; agentes mantêm registros exclusivos de sessão. API, frontend e modelos/migrações têm responsáveis separados.
- IDs já vistos no re-roll permanecem efêmeros no cliente, sem migração, histórico persistente ou efeito no ranking pessoal. Contrato musical deve espelhar livros e corrigir disponibilidade de continuação considerando filtros e limite de paginação.
- Nenhuma troca de chave/API/modelo LLM ou ampliação de cotas autorizada por inferência. Diagnóstico de indisponibilidade deve distinguir credenciais/provedor de bloqueios do sandbox; avisar o usuário se nova chave for necessária.

### Estado atual
- Suíte completa backend no Maestro: **361 aprovados/3 falhas de ambiente**, 1 aviso Starlette/httpx, 69,87 s; três casos falham em named pipe de `ProcessPoolExecutor` antes dos workers (dois favoritos, um cache). Não é aprovação integral. Subset de recomendações/re-roll do Backend: 185 aprovados; gates v7 K=5/10 sem mudanças/regressões. Dois casos extras adicionados depois da coleta integral e ajuste equivalente de literal/formato foram validados separadamente: `test_reroll.py` **20 aprovados**, Ruff/check de formato final **83 arquivos** aprovados.
- Permissões Windows impediram o TEMP padrão e diretórios `0700` do pytest. Runner ignorado `.impeccable/runtime/maestro_pytest_temp.py` substitui somente fixture `tmp_path` por diretórios comuns herdados no workspace com `-p no:tmpdir -p no:cacheprovider -p maestro_pytest_temp`; código e asserções preservados. Primeira tentativa do runner teve erro de teardown `_retention_policy` e foi corrigida; somente a rodada final sem esse erro é evidência. Favoritos isolados: 29 aprovados/2 bloqueados named pipe.
- Favoritos continuam sem commit. `npm test` inicial não iniciou casos: esbuild/Vite bloqueado por `spawn EPERM`. TypeScript atualizado passou novamente no Maestro; `node tests/discovery-state.mjs` passou para MUSIC/BOOK, filtros, offsets 0/300, deduplicação e limite 199+1/200, sem subprocessos. Sintaxe dos testes reroll/favoritos/live passou. Build/E2E visual atual não aprovado. Capturas de favoritos de 01/10 têm títulos/cores inconsistentes e exigem recaptura após fontes/animações estabilizarem; testes agora aguardam fontes/animações finitas. Suíte frontend preserva os sete módulos anteriores e acrescenta testes de estado/re-roll.
- `git add` seletivo dos dez arquivos backend de favoritos falhou ao criar `.git/index.lock` por permissão negada. `.git` somente leitura nesta sessão; nenhum commit novo nem push. Não contornar esse limite.
- API online iniciada pelo Backend (PID 37452, porta 8000), preservada. Maestro confirmou status/readiness 200, banco/schema saudáveis, Groq configurado no modelo existente `openai/gpt-oss-20b`; frontend ainda sem instância nova confirmada. MusicBrainz indisponível; “O Hobbit” veio de fallback local, não prova Open Library. Diagnóstico direto Open Library/MusicBrainz e única interpretação Groq falharam no transporte com conexão recusada, sem resposta HTTP. Cota Groq 0→1/50; nenhuma chave/API/modelo/cota alterados, sem evidência de credencial inválida.
- MCP autenticado 21st.dev indisponível no Frontend e Maestro durante `initialize` (`WinError 10061`); nenhuma recuperação autenticada ou cota atual confirmada. Alert usa fonte pública oficial, sem segredo no frontend/Git.
- Banco confirmou Docker daemon ausente, PostgreSQL 18 em 5432 exigindo senha e pgvector não encontrado nos diretórios verificados; gate PostgreSQL/pgvector real permanece aberto. Relatório de auditoria: 122 aprovados/3 bloqueados de ambiente; nenhum serviço/banco PostgreSQL existente alterado.

### Próximos passos
- Ler os três relatórios de sessão para separar unidades/arquivos. Snapshot seletivo de favoritos backend pré-re-roll está em `.impeccable/runtime/favorites-backend-20261002.patch` (ignorado); README/Spec/índice ADR contêm hunks das duas entregas e exigem revisão seletiva ao commitar.
- Em ambiente habilitado, reexecutar os três casos multiprocessos da suíte backend; fixtures online simuladas não fecham disponibilidade/afinidade das fontes reais. Retomar diagnóstico de transporte antes de cogitar troca de chave LLM.
- Em ambiente que permita subprocessos, executar build/`npm test` e QA responsiva dos dois temas, incluindo nova lista musical sem repetições e preservação de favoritos/login.
- Com escrita Git habilitada, revisar diff e fazer commits locais seletivos por unidade: favoritos backend, favoritos frontend, re-roll, componentes e documentação. Nenhum push automático; não marcar etapas bloqueadas como concluídas.

## 2026-10-01 — Backend de favoritos validado e encerramento do dia

### Implementado
- Coleção autenticada `/api/v1/users/me/favorites`: POST por origem/item UUID com snapshot do servidor (`201` novo/`200` existente), GET paginado/com filtro MUSIC/BOOK, POST `/status` em lote até 60 IDs únicos e DELETE idempotente `204` por proprietário.
- Favoritos independentes do catálogo/cache após salvar, sem feedback/ranking, playlist ou histórico automático. Repetição conserva primeiro ID/snapshot/proveniência/data; exige origem ainda válida.
- Correções apontadas em revisão independente: falha SQL ao validar conta agora retorna 503 genérico com rollback; upsert devolve o snapshot atomicamente, eliminando a consulta que podia perder a linha para DELETE concorrente no PostgreSQL.

### Arquivos principais alterados
- `api/app/routes/favorites.py`, `api/app/schemas/favorite.py`, `api/app/services/favorite_service.py`
- `api/app/services/auth_service.py`, `api/app/main.py`, `api/tests/test_favorites.py`, `api/README.md`
- `docs/05-API-Specification.md`, `docs/adr/0016-owner-scoped-favorites.md`, `docs/adr/README.md`
- `docs/CONTINUATION.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Schema `0008_favorites` entregue separadamente em `bfa418b`. JSON contém somente o item da origem, sem score/explicação/consulta/contexto. Não há FK ao cache/catálogo nem payload arbitrário do cliente.
- Decisão final após revisão: `ON CONFLICT DO UPDATE` sem alterar valores (`id = favorites.id`) com `RETURNING` e UUID candidato para distinguir criação/repetição. Preserva o primeiro snapshot e mantém a operação protegida até commit, sem SELECT posterior. Substitui no serviço a proposta inicial de DO NOTHING registrada na entrega do schema.
- DELETE ausente/de outra conta retorna o mesmo 204, sem vazamento ou efeito sobre terceiros. Status/listagem/exclusão funcionam mesmo se a tabela de origens estiver indisponível. Erros 401/404/422/503 conforme contrato; I/O de banco fora do event loop.

### Estado atual
- **Backend validado:** 346 testes aprovados (31 de favoritos, 17 de migração), Ruff/formatação (82 arquivos), gates v7 K=5/10 sem mudanças/regressões. Testes cobrem duas contas, música/livro/trilha, origem expirada, reinício, dedup, lote, paginação, rollback, falha de auth/banco/cache e três processos SQLite criando/excluindo. O caso multiprocessos bloqueado no sandbox do agente de banco também passou no terminal Maestro. Revisão das correções: nenhum novo bloqueador.
- **Frontend permanece WIP:** build aprovado (2.045 módulos; aviso não fatal de bundle 500,83 kB), `node tests/favorites.mjs` completo aprovado, 36 capturas `favorites-*` ignoradas em `.impeccable/review/`. Esperas de rota/filtro corrigidas pelo agente frontend apenas nos testes, preservando asserções. `npm test`, live/API real e os seis outros módulos da árvore atual **não foram executados/validados nesta etapa**: usuário encerrou o dia durante a autorização. Não declarar UI concluída nem commitar seus arquivos ainda.
- Usuário pediu encerramento por hoje; os agentes foram avisados e liberaram documentos compartilhados. Arquivos frontend modificados/não rastreados foram preservados para amanhã e ficam fora do commit backend. Sem novas tarefas, push ou mudanças de chaves/cotas/modo/servidores/dados existentes.
- PostgreSQL/pgvector real e CI hospedada seguem pendentes. O caso READ COMMITTED foi corrigido por semântica SQL/revisão e testado em SQLite, sem afirmar validação PostgreSQL real.

### Próximos passos
- Retomar pela árvore frontend WIP: conferir Git e combinar escopo com Frontend via Maestri; executar `npm test` em `frontend` (sete módulos, API/SQLite temporários). Se falhar, enviar stack/linha ao frontend e repetir só casos afetados após correção; não enfraquecer asserções. Build e favoritos isolados já passaram nesta árvore.
- Validar E2E de favoritos MUSIC/BOOK, coleção/filtros/remoção, retorno do login sem autosave e isolamento entre contas (DELETE estrangeiro 204); revisar as 36 capturas e capturas reais geradas por live, preservando visual aprovado. Só então registrar entrega/commit frontend seletivo e local.
- Aplicar migração 0008 no banco correto antes de iniciar (`local.py` faz automaticamente); validar PostgreSQL real, inclusive criar/repetir/excluir em concorrência. Histórico exige contrato de privacidade próprio e não foi iniciado. Não fazer push sem pedido explícito.

## 2026-10-01 — Schema de favoritos individuais por conta

### Implementado
- Modelo `Favorite` exportado por `app.models` e migração reversível `0008_favorites`, após `0007_recommendation_results`.
- Favoritos de música/livro com UUID4, proprietário obrigatório, snapshot JSON/JSONB somente do item, identidade pública do provedor, origem da recomendação e data do banco. CHECK de tipo, unicidade por conta/tipo/item e índices para listagem por conta/com filtro de tipo.
- Testes de upgrade/downgrade, paridade modelo/schema, UUID/data default, campos obrigatórios, FK/tipos, unicidade entre contas/tipos, cascata, sobrevivência à remoção da origem/catálogo e preservação das tabelas anteriores.

### Arquivos principais alterados
- `api/app/models/favorite.py`
- `api/app/models/__init__.py`
- `api/alembic/versions/0008_favorites.py`
- `api/tests/test_migrations.py`
- `docs/04-Data-Model.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Única FK: `user_id` → `users.id` com CASCADE. `item_id` e `source_recommendation_id` não referenciam catálogo/cache: favorito não exige catalogar o item e permanece após expiração da origem.
- UUID4 é default do modelo; `created_at` usa default `now()` do banco com tipo timezone-aware no PostgreSQL. Revisões anteriores preservadas.
- Favoritos separados de `interactions`, playlists e histórico automático; não persistem consulta, motivos, score ou contexto e não alteram ranking. O backend deve filtrar o JSON para somente metadados do item.
- Unicidade `uq_favorites_user_type_item` permite ao backend usar `ON CONFLICT DO NOTHING` preservando primeiro snapshot/origem/data. HTTP/ownership da consulta/exclusão são responsabilidade da entrega backend separada.

### Estado atual
- Schema implementado e 17 testes de migração aprovados; Ruff/formatação aprovados. Suíte relacionada de migração/auth/playlists/cache: 69 aprovados, um caso de três processos bloqueado por `WinError 5` ao abrir named pipe do `ProcessPoolExecutor` no sandbox Windows, antes de executar os workers. Esse caso precisa ser revalidado no terminal Maestro; não houve falha de schema nos casos executados.
- SQL PostgreSQL de upgrade/downgrade validado, sem execução PostgreSQL/pgvector real: esse gate permanece pendente.
- Store/rotas de favoritos e interface estão em desenvolvimento por outros agentes; este registro não declara essas integrações concluídas. Validação usa SQLite temporário com FKs habilitadas, sem alterar banco/servidores existentes.
- Commit de banco deve selecionar somente os seis arquivos acima. `.git` somente leitura nesta sessão; commit local autorizado pelo terminal Maestro após revisão, sem push. Frontend aguarda esse commit antes de adicionar sua entrada ao log.

### Próximos passos
- Backend concluir/testar POST com origem validada (201 novo/200 existente, primeiro snapshot preservado), GET paginado/com filtro por proprietário e DELETE idempotente 204, inclusive ausente/de terceiro.
- Frontend integrar favoritos individuais de música/livro e gestão por conta, sem histórico/feedback/ranking; validar com duas contas e origem expirada.
- Aplicar `alembic upgrade head` no banco correto antes das novas rotas; testar migração/cascata/persistência em PostgreSQL/pgvector descartável quando disponível. Não fechar esse gate apenas com SQL gerado.

## 2026-10-01 — Cache de recomendações compartilhado entre instâncias

### Implementado
- Integrado o schema 0007 ao backend local/online para salvar origens de trilha e recuperar explicações após reinício ou troca de instância, enquanto válidas. Endpoints, contratos e isolamento das playlists preservados.
- Snapshot contém somente identidade, itens e resumo da playlist; publicação acontece depois de filtros/paginação/resumo. Consulta, intenção interpretada e conta não são persistidas.
- TTL de uma hora sem renovação nas consultas, limite global de 256 e limpeza de expirados/evicção em transações. Banco é fonte única; não há cópia local capaz de ressuscitar removidos. Sem banco configurado, cache público em memória preservado.
- I/O do cache fora do event loop; banco configurado indisponível/desatualizado retorna 503 sem expor SQL. Origem ausente/expirada/removida continua 404; playlists já salvas continuam disponíveis.

### Arquivos principais alterados
- `api/app/services/recommendation_cache.py`, `api/app/services/recommendation_service.py`, `api/app/services/online_recommendations.py`
- `api/app/main.py`, `api/app/routes/recommendations.py`, `api/app/routes/playlists.py`
- `api/tests/test_recommendation_cache.py`, `api/tests/test_playlists.py`
- `api/README.md`, `docs/05-API-Specification.md`
- `docs/adr/0015-shared-recommendation-cache.md`, `docs/adr/0014-owner-scoped-playlists.md`, `docs/adr/README.md`
- `docs/CONTINUATION.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- SQLite serializa escrita antes de limitar o cache; PostgreSQL usa bloqueio consultivo por transação. Preservar a gravação recém-publicada quando timestamps empatam. PostgreSQL real ainda não validado.
- TTL usa milissegundos Unix UTC entre instâncias. Acessos/gravações purgam expirados, mas não há job periódico: sem tráfego, dados expirados podem ficar em disco, sempre inacessíveis pelo cache. Não equivale a histórico pessoal ou limpeza de backups.
- Banco configurado é dependência para gerar/recuperar resultados: não cair em memória após falha, pois outra instância não poderia recuperar essa origem. Aplicar 0007 antes de iniciar; `local.py` migra automaticamente.
- Coordenação via Maestri entre Maestro/backend, Frontend e Banco de Dados, com as três conexões verificadas. Commits locais separados de schema (`54e13c2`) e frontend (`d2359c2`) registrados neste terminal após revisão/testes, pois os outros terminais não podiam escrever `.git`. Nenhum frontend editado por este agente.

### Estado atual
- 302 testes backend aprovados; sete novos casos cobrem snapshots mínimos/cópias, TTL exato sem renovação, evicção global, três processos SQLite concorrentes, duas aplicações/contas, falha de banco e empate de timestamps. Ruff/formatação aprovados; gates v7 K=5/10 sem mudanças ou regressões. Compatibilidade online sem banco revalidada em 43 testes após ajuste final. Persiste aviso Starlette/httpx conhecido.
- Build e todos os seis módulos frontend aprovados, incluindo playlists/E2E real com duas contas. Agente frontend revisou 24 capturas nos dois temas e três larguras, com reviewer `ship`. Testes usaram API/bancos temporários; dados e configuração do usuário não foram modificados. Nenhum push/deploy.
- PostgreSQL/pgvector real, concorrência de refresh nesse banco, CI hospedada, lock Python, mypy e avaliações online amplas continuam pendentes.

### Próximos passos
- Iniciar backend atualizado com banco migrado até 0007; verificar readiness e salvar/explicar uma trilha na instância correta, mantendo o modo online existente se necessário. Não copiar SQLite ativo para outra máquina; parar a API ou usar backup consistente.
- Agente de banco: com PostgreSQL/pgvector disponível, testar migração e cache/refresh concorrentes em banco descartável antes de ampliar implantação com múltiplos workers.
- Backend/infra: preparar lock Python e mypy incremental; após push explicitamente autorizado, conferir jobs/artefatos da CI hospedada. Para favoritos/histórico, definir contrato de proprietário/privacidade antes de persistir consultas ou integrar botões na UI.

## 2026-10-01 — Integração de playlists na conta

### Implementado
- Interface de salvar a trilha inteira com nome, lista paginada na conta, detalhe com faixas/links externos e exclusão com confirmação inline.
- Login/cadastro a partir de uma trilha conserva seleção e controles ao retornar. Cliente tipado reutiliza Bearer/refresh em memória e cancela requisições ao sair, trocar de conta ou desmontar a página; respostas tardias de outra sessão são rejeitadas.
- Estados de carregamento, vazio, retry, sessão expirada, playlist ausente e origem expirada; duração real e estimada continuam distintas. Endpoints e ranking preservados.

### Arquivos principais alterados
- `frontend/src/lib/playlists.ts`, `frontend/src/lib/auth.ts`
- `frontend/src/components/SavePlaylist.tsx`, `frontend/src/components/AccountPlaylists.tsx`
- `frontend/src/pages/Playlist.tsx`, `frontend/src/pages/Account.tsx`, `frontend/src/pages/Authentication.tsx`, `frontend/src/pages/ReadWithMusic.tsx`
- `frontend/src/App.tsx`, `frontend/src/main.tsx`, `frontend/src/playlists.css`
- `frontend/tests/playlists.mjs`, `frontend/tests/live.mjs`, `frontend/tests/auth.mjs`, `frontend/package.json`, `frontend/README.md`
- `docs/CONTINUATION.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Criação usa `source_recommendation_id`, sem reconstruir a playlist pelos IDs ou fazer consultas extras de catálogo. O backend copia os metadados/ordem da seleção real.
- Extensão do visual aprovado, com linhas de resultado e confirmação inline; sem redesenho, dependência nova, áudio/exportação ou uso de playlists como favoritos/feedback.
- Dados privados pertencem à sessão atual; estado de retorno do login contém somente a trilha pública/controles, nunca tokens. Cancelamento e verificação da revisão de sessão evitam repopular a conta com respostas antigas.

### Estado atual
- Build e todos os módulos da suíte frontend aprovados no terminal Maestro: smoke, componentes, autenticação, continuação, playlists e E2E real. TypeScript/sintaxe/diff e detector visual sem achados também passaram no terminal frontend. Esperas de navegação, carregamento, logout e retorno de foco foram corrigidas nos testes; asserções de validade nativa, títulos completos, isolamento, revogação e foco preservadas.
- E2E real com SQLite temporário validou salvar/listar/detalhar, as mesmas 11 faixas após logout/troca de conta, GET/DELETE 404 para outra conta, confirmação/cancelamento/exclusão e refresh revogado com 401. Suíte simulada cobre paginação, retries, origem expirada, retorno de login/cadastro com controles, refresh e cancelamento/respostas tardias. Servidores/dados existentes preservados.
- 24 capturas de salvar/lista/detalhe/confirmação em 1440/390/320 px nos dois temas revisadas; reviewers independentes retornaram `ship` no escopo visual/código, sem defeitos materiais. Documenter confirmou extensão do sistema aprovado; `DESIGN.md` e sidecar preservados. Drift preexistente do sidecar permanece, sem reparo incidental.
- Subprocessos e escrita em `.git` bloqueados no terminal frontend: validação e commit coordenados pelo Maestri com Maestro. Schema paralelo `0007` foi commitado separadamente em `54e13c2` antes deste registro; integração backend/cache permanece na entrega desse agente. Não há edição/exportação de playlists, favoritos individuais ou histórico nesta entrega.

### Próximos passos
- Após o commit frontend isolado, liberar `DEVELOPMENT_LOG.md`, `CONTINUATION.md` e `IMPLEMENTATION_STATUS.md` ao Maestro para registrar o cache compartilhado já desenvolvido/testado por esse agente; não incluir seu WIP no commit frontend nem fazer push.
- Definir contrato e persistência próprios de favoritos individuais de livros/músicas e histórico por conta antes de adicionar botões/listas desses recursos. Não reutilizar playlists como feedback do ranking.
- Experimentar salvar/consultar uma trilha online pela interface na instância correta, conservando duração real/estimada e tratamento de fonte insuficiente. Edição/exportação, PostgreSQL real e gates online seguem pendentes.

## 2026-10-01 — Schema do cache compartilhado de recomendações

### Implementado
- Modelo `RecommendationResult` e migração reversível `0007_recommendation_results`, acordados com o agente de backend para compartilhar resultados entre processos e permitir salvar uma trilha após reiniciar a API durante sua validade.
- Snapshot JSON/JSONB com ID UUID original e timestamps UTC em milissegundos (`BIGINT`). Índices por criação/ID e expiração permitem limitar e limpar o cache.
- Testes de upgrade/downgrade, preservação de contas/catálogo/playlists, leitura por conexões independentes, timestamps de 64 bits, unicidade/NOT NULL e paridade entre schema migrado e modelos.

### Arquivos principais alterados
- `api/app/models/recommendation_result.py`
- `api/app/models/__init__.py`
- `api/alembic/versions/0007_recommendation_results.py`
- `api/tests/test_migrations.py`
- `docs/04-Data-Model.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Cache anônimo temporário, sem colunas de usuário, consulta, intenção interpretada ou contexto. O serviço deve filtrar o JSON para itens/playlist e identidade da recomendação; não equivale a histórico pessoal.
- TTL de 3.600 segundos e limite global de 256 são responsabilidade do store de backend. A migração não adiciona FK em `playlists.source_recommendation_id`, preservando playlists salvas quando o cache expira.
- Mantidas revisões anteriores intactas; downgrade para `0006_playlists` descarta somente a tabela/índices do cache, preservando os dados existentes.

### Estado atual
- Quatro testes de migração aprovados, Ruff/formatação aprovados; 42 testes de migração/playlists aprovados em cópia isolada do HEAD com apenas a mudança de banco. Suíte completa da árvore compartilhada após os ajustes de testes do backend: 295 aprovados.
- Modelo disponível ao backend em desenvolvimento. A integração do store e rotas pertence à entrega separada desse agente; não é declarada concluída neste registro de schema.
- PostgreSQL/pgvector real continua pendente: Docker Engine indisponível. SQL PostgreSQL gerado validado; execução SQLite em banco temporário, sem alterar banco/servidores existentes.
- Pytest local usa runner ignorado em `.impeccable/db-tests-20261001/run_pytest.py` que preserva ACLs herdadas dos diretórios temporários no sandbox Windows; sem mudança nas permissões do projeto ou dependências.

### Próximos passos
- Concluir e validar o store compartilhado no backend, com expiração, limite de resultados, snapshots mínimos, falha de banco e testes entre instâncias; integrar a interface de salvar/listar/excluir playlists em entrega própria.
- Aplicar `alembic upgrade head` no banco correto antes de executar o backend com cache compartilhado; o iniciador local aplica migrações na próxima inicialização.
- Com PostgreSQL/pgvector disponível, executar upgrade/downgrade em banco descartável e validar persistência/concorrência real; não considerar SQL gerado como aprovação desse gate.

## 2026-10-01 — Trilhas reais completas e busca por títulos em português

### Implementado
- Corrigida leitura online que podia devolver quatro/cinco músicas e cerca de 20 minutos para uma meta de 90. A IA interpreta/ordena uma amostra, mas suas poucas escolhas não limitam o conjunto de faixas compatíveis; a busca continua até atender à duração ou esgotar os limites.
- Sessões online usam somente gravações reais MusicBrainz de lançamentos oficiais, com duração conhecida de 90 segundos a 10 minutos. Consulta exclui spokenword/audiobook/dj-mix; instrumental depende de identificação na fonte. Não completa com músicas locais ou cinco minutos estimados. Sucesso exige a meta; insuficiência retorna `503 SOUNDTRACK_INCOMPLETE`, com contagem/minutos encontrados. Interface existente limpa resultados e apresenta o erro.
- Contexto musical precede o livro e orienta buscas por ambient/piano/soundtrack no pedido de chuva, foco e drama. Até três termos, oito páginas de 50 candidatos por termo, 60 faixas e quatro por artista. Deduplica IDs e título/artista. Falha/cota Groq continua por metadados sem ampliar o limite diário.
- Busca Open Library alcança títulos de edições (`q`, `lang=pt`); descoberta filtra português. Título/capa de edição portuguesa conservam identidade da obra. Alias editorial verificado resolve a edição brasileira “Quem é você, Alasca?”/“Looking for Alaska” de John Green quando falta no índice; não traduz títulos especulativamente nem cria catálogo fictício. Cache externo versionado evita listas antigas em inglês.

### Arquivos principais alterados
- `api/app/providers/musicbrainz.py`, `api/app/providers/open_library.py`, `api/app/providers/portuguese_titles.py`
- `api/app/services/online_soundtrack.py`, `api/app/services/online_recommendations.py`, `api/app/services/book_service.py`
- `api/tests/test_books.py`, `api/tests/test_continuation.py`, `api/tests/test_online.py`, `frontend/tests/continuation.mjs`
- `api/README.md`, `docs/05-API-Specification.md`, `docs/CONTINUATION.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Separado gerador de sessões online da descoberta de músicas/livros, preservando ranking e catálogo offline. Catálogo externo amplo completa a duração; classificação/ordenação da IA não é uma lista fechada de quatro/cinco itens.
- A última faixa permanece inteira e pode ultrapassar a meta. Duração conhecida e identidade do catálogo são requisitos para sucesso online; falta de material é erro explícito, sem playlist curta apresentada como concluída. Limite de quatro faixas por artista vale apenas para leitura online; descoberta/local mantêm seus limites.
- Traduções vêm das edições ou de alias com título/autor verificados pela editora. Fonte de Alasca registrada em `portuguese_titles.py` e na especificação. Sem migração, dependência nova, alteração de chaves/modelo/cota ou edição visual.

### Estado atual
- 293 testes backend aprovados, Ruff/formatação, build e suíte frontend completa aprovados. Testes cobrem IA omitindo escolhas/indisponível, duração desconhecida ou imprópria, quatro faixas insuficientes, paginação, deduplicação, artista/60 faixas, persistência de playlist real, edição portuguesa, alias e rejeição de tradução para autor homônimo. Gates estritos v7 K=5/10 sem mudanças/regressões no ranking local.
- API do projeto identificada/reiniciada online na porta 8000, frontend 5173 preservado, readiness 200. Pedido exato: John Green/Alasca, `FOCUS`, `INSTRUMENTAL`, 90 minutos, “clima chuvoso, musica sem letra para conseguir focar, mas com um toque de drama para combinar com a historia” → 20 faixas MusicBrainz únicas, todas instrumentais identificadas e com duração conhecida, total 5.517.572 ms (91 min 57 s), `target_met=true`, `duration_estimated=false`, `ai_used=true`, `degraded=false`. Evidência local ignorada: `.impeccable/runtime/live-request-v2.json`.
- Buscas reais por “Quem é você, Alasca?” e “Looking for Alaska” retornam a mesma obra em português; Addie LaRue, O Problema dos Três Corpos e Devoradores de estrelas também retornaram títulos portugueses reais. Obras sem edição portuguesa informada/alias verificado conservam título da fonte. Disponibilidade e afinidade dos provedores não são garantidas por esta amostra. Sem reprodução/exportação de áudio; integração de playlists na interface pendente.

### Próximos passos
- Usuário repetir o pedido de Alasca em `http://127.0.0.1:5173` e avaliar afinidade das faixas, além da duração; testar outras descrições/90–120 minutos e recuperação do erro de fonte insuficiente.
- Ampliar avaliação online de títulos portugueses/edições ausentes e atmosferas musicais. Novos aliases exigem fonte editorial verificável; não inventar traduções via IA nem ampliar cotas para compensar busca inadequada.
- Retomar integração de salvar/listar/detalhar/excluir playlists na conta conforme `docs/CONTINUATION.md`; preservar contratos de duração conhecida online e limites do modo offline.

## 2026-10-01 — Novos livros e trilhas que buscam a duração pedida

### Implementado
- “Ver outros livros” substitui sugestões para o mesmo pedido enviado, acumulando IDs já exibidos. Lista atual permanece em espera, erro, cancelamento ou esgotamento; nova busca reinicia as exclusões. Botão e mensagens funcionam nos dois temas e em telas pequenas.
- API de livros aceita `excluded_book_ids` (até 200 UUIDs) e `offset` (0–300); exclusões valem para IA e fallback. Open Library pagina candidatos; cache persistente distingue páginas. `meta.has_more`/`next_offset` orientam continuação.
- Leitura online envia durações e meta restante ao Groq, recuperando novos lotes até atender a meta ou os limites de recuperação. Descrição musical aparece antes dos metadados do livro, sem perder o contexto por truncamento. Deduplicação por ID/título/artista e limite global de duas faixas por artista.
- Resumo de duração compartilhado entre local/online informa meta, total, estimativa e diferença. Interface usa a meta do resultado enviado, mesmo após editar o formulário. Salvamento de trilhas ampliado para até 60 faixas; criação manual permanece limitada a 25.
- Groq respeita `Retry-After` curto em 429, com uma espera de até 30 segundos e uma tentativa adicional; ambas contam no limite local. Interpretação reutilizada nos lotes; cota persistente não causa novas tentativas em cada página. Mensagem final consolida fontes/avisos, sem avisos enganosos de lotes intermediários vazios.

### Arquivos principais alterados
- `api/app/ai/groq.py`, `api/app/providers/musicbrainz.py`, `api/app/providers/open_library.py`
- `api/app/routes/recommendations.py`, `api/app/schemas/recommendation.py`, `api/app/schemas/playlist.py`
- `api/app/services/online_recommendations.py`, `api/app/services/recommendation_service.py`, `api/app/services/reading_duration.py`
- `api/app/services/book_service.py`, `api/app/services/hybrid_books.py`, `api/app/services/playlist_service.py`
- `api/tests/test_continuation.py`, `api/tests/test_online.py`, `api/tests/test_playlists.py`
- `frontend/src/pages/Discovery.tsx`, `frontend/src/pages/ReadWithMusic.tsx`, `frontend/src/lib/api.ts`, `frontend/src/styles.css`
- `frontend/tests/continuation.mjs`, `frontend/package.json`, `api/README.md`
- `docs/05-API-Specification.md`, `docs/adr/0014-owner-scoped-playlists.md`, `docs/CONTINUATION.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Renovação mantém a consulta enviada, sem aplicar texto ainda editado. Exclusões vivem na página atual, sem criar histórico/feedback persistentes. Catálogo local finito sinaliza esgotamento.
- Trilhas usam até seis lotes de 25 candidatos e no máximo 60 faixas. A última faixa fica inteira e pode ultrapassar a meta. Falta de itens compatíveis, metadados, IA ou cota pode produzir trilha menor: informa o déficit, sem completar com itens incompatíveis.
- Paginação segue contratos Open Library/MusicBrainz; retry limitado segue cabeçalho Groq. Não houve migração, nova dependência, aumento de cota diária, mudança de modelo ou exposição de chaves.
- Extensão visual preserva PRODUCT/DESIGN/sidecar. Detector sem achados; revisão Impeccable `ship` no escopo da extensão, com 20 capturas válidas em `.impeccable/review/continuation-*.png`. Documenter confirmou coerência e registrou divergências anteriores do sidecar, sem repará-las.

### Estado atual
- 281 testes backend aprovados. Cobrem 90 minutos após cinco escolhas iniciais, duração real/estimada, contexto longo, paginação/cache, deduplicação, limites globais/de recuperação, Groq 429, cota local, persistência de 60 faixas, renovação local/online, retry/cancelamento/esgotamento e duração do pedido enviado. Build, suíte frontend completa, Ruff e gates estritos v7 K=5/10 aprovados sem mudanças/perdas no ranking local.
- Instância do projeto reiniciada em modo online na porta 8000, mantendo banco/segredo e frontend 5173. Busca real de livros retornou seis opções e depois três novas sem IDs repetidos; IA ativa, sem degradação. Teste real de leitura de Duna, jazz suave instrumental com saxofone/piano, 90 minutos: 26 faixas únicas, 19 MusicBrainz com duração conhecida e sete locais estimadas; total 5.701.078 ms (cerca de 95 min), meta atendida, máximo duas por artista, `ai_used=true`, `degraded=false`.
- Primeira tentativa real musical acionou fallback por 429 do Groq. Depois do tratamento limitado, nova tentativa atingiu a meta. Essas amostras não garantem disponibilidade futura, afinidade em todas as consultas ou preenchimento de qualquer pedido. Sem reprodução/exportação de áudio; playlists ainda não integradas à interface.

### Próximos passos
- Usuário testar “Ver outros livros” e leitura de 90/120 minutos em `http://127.0.0.1:5173`, inclusive descrições/exclusões específicas; conferir duração conhecida/estimada e avisos de déficit/cota.
- Retomar integração de playlists na conta conforme `docs/CONTINUATION.md`; usar origem pública completa ou subconjunto de até 60 faixas, com retry de expiração/autorização e revisão responsiva.
- Avaliar corpus/qualidade online e casos em que seis lotes não preenchem a meta antes de alterar limites; preservar filtros, deduplicação e limite diário existente. PostgreSQL/CI hospedada e cache compartilhado continuam pendentes.

## 2026-10-01 — Instância local online para testes reais

### Implementado
- A pedido do usuário, substituída a API offline identificada na porta 8000 por `local.py` com `GANDALF_ONLINE=1`, em segundo plano. Frontend existente na porta 5173 preservado; banco/segredo locais mantidos e migração 0006 aplicada pelo iniciador.
- Configuração online existente de `api/.env` carregada sem exibir chaves: Groq configurado com `openai/gpt-oss-20b`, limite local de 50 chamadas/dia; Open Library e MusicBrainz ativos. Sem mudança de dependências, código, segredo, faturamento ou limite.
- Conferidas buscas externas e descoberta com IA real em músicas/livros. Diagnóstico temporário em `.impeccable/runtime/` mostrou HTTP 200 da seleção estruturada Groq e da busca por tag MusicBrainz, sem registrar corpos de erro/chaves.

### Arquivos principais alterados
- `docs/DEVELOPMENT_LOG.md`
- `docs/CONTINUATION.md`
- `docs/IMPLEMENTATION_STATUS.md`

### Decisões técnicas
- API iniciada com `Start-Process -WindowStyle Hidden`; logs de execução em `.impeccable/runtime/online-api.stdout.log` e `online-api.stderr.log`, ignorados pelo Git. Mantido frontend já ligado à API na porta 8000, sem encerrar processos alheios ao projeto.
- Validada a presença da chave apenas como booleano. Testes online usam conta/limites já configurados e não ativam cobrança nem substituem os testes offline reprodutíveis.

### Estado atual
- Interface: `http://127.0.0.1:5173` (HTTP 200). Swagger: `http://127.0.0.1:8000/docs`. `/health/ready` retorna 200 com banco/schema ok; `/api/v1/system/status` retorna `catalog=online`, Groq configurado e `gpu_used=false`.
- Busca musical por GoGo Penguin retornou cinco gravações MusicBrainz, incluindo Atomised/Embers. Busca por Project Hail Mary retornou obras Open Library, incluindo Andy Weir. Descoberta musical de jazz/saxofone/piano retornou faixas de Steve Swallow; descoberta de ficção científica/exploração espacial retornou Project Hail Mary, The Dark Forest e outras obras externas. Nas duas descobertas finais: `ai_used=true`, `degraded=false`, fontes externas.
- A primeira descoberta apresentou indisponibilidade transitória de IA/catálogo e acionou fallback local. Diagnóstico e nova tentativa passaram; causa precisa dessa primeira falha não foi determinada. Uma amostra real bem-sucedida não fecha gates de cobertura/licenças, qualidade do corpus online ou estabilidade dos provedores. Catálogo local continua como fallback e pode compor resultados online; não há reprodução de áudio/exportação.
- Etapa de playlists concluída no commit local `40e0eea`; 258 testes backend, Ruff, ranking K=5/10, build e suíte frontend aprovados antes da ativação online. Nenhum push ou deploy público.

### Próximos passos
- Usuário testar os três fluxos na interface ou via Swagger; conferir mensagens de IA/fonte nos resultados e reportar consultas que retornem vazio/fallback ou obras inadequadas. Para busca direta usar `/api/v1/music/search` e `/api/v1/books/search`; discovery usa `/api/v1/recommendations/music` e `/api/v1/recommendations/books`.
- Para reiniciar no mesmo modo, identificar/encerrar a instância do projeto nas portas 8000/5173 e executar `./start-local.ps1 -Online`; não executar sem `-Online` se quiser manter acesso aos catálogos externos. Não duplicar processos nem expor `api/.env`.
- Retomar a integração de playlists na interface conforme a entrada anterior e `docs/CONTINUATION.md`; manter avaliações online amplas, revisão humana, PostgreSQL e CI hospedada como pendências.

## 2026-10-01 — Playlists persistentes por conta na API

### Implementado
- Criados `POST /api/v1/playlists`, `GET /api/v1/playlists`, `GET /api/v1/playlists/{id}` e `DELETE /api/v1/playlists/{id}` com Bearer, conta ativa e isolamento por proprietário. Listagem paginada retorna resumos; consulta/exclusão de recursos de outra conta usa o mesmo 404 de recurso ausente.
- Criação manual por 1–25 IDs musicais únicos do catálogo e salvamento de trilha de leitura pública ainda disponível, inteira ou um subconjunto ordenado. Valida origem, expiração, faixas e campos antes de escrever; cliente não fornece proprietário nem metadados.
- Migração reversível `0006_playlists`, com cópia dos metadados/ordem, duração calculada e flag de estimativa. Playlist e faixas permanecem após reinício/expiração/atualização do catálogo; transação única reverte gravações parciais. Exclusão preserva o catálogo compartilhado.
- Habilitadas FKs nas conexões SQLite da aplicação para aplicar CASCADE/RESTRICT no modo local. Contrato, modelo, roadmap, matriz e continuidade atualizados; decisão registrada no ADR-0014.

### Arquivos principais alterados
- `api/alembic/versions/0006_playlists.py`, `api/app/models/playlist.py`, `api/app/models/__init__.py`
- `api/app/schemas/playlist.py`, `api/app/routes/playlists.py`, `api/app/services/playlist_service.py`
- `api/app/database/session.py`, `api/app/services/recommendation_service.py`, `api/app/main.py`
- `api/tests/test_playlists.py`, `api/tests/test_migrations.py`, `api/tests/test_online.py`, `api/README.md`
- `docs/04-Data-Model.md`, `docs/05-API-Specification.md`, `docs/12-development-roadmap.md`
- `docs/adr/0014-owner-scoped-playlists.md`, `docs/adr/README.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/CONTINUATION.md`, `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Aproveitado `music_catalog` existente, com FK das faixas e cópia JSON independente. Músicas locais entram no catálogo apenas ao serem salvas; nenhuma operação de playlist consulta provedores externos. Total usa bigint para suportar soma acima de 32 bits; duração desconhecida continua ausente/nula no item, com estimativa somente no total.
- Origem anônima é identificada por UUID imprevisível, como nas explicações públicas; não tem proprietário nem vira histórico pessoal. `source_recommendation_id` é proveniência sem FK e não persiste query/contexto. A playlist criada pertence à conta autenticada. Apenas trilhas são aceitas como origem nesta etapa; descoberta musical pode usar o fluxo manual por IDs.
- Cache é copiado no event loop antes da transação no pool de threads. Salvar não renova TTL; cache ausente/expirado retorna 404 mesmo com músicas no corpo. Sem novas dependências, alterações de ranking ou de interface.

### Estado atual
- 258 testes backend aprovados (38 novos), Ruff check/formatação aprovados. Cobertura de duas contas, autenticação inválida/expirada e conta inativa, paginação, ordem/subconjuntos, validações/TTL, persistência após reinício, metadados/duração, rollback por falha real de gravação, cascata de conta/restrição de catálogo e upgrade/downgrade. Integração online usa provedores simulados e confirma salvamento/leitura/exclusão sem chamadas adicionais. SQL PostgreSQL gerado; execução real ainda pendente.
- Comparação estrita K=5/10 contra v7: zero mudanças no catálogo, resultados ou métricas; nenhuma regressão agregada/por consulta. `npm run build` e `npm test` aprovados (smoke, componentes, auth e E2E com API real/SQLite temporário). Permanece somente o aviso conhecido Starlette/httpx na API.
- Servidores/dados locais existentes preservados; API temporária do E2E iniciou com a migração nova. O sandbox bloqueou cache de pytest e subprocesso esbuild; validações concluídas com permissão para temporários/subprocessos. Nenhum acesso direto a `api/.env`, push ou deploy. Interface de playlists, favoritos/histórico, edição/exportação e PostgreSQL real não estão concluídos. Uma instância local já em execução precisa ser reiniciada para carregar as novas rotas/migração.

### Próximos passos
- Expor o cliente autenticado de `frontend/src/lib/auth.ts` para as novas rotas e adicionar tipos/API de playlists; integrar salvar trilha em `frontend/src/pages/ReadWithMusic.tsx` e lista/detalhe/exclusão na conta. Cancelar requisições ao sair/trocar de conta, tratar expiração de origem e erros com retry; preservar sessão somente em memória, visual e animações aprovados.
- Testar UI com duas contas/API real/SQLite temporário, incluindo isolamento, paginação, logout durante solicitações, renovação compartilhada e 401/404/503; revisar desktop/mobile e ambos os temas. Depois definir contratos/migrations de favoritos e histórico próprios, sem tratá-los como feedback já implementado.
- Em PostgreSQL/pgvector descartável, validar migração 0006 up/down, integridade e concorrência; resolver cache/recomendações entre processos antes de escalar. Manter gates de revisão humana/conjunto reservado, provedores e CI hospedada abertos; não fazer push sem pedido explícito.

## 2026-10-01 — Cadastro, login e conta na interface

### Implementado
- Integradas telas `/register`, `/login` e `/account` aos endpoints existentes de cadastro, login, dados da conta e logout. Cabeçalho alterna entre Entrar/Minha conta, preservando os três fluxos públicos sem conta e o visual aprovado.
- Formulários com validação, confirmação/visibilidade de senha, preenchimento do e-mail após cadastro, estados de envio, erros focados/anunciados e retry. Navegar para fora cancela requisições de formulário.
- Sessão somente em memória, renovação rotativa compartilhada e logout que aguarda rotação/revoga o token atual. Respostas atrasadas após saída não restauram a conta; refresh inválido leva novamente ao login.
- Corrigida documentação frontend obsoleta; CI paralela concluída em `ccffe39` preservada integralmente.

### Arquivos principais alterados
- `frontend/src/lib/auth.ts`, `frontend/src/lib/useSession.ts`, `frontend/src/lib/api.ts`
- `frontend/src/pages/Authentication.tsx`, `frontend/src/pages/Account.tsx`, `frontend/src/account.css`, `frontend/src/App.tsx`, `frontend/src/main.tsx`
- `frontend/tests/auth.mjs`, `frontend/tests/live.mjs`, `frontend/package.json`, `frontend/README.md`
- `docs/IMPLEMENTATION_STATUS.md`, `docs/CONTINUATION.md`, `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Mantido ADR-0006: sem tokens em localStorage/sessionStorage/cookies; reload/fechamento exige login. Registro não autentica automaticamente, seguindo os contratos da API. Sem novas dependências, endpoints ou migrations.
- Uma renovação por sessão atende requisições concorrentes; 401 atrasado reutiliza o par novo. Saída bloqueia novas renovações e aguarda as já iniciadas para impedir revogação de um refresh antigo. Falha de rede ao sair mantém a conta disponível para retry.
- Cliente HTTP conserva Headers/Authorization, identifica status de erro e aceita 204 sem tentar decodificar JSON. Esperas dos testes usam a nova tela montada antes de preencher campos compartilhados; navegação tem timeout de 30 s, sem sleeps fixos.

### Estado atual
- `npm run build` e `npm test` aprovados: smoke, componentes, autenticação simulada e E2E com API real/SQLite isolado. Cobertura de validação, erros 401/409/429, tokens somente em memória, rotação simultânea/401 atrasado, renovação proativa, logout durante refresh, retry/204, expiração, cancelamento e resposta de perfil após saída. E2E confirma refresh revogado no banco.
- 220 testes backend e Ruff check/formatação aprovados; permanece o aviso conhecido Starlette/httpx. Capturas de login/cadastro/conta em 1440/390/320 px, claro/escuro, inspecionadas sem overflow; detector Impeccable retornou `[]`. Revisão independente Impeccable: `ship` para esta extensão Operate, sem correções materiais; estados transitórios corroborados no código/testes, sem capturas específicas. Capturas ignoradas pelo Git em `.impeccable/review/auth-*`.
- Servidores existentes em 5173/8000 preservados; testes usam portas/banco temporários. Nenhum acesso a `api/.env`, consulta ao 21st, push ou deploy nesta etapa. Histórico/salvos, playlists persistentes, recuperação de senha, edição da conta e preferências ainda pendentes. Conferência de documentação Impeccable preservou `PRODUCT.md`, `DESIGN.md` e sidecar; divergências preexistentes de tokens não foram incorporadas nem corrigidas nesta extensão.

### Próximos passos
- Definir contratos e migrations para playlists/salvos por proprietário, com autorização e isolamento entre contas; integrar os fluxos públicos após testes de persistência.
- Continuar revisão humana/conjunto reservado do ranking v7 e gates de provedores/infra. CI hospedada só deve ser verificada após push explicitamente autorizado; detalhes em `docs/CI.md`.

## 2026-10-01 — CI inicial para API, ranking e fluxos públicos

### Implementado
- Configurado GitHub Actions para PRs destinados a `main`, pushes em `main` e execução manual: Ruff/formatação, pytest/SQLite, comparação estrita do ranking v7 em K=5/10 e build/smoke/componentes/E2E dos três fluxos públicos.
- Relatórios JUnit/JSON e capturas PNG são coletados após sucesso ou falha, quando gerados, com retenção de sete dias. CI usa API local e SQLite temporário, sem chaves de provedores.
- Corrigida uma espera no teste responsivo de carregamento após mudar viewport/tema, autorizada pelo usuário. Componentes, estilos e animações aprovados preservados.
- Documentados escopo, resultados locais, comandos e limitações da CI; matriz e roadmap distinguem workflow preparado de execução hospedada aprovada.

### Arquivos principais alterados
- `.github/workflows/ci.yml`, `frontend/tests/components.mjs`
- `docs/CI.md`, `api/README.md`
- `docs/10-testing-strategy.md`, `docs/11-deployment-guide.md`, `docs/12-development-roadmap.md`
- `docs/CONTINUATION.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Dois jobs em Ubuntu 24.04, Python 3.12 e Node 24. Actions fixadas por SHA completo conferido nos releases oficiais; token com `contents: read`, sem persistência de credenciais no checkout.
- Mantidos os baselines v7 versionados e `--fail-on-case-regression`; CI não atualiza julgamentos/baselines automaticamente. Instalação requer rede, mas testes não consultam provedores reais.
- Espera do teste usa timeout do Playwright antes da asserção de overflow, para permitir atualização do layout; overflow persistente continua sendo falha.
- Integração de UI `beb7569` preservada. Novas alterações de autenticação feitas simultaneamente por outro terminal ficam fora deste commit; precisam de validação própria.

### Estado atual
- Actionlint v1.7.12, Ruff check/formatação e 220 testes backend aprovados; JUnit gerado. Gates K=5/10 contra v7: zero regressões agregadas ou por consulta, sem mudança de catálogo. Persiste o aviso conhecido Starlette/httpx.
- `npm run build` e `npm test` (smoke, componentes e E2E com API real) aprovados no checkout com as variáveis da CI, após a integração de UI e a correção autorizada do teste.
- Primeira execução no runner hospedado e instalação limpa de dependências ainda não verificadas. Nenhum push ou deploy realizado; G6 permanece aberto. Python ainda instala faixas de versões sem lock; mypy, PostgreSQL/pgvector e avaliações online reais não fazem parte deste workflow inicial.

### Próximos passos
- Após um push explicitamente autorizado, conferir os dois jobs no GitHub Actions e baixar `api-results`/`frontend-screenshots`; confirmar instalação limpa e Chromium no Ubuntu antes de registrar CI hospedada aprovada.
- Continuar backend/infra com lock de dependências Python e adoção incremental de mypy; adicionar job PostgreSQL/pgvector somente junto de testes de migração/concorrência nesse banco.
- Conferir o Git antes de retomar autenticação da interface no outro terminal. Para ranking, usar v7 como baseline e obter revisão humana/conjunto reservado antes de novos ajustes.

## 2026-10-01 — Accordion, Toggle Group e Skeleton integrados

### Implementado
- Concluído o handoff de UI: dependências Radix instaladas; Accordion em preferências e explicações, Toggle Group de vocais/energia e Skeletons nos carregamentos de música, livros e trilhas. Removidos os usos de `Why` e estilos antigos de summary/select.
- Preferências permitem teclado e limpeza, preservam os valores HTTP e exibem os filtros usados na busca. Mudanças posteriores no formulário avisam que é necessário buscar novamente.
- `Explanation` compartilhado busca somente ao abrir, reutiliza respostas, oferece retry explícito e aborta ao desmontar; também presente nas faixas de leitura.
- Testes e créditos/licença atualizados. Trabalho backend paralelo reconciliado com o commit `f120676`, preservado integralmente e validado com a nova UI.

### Arquivos principais alterados
- `frontend/src/components/ui/accordion.tsx`, `frontend/src/components/ui/toggle-group.tsx`, `frontend/src/components/ui/skeleton.tsx`, `frontend/src/components/ui/components.css`
- `frontend/src/components/Explanation.tsx`, `frontend/src/pages/Discovery.tsx`, `frontend/src/pages/ReadWithMusic.tsx`, `frontend/src/main.tsx`, `frontend/src/styles.css`
- `frontend/package.json`, `frontend/package-lock.json`, `frontend/THIRD_PARTY_NOTICES.md`
- `frontend/tests/components.mjs`, `frontend/tests/smoke.mjs`, `frontend/tests/live.mjs`
- `DESIGN.md`, `docs/HANDOFF_MAESTRI.md`, `docs/CONTINUATION.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Instalação com `NODE_OPTIONS=--use-system-ca` temporário; TLS permaneceu validado e a configuração anterior foi restaurada. Nenhuma nova consulta de código ao 21st, acesso à chave ou alteração em `api/.env` nesta continuação.
- Radix mantém papéis radiogroup/radio e navegação por setas; opções indiferentes são omitidas da requisição. Filtros submetidos ficam separados do formulário; componentes de resultado usam a identidade da recomendação para evitar cache de explicação de uma busca anterior.
- Skeletons têm `aria-hidden`; mensagens e cancelamento continuam reais. Accordion, Skeleton e escolhas respeitam movimento reduzido. Créditos shadcn/MIT registrados com fontes e URLs do catálogo.
- Servidores existentes em 5173/8000 foram verificados e preservados. Smoke/E2E usam portas temporárias e SQLite isolado, sem tocar nos dados de `api/.local`.

### Estado atual
- `npm test` (smoke, componentes e E2E real offline) e `npm run build` aprovados. Cobertura de teclado, filtros none/required/low/medium/high e omissão, snapshot/limpeza, explicações lazy/cache/retry, cancelamento, troca de livro e respostas antigas.
- 220 testes backend, Ruff check e formatação aprovados. Comparação estrita v6→v7 em K=5/10 confirma zero regressões agregadas ou por consulta. Persiste o aviso de depreciação Starlette/httpx já conhecido.
- Capturas dos três fluxos com API real em 1440/390/320 px, claro/escuro, sem overflow; contraste dos filtros ≥4,5:1. Loading capturado em desktop escuro/mobile claro; movimento reduzido verificado e console sem erros no E2E. Capturas reproduzíveis em `.impeccable/review/components-*`, ignoradas pelo Git. Detector Impeccable não encontrou ocorrências.
- Frontend existente serve os componentes atualizados; API existente retorna v7 e readiness saudável. A integração de UI está concluída; gates de provedores, revisão humana, PostgreSQL e CI continuam abertos.

### Próximos passos
- Revisar b03/m06 e os cinco modos de leitura com avaliação humana usando os relatórios v7; criar conjunto reservado antes de novos ajustes do ranking.
- Para evolução da UI, iniciar persistência de playlists/salvos e conectar registro/login aos endpoints existentes, com contratos e estados de conta definidos conforme o roadmap.
- Concluir cobertura/termos dos provedores, avaliação online real e infraestrutura/CI. Não repetir `.impeccable/integrate-components.py`; o handoff original está preservado como histórico.

## 2026-10-01 — Piano e detetive validados no ranking v7

### Implementado
- Concluída a etapa iniciada em `39a7395`: formalizadas fontes por obra para sete etiquetas de piano e a categoria detetive em O Cão dos Baskervilles, preservando itens/IDs e o visual aprovado.
- Acrescentados 28 casos de teste para interpretação/negação, descoberta, explicações, referências, exclusões, leitura e fallback online sem IA ou sem chave. Expectativa de versão alinhada a v7; catálogo formatado.
- Gerados relatórios v7 em K=5/10 contra v6, com gate estrito; proteção agregada e por consulta incorporada a `test_evaluation.py`. Corpus e julgamentos mantidos.

### Arquivos principais alterados
- `api/app/providers/local_catalog.py`
- `api/tests/test_books.py`, `api/tests/test_recommendations.py`, `api/tests/test_online.py`, `api/tests/test_evaluation.py`
- `api/README.md`, `docs/05-API-Specification.md`, `docs/IMPLEMENTATION_STATUS.md`, `docs/CONTINUATION.md`
- `docs/catalog-metadata.md`
- `docs/eval-reports/2026-10-01-piano-detective.md`
- `docs/eval-reports/local-v7-piano-detective-k5.json`, `docs/eval-reports/local-v7-piano-detective-k10.json`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Piano descreve obra/edição com piano, sem garantir piano solo ou instrumentação de cada gravação. Detetive é categoria distinta de mistério e participa do desempate por gênero explícito. Cobertura parcial; Saman permanece sem nova etiqueta.
- Preservadas alterações frontend e documentação de outro terminal, recebidas durante esta sessão. Esse trabalho não foi integrado nem incluído no commit v7.
- Build, smoke e E2E executados com a interface aprovada de `3732389` em cópia isolada (`.impeccable/v7-approved-validation`) e backend atual; dependências existentes reutilizadas, sem instalação. Isso não valida os componentes pausados da árvore de trabalho.

### Estado atual
- 220 testes backend, Ruff check e formatação aprovados. Comparação K=5/10 com zero regressões agregadas ou individuais; apenas b03 e m06 mudam. nDCG de b03 chega a 1; Precision@5 de m06 passa de 0,8 para 1.
- Build, smoke e E2E da interface aprovada passaram; capturas desktop/mobile foram inspecionadas. Processos locais já existentes preservados; API confirmou v7, readiness e quatro consultas positivas/negativas. O E2E iniciou uma instância nova com SQLite temporário.
- Persistem aviso Starlette/httpx, ausência de revisão humana/conjunto reservado e gates online/PostgreSQL/CI abertos. Execuções de testes exigiram permissão para temporários e subprocessos do Windows.
- A árvore frontend recebe alterações de componentes 21st.dev de outra sessão, preservadas sem validação neste trabalho. O estado continua mudando; conferir diff/dependências/testes e consultar `docs/HANDOFF_MAESTRI.md` local, se presente.

### Próximos passos
- Para ranking, usar relatórios v7 como baseline; revisar b03/m06 e os cinco modos com avaliação humana, criar conjunto reservado e obter fontes específicas antes de ampliar instrumentos/subgêneros.
- Para a interface pausada, ler `docs/HANDOFF_MAESTRI.md` e revisar o diff antes de instalar dependências e concluir integração/testes/créditos. Não tratar os novos componentes como entregues.
- Continuar os gates de cobertura/termos de provedores, avaliação online real, PostgreSQL/pgvector e CI; não confundir sucesso offline com aprovação desses gates.

## 2026-10-01 — Componentes 21st.dev iniciados; pausa solicitada

### Implementado
- Analisados o registro de desenvolvimento, estado da implementação, contexto de produto/design e fluxos/testes da interface. Preservar o visual aprovado e ampliar os fluxos atuais foi a direção escolhida.
- Iniciados frontend em `http://127.0.0.1:5173` e API local em `http://127.0.0.1:8000` usando `start-local.ps1`, sem ativar o modo online.
- Autenticação 21st.dev confirmada com `API_KEY_21st` em `api/.env`, sem expor ou versionar a chave. Accordion (demo 1530) e Toggle Group (demo 252), ambos do shadcn, foram obtidos pelo endpoint MCP autenticado.
- Criados componentes de Accordion, Toggle Group, Skeleton e explicação compartilhada. **Integração incompleta:** não considerar esses recursos entregues.
- Criado `docs/HANDOFF_MAESTRI.md` com o estado exato, bloqueio de instalação e comandos para continuidade.

### Arquivos principais alterados
- `frontend/src/components/ui/accordion.tsx`
- `frontend/src/components/ui/toggle-group.tsx`
- `frontend/src/components/ui/skeleton.tsx`
- `frontend/src/components/ui/components.css`
- `frontend/src/components/Explanation.tsx`
- `frontend/src/main.tsx`
- `frontend/src/pages/Discovery.tsx`
- `docs/HANDOFF_MAESTRI.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Manter primitivas Radix dos componentes shadcn para semântica e navegação por teclado; adaptar estilos aos tokens existentes.
- Skeleton consultado na fonte pública MIT do shadcn; créditos/licença ainda precisam ser atualizados em `frontend/THIRD_PARTY_NOTICES.md`.
- Usadas as duas consultas gratuitas de código disponíveis no 21st. Cota informada pelo serviço: zero restantes até `2026-10-02T00:00:00Z`. Nenhum plano pago ou geração hospedada ativado.

### Estado atual
- Trabalho interrompido por pedido explícito do usuário, antes de instalar dependências, concluir integração ou executar testes/build.
- `npm install @radix-ui/react-accordion @radix-ui/react-toggle-group` falhou com `UNABLE_TO_VERIFY_LEAF_SIGNATURE`. Node v24.16.0 oferece `--use-system-ca`; tentativa com esse recurso ainda não realizada. Não desativar validação TLS.
- **Interface em estado intermediário:** `Discovery.tsx` já importa os novos componentes e removeu a função `Why`, mas ainda contém usos de `<Why>`. As dependências Radix ainda não foram instaladas. Build deve ser considerado quebrado até concluir a integração.
- `ReadWithMusic.tsx`, testes e créditos ainda não receberam as alterações planejadas. Nenhum teste/build executado nesta etapa; nenhum commit realizado porque a implementação está incompleta e não validada.
- Scripts temporários e respostas do 21st estão em `.impeccable/`, ignorada pelo Git; não são dependências do produto.
- Ao encerrar, surgiram alterações adicionais de backend/testes e relatórios v7 no mesmo checkout, não produzidas nem revisadas nesta sessão. Lista e orientação de preservação em `docs/HANDOFF_MAESTRI.md`; reconciliar antes de commitar. API pronta e frontend HTTP 200 confirmados, sem validar a interface parcial.

### Próximos passos
- Ler `docs/HANDOFF_MAESTRI.md`; instalar as dependências usando a confiança de certificados do sistema.
- Revisar e executar uma única vez `.impeccable/integrate-components.py` (preparado, ainda não executado), ou completar manualmente a integração equivalente.
- Atualizar testes para filtros Radix e explicações em músicas/livros/trilhas; validar retry, cancelamento, preferências aplicadas e movimento reduzido.
- Atualizar créditos, executar testes frontend/backend e build, revisar desktop/mobile/temas, atualizar documentação e fazer commit local apenas após aprovação dos checks. Não fazer push.

## 2026-10-01 — Ponto de retomada para outro terminal

### Implementado
- Consolidado o histórico, decisões visuais aprovadas, estado do Git, execução local e sequência de retomada em `docs/CONTINUATION.md`, a pedido do usuário.
- Distinguida a última etapa validada (v6, `b698eb3`) do salvamento incompleto de piano/detetive (v7, `39a7395`). Nenhuma alteração de código nesta etapa documental.

### Arquivos principais alterados
- `docs/CONTINUATION.md`
- `docs/DEVELOPMENT_LOG.md`
- `docs/IMPLEMENTATION_STATUS.md`

### Decisões técnicas
- Preservar o commit incompleto existente e registrar as pendências, sem apresentar v7 como aceito nem continuar sua implementação durante a transferência.
- Registrar fontes já pesquisadas e comandos reproduzíveis; artefatos ignorados de `.impeccable/` não substituem relatórios versionados.

### Estado atual
- Branch `main`, árvore limpa antes deste registro. Interface respondeu HTTP 200 em `http://127.0.0.1:5173/`; API local respondeu v7 e readiness saudável.
- Nova execução da suíte: 191 testes aprovados e uma falha em `test_health_version_and_readiness_are_honest`, cuja expectativa ainda é v6. A primeira tentativa teve bloqueio de temporários; a repetição com permissão adequada isolou a falha real.
- Ruff check aprovado; catálogo local precisa de formatação. Fontes ainda não formalizadas no arquivo `docs/catalog-metadata.md` citado pelo código.
- Visual/animações já entregues e aprovados; testes frontend/build anteriores aprovados, não repetidos nesta etapa documental.

### Próximos passos
- No novo terminal, ler `docs/CONTINUATION.md` e conferir novamente Git/processos locais.
- Concluir proveniência e testes de piano/detetive, validar K=5/10 contra v6, atualizar relatórios/documentação e só então aceitar v7 em novo commit local.
- Preservar o visual aprovado e manter abertos os gates de revisão humana, integrações, infraestrutura e CI.

## 2026-09-30 — Gêneros explícitos no desempate de livros locais

### Implementado
- Diagnosticadas as consultas de detetive, romance introspectivo e piano, separando interpretação, ordenação e cobertura do catálogo.
- Ranking `local-rules-v6`: livros com igual relevância favorecem os gêneros explicitamente pedidos antes do desempate por título; critério visível na interpretação, scores e explicação.
- Registrados relatórios K=5/10 com comparação estrita e proteção contra perdas por caso no baseline v6.

### Arquivos principais alterados
- `api/app/services/recommendation_service.py`, `api/tests/test_recommendations.py`, `api/tests/test_books.py`, `api/tests/test_evaluation.py`
- `api/README.md`, `docs/05-API-Specification.md`, `docs/IMPLEMENTATION_STATUS.md`
- `docs/eval-reports/2026-09-30-explicit-book-genres.md`
- `docs/eval-reports/local-v6-genres-k5.json`, `docs/eval-reports/local-v6-genres-k10.json`

### Decisões técnicas
- Gêneros herdados de referências não recebem prioridade extra. Contexto, exclusões e limite de autor continuam prevalecendo.
- Nenhuma alteração de catálogo/corpus, chamada externa ou mudança no ranking musical, de leitura ou online.

### Estado atual
- 192 testes da API, Ruff e formatação aprovados. Nenhuma regressão por caso ou agregada contra v5 em K=5/10.
- Romance introspectivo traz Jane Eyre e Orgulho e Preconceito primeiro; P@5 passa de 0,2 para 0,4. nDCG de livros melhora nos dois K.
- Detetive ainda é interpretado apenas como mistério; piano não é reconhecido nem consta dos metadados. Gates e revisão humana permanecem abertos.

### Próximos passos
- Obter proveniência de instrumentos/subgêneros das obras existentes antes de enriquecer as classificações locais.
- Experimentar interpretação de piano/detetive e medir impactos por caso contra v6, sem alterar julgamentos v1.
- Preservar o visual aprovado; atualizar a instância local após mudanças do backend.

## 2026-09-30 — Comparação de avaliações por consulta

### Implementado
- CLI exibe casos alterados, títulos antes/depois, deltas e contagem de consultas com perda, inclusive quando a média não regride.
- `--fail-on-case-regression` oferece gate estrito opcional; o padrão continua usando agregados por módulo/modo.
- Validação de compatibilidade dos relatórios e proteção contra saída sobre o dataset/baseline.

### Arquivos principais alterados
- `api/app/evaluation/runner.py`, `api/tests/test_evaluation.py`, `api/README.md`
- `docs/eval-reports/2026-09-30-case-comparison.md`, `docs/IMPLEMENTATION_STATUS.md`

### Decisões técnicas
- Comparar por ID, não posição da linha; manter tolerância de 0,000001 e sinalizar mudanças de catálogo.
- Não modificar ranking, julgamentos nem baselines aceitos nesta etapa.

### Estado atual
- 186 testes da API aprovados; Ruff e formatação aprovados. Persiste aviso de depreciação Starlette/httpx.
- CLI real confirma zero perdas agregadas v4→v5 em K=5/10, mas uma consulta com perda em K=5 e duas em K=10; modo estrito retorna 1 como esperado.
- Repaginação/animações concluídas no commit local `5b40091`; documentação visual e licenças incluídas.

### Próximos passos
- Inspecionar interpretação e candidatos de mistério/detetive, romance introspectivo e piano antes de alterar regras.
- Comparar qualquer experimento com v5 e registrar todas as perdas por consulta; manter corpus intacto.
- Revisão humana, modo online e gates externos seguem pendentes.

## 2026-09-30 — Descoberta imersiva com capas e animações acessíveis

### Implementado
- Repaginação aprovada pelo usuário, preservando identidade ametista, temas e os três fluxos públicos.
- Carrossel de capas com botões, teclado e arraste, ligado à trilha do livro; escolhas animadas e sugestões acionáveis na Home.
- Entradas discretas dos conteúdos e feedback de interação, respeitando movimento reduzido e sem avanço automático.
- Fontes e capas servidas localmente; créditos dos componentes disponíveis no 21st.dev e licenças das fontes incluídos.
- Capas de apoio restritas a resultados do provedor local, sem atribuição a homônimos externos.

### Arquivos principais alterados
- `frontend/src/pages/Home.tsx`, `frontend/src/pages/Discovery.tsx`
- `frontend/src/components/ui/animated-tabs.tsx`, `frontend/src/components/ui/three-d-carousel.tsx`
- `frontend/src/lib/showcase.ts`, `frontend/src/showcase.css`, `frontend/src/styles.css`, `frontend/src/main.tsx`
- `frontend/package.json`, `frontend/package-lock.json`, `frontend/index.html`, `frontend/tests/smoke.mjs`
- `frontend/public/images/covers/`, `frontend/public/licenses/`, `frontend/THIRD_PARTY_NOTICES.md`
- `PRODUCT.md`, `DESIGN.md`, `.impeccable/design.json`, `docs/IMPLEMENTATION_STATUS.md`

### Decisões técnicas
- Adaptados Animated Tabs de Chetan Verma e 3D Carousel do Cult UI a partir das fontes públicas MIT; CLI do 21st exige autenticação ausente.
- Motion controla transições; fontes via Fontsource eliminam a dependência de Google Fonts em tempo de execução.
- Mantida a composição aprovada após correção visual; sem reprodução de áudio ou recomendação personalizada fictícia.

### Estado atual
- `npm test` e `npm run build` aprovados: smoke e E2E com FastAPI/SQLite reais, incluindo filtros, explicações, erro, vazio e mobile.
- Revisão visual direta de desktop/mobile e tema claro; subagente revisor interrompido por limite de uso, sem parecer independente concluído.
- Capas são de edições em inglês e mantêm direitos de seus titulares. Catálogo local e integrações online continuam com os limites documentados.

### Próximos passos
- Concluir e testar `compare_reports` e o modo estrito da CLI de avaliação em `api/app/evaluation/runner.py`; alteração pendente fora do commit visual.
- Diagnosticar consultas com baixa precisão usando comparação por caso, preservando corpus e baselines aceitos.

## 2026-09-30 — Modo Cinematográfico com desempate e diversidade

### Implementado
- CINEMATIC local desempata por artistas menos repetidos, etiqueta cinematográfica e título, sempre após relevância contextual; ranking `local-rules-v5`.
- Critério exposto no score de modo e na explicação, com testes sintéticos e pela API em três livros.
- Relatórios v5 em K=5/10 e proteção contra regressões dos resultados aceitos, preservando corpus, catálogo e baselines anteriores.

### Arquivos principais alterados
- `api/app/services/recommendation_service.py`
- `api/tests/test_recommendations.py`
- `api/tests/test_books.py`
- `api/tests/test_evaluation.py`
- `docs/05-API-Specification.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/eval-reports/2026-09-30-cinematic-tiebreak.md`
- `docs/eval-reports/local-v5-cinematic-k5.json`
- `docs/eval-reports/local-v5-cinematic-k10.json`

### Decisões técnicas
- Descartada variante que favorecia a etiqueta sem considerar variedade de artistas por regredir diversidade em K=10.
- Mudança restrita a leitura local CINEMATIC; nenhuma dependência, chamada externa ou exigência de energia alta.

### Estado atual
- 157 testes da API aprovados; Ruff e formatação aprovados. Sem regressões agregadas contra v3/v4 nos dois valores de K.
- CINEMATIC Precision@10: 0,466667 → 0,500000; nDCG@10: 0,876961 → 0,921324. Perda individual em Duna@5 documentada; corpus não é avaliação humana nem conjunto reservado.

### Próximos passos
- Expor comparação por consulta na CLI para tornar visíveis perdas escondidas por médias; manter a política agregada explícita.
- Diagnosticar baixa precisão em mistério de detetive, romance introspectivo e pedidos de piano antes de alterar regras/catálogo.
- Manter gates externos e revisão humana pendentes; não avançar para personalização com base apenas nesses experimentos locais.

## 2026-09-30 — Validação e fechamento da etapa Calma

### Implementado
- Revisada a alteração pendente do modo Calma e confirmada sua avaliação antes do commit local.
- Atualizada a matriz de implementação para refletir o ranking v4 e a diferenciação já entregue.

### Arquivos principais alterados
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Preservar código, julgamentos e relatórios da etapa anterior; concluir sua unidade lógica antes de iniciar CINEMATIC.

### Estado atual
- 152 testes da API aprovados; Ruff e verificação de formatação aprovados em 2026-09-30.
- Permanece o aviso de depreciação Starlette/httpx.

### Próximos passos
- Experimentar desempate CINEMATIC por etiqueta cinematográfica; comparar com v3 e v4 em K=5/10 sem modificar o corpus.

## 2026-09-29 — Modo Calma diferenciado com avaliação sem regressões

### Implementado
- Leitura local em CALM desempata candidatos pela preferência atmosférica e menor preferência cinematográfica, preservando prioridade de livro/contexto, filtros e diversidade.
- Critério exposto em `scores.reading_mode` e explicações; ranking versionado como `local-rules-v4`.
- Testes pela API demonstram ordens diferentes entre FOCUS/CALM com os mesmos filtros em Duna, O Hobbit e O Jardim Secreto. Cenário sintético garante que contexto maior vence o desempate.
- Registrados relatórios v4 e comparação também contra eles, preservando os baselines e julgamentos originais.

### Arquivos principais alterados
- `api/app/services/recommendation_service.py`
- `api/tests/test_recommendations.py`
- `api/tests/test_books.py`
- `api/tests/test_evaluation.py`
- `docs/eval-reports/local-v4-calm-k5.json`
- `docs/eval-reports/local-v4-calm-k10.json`
- `docs/eval-reports/2026-09-29-calm-tiebreak.md`
- `docs/05-API-Specification.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Usar desempate editorial explicável, sem mapear títulos/IDs do corpus nem substituir relevância contextual por uma preferência de modo.
- Alteração restrita ao caminho local de leitura; o modo online experimental exige avaliação própria.
- Manter dados e baselines v3 imutáveis. Experimento aceito por não apresentar regressões por módulo/modo em K=5 ou K=10.

### Estado atual
- 152 testes da API passaram; Ruff e formatação aprovados.
- CALM P@5 passou de 0,8000 para 0,9333 e nDCG@5 de 0,9207 para 0,9797. Leitura agregada P@5: 0,8267; os demais módulos preservam métricas.
- Diferenciação demonstrada em três livros, sem garantia de listas distintas para qualquer catálogo. Não fecha G4 nem valida preferências humanas.

### Próximos passos
- Experimentar preferência CINEMATIC ancorada em etiquetas e explicações, preservando prioridade de contexto e comparando v3/v4 nos dois valores de K.
- Depois revisar baixa precisão em mistério de detetive, romance introspectivo e pedidos de piano, sem modificar julgamentos para favorecer o ranking.
- Manter pendentes avaliação humana, modo online e gates externos antes de ampliar integrações/personalização.

## 2026-09-29 — Reconciliação da documentação com o modo online

### Implementado
- Criada matriz de implementação e gates, separando modo local, online experimental e desenho futuro.
- Atualizados guias de execução, roadmap, índice de ADRs e notas nas arquiteturas de IA/recomendação.
- Registrada a divergência entre ADR-0002 e seleção pontuada por Groq; MusicBrainz permanece experimental e G1 aberto.

### Arquivos principais alterados
- `README.md`
- `api/README.md`
- `docs/IMPLEMENTATION_STATUS.md`
- `docs/06-ai-architecture.md`
- `docs/07-recommendation-engine-specification.md`
- `docs/12-development-roadmap.md`
- `docs/adr/README.md`
- `docs/adr/0002-llm-interprets-backend-ranks.md`
- `docs/adr/0012-music-provider-selection.md`
- `docs/adr/0013-free-local-mode.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Preservar decisões arquiteturais como alvo, registrando divergências em vez de apresentar integração experimental como cumprimento dos gates.
- Não afirmar gratuidade garantida de contas externas: o limite de chamadas do backend não controla faturamento. Nenhuma integração foi ativada nesta etapa.
- Evidências históricas de providers permanecem datadas; não houve consulta externa nem nova validação de termos/licenças.

### Estado atual
- Documentação revisada contra código de inicialização, configuração, providers, cache, IA e endpoints. Baseline e testes permanecem os da etapa anterior; não houve mudança de comportamento.
- README/guia da API ainda contêm trechos legados com acentuação corrompida; notas iniciais e matriz atual orientam o contrato efetivo.

### Próximos passos
- Implementar critérios distintos para FOCUS/CALM/CINEMATIC e registrar experimento sem alterar os baselines `local-v3-baseline-k5.json` e `local-v3-baseline-k10.json`.
- Exigir que a comparação automática não indique regressões por módulo ou modo; ampliar teste de diferenciação sem otimizar julgamentos para os resultados.
- Depois revisar consultas de baixa precisão/cobertura; manter G1/G2 e avaliação humana como pendências antes de expandir integrações/personalização.

## 2026-09-29 — Avaliação offline e baseline de relevância

### Implementado
- Dataset editorial versionado com 45 consultas: 15 por módulo, cobrindo os cinco modos de leitura.
- CLI offline para Precision@K, nDCG@K, diversidade, preenchimento, cobertura, existência no catálogo e satisfação de restrições; relatórios reproduzíveis em K=5 e K=10.
- Comparação de regressões por módulo e modo de leitura, integrada ao pytest. Hashes do dataset/catálogo e versão das métricas identificam o experimento.

### Arquivos principais alterados
- `api/app/evaluation/__init__.py`
- `api/app/evaluation/metrics.py`
- `api/app/evaluation/runner.py`
- `api/evaluation/local-golden-v1.json`
- `api/tests/test_evaluation.py`
- `docs/eval-reports/local-v3-baseline-k5.json`
- `docs/eval-reports/local-v3-baseline-k10.json`
- `docs/eval-reports/2026-09-29-local-baseline.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Julgamentos são separados do ranking, mas produzidos editorialmente pelo assistente; não representam avaliação humana independente ou teste reservado.
- Baselines são imutáveis para comparação; alterações de dataset exigem nova versão. K e hash diferentes não são comparáveis automaticamente.
- Não ajustar ranking nesta etapa: registrar primeiro os limites existentes. Nenhuma chamada externa ou dependência nova.

### Estado atual
- 148 testes da API passaram; seis testes de avaliação verificam métricas, dados inválidos, reprodutibilidade sem rede e regressões. Ruff e formatação aprovados.
- P@5: música 0,6933, livros 0,6533, leitura 0,8000. Restrições e IDs do catálogo avaliados: 100%.
- FOCUS/CALM retornaram listas idênticas nos três livros; CINEMATIC teve menor precisão entre modos. Catálogo limita cobertura em K=10. Relatório detalha limites; gates do motor completo permanecem abertos.

### Próximos passos
- Reconciliar roadmap, especificação do motor e ADRs com o código online existente antes de ampliar integrações.
- Após essa reconciliação, experimentar diferenciação FOCUS/CALM/CINEMATIC, preservando baselines e comparando ambos os valores de K.
- Revisar casos de baixa precisão e submeter julgamentos a revisão humana antes de prometer qualidade geral.

## 2026-09-29 — Referências por título no ranking local e online

### Implementado
- Resolvedor compartilhado de títulos com palavras completas, normalização de acentos/caixa, aliases locais e preferência pelo título mais longo em sobreposições.
- Títulos negados removem a própria obra sem acrescentar seus temas; palavras dentro de títulos reconhecidos são mascaradas antes do parser determinístico de temas.
- Referências são removidas também quando a seleção online falha e usa ranking por regras; referências inventadas pela IA não bloqueiam candidatos.
- Adicionado `parsed_query.excluded_references` e atualizado ranking local para `local-rules-v3`.

### Arquivos principais alterados
- `api/app/services/references.py`
- `api/app/services/recommendation_service.py`
- `api/app/services/online_recommendations.py`
- `api/tests/test_references.py`
- `api/tests/test_online.py`
- `api/tests/test_books.py`
- `docs/05-API-Specification.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- A confirmação de referência depende de texto e catálogo, não exclusivamente da interpretação da IA. Homônimos recuperados são bloqueados por título; desambiguação por autoria permanece futura.
- IDs externos só são aliases no catálogo editorial local, onde representam títulos originais; IDs Open Library não são títulos.
- O fallback recalcula temas após conhecer os títulos externos, evitando transformar `sem External Fantasy` em exclusão do gênero fantasia.

### Estado atual
- 142 testes passaram, incluindo 23 novos casos de referências; Ruff e formatação aprovados. Mantido o aviso de depreciação Starlette/httpx.
- Não há consulta externa por título para resolver referências ausentes dos candidatos. Vocabulário de negação continua limitado, sem compreensão semântica geral.

### Próximos passos
- Construir dataset editorial de relevância com pelo menos 15 consultas por módulo, incluindo os cinco modos de leitura; implementar avaliação reproduzível de Precision@K, nDCG, existência e diversidade.
- Registrar o baseline antes de ajustar pesos; manter julgamentos separados do ranking e documentar limitações de cobertura do catálogo.
- Reconciliar roadmap, especificação do motor e ADRs com o modo online após registrar o baseline.

## 2026-09-29 — Filtros musicais consistentes entre modo local e online

### Implementado
- Corrigidas consultas como `não quero instrumental` e `sem energia alta`; adicionados reconhecimento de energia média e aliases de voz/letras.
- Criado resolvedor compartilhado de filtros e predicado aplicado ao ranking local, à seleção da IA e ao fallback online.
- Adicionado `filters.excluded_energy`, com validação de níveis e conflitos. Filtros explícitos prevalecem por dimensão; conflitos textuais não resolvidos retornam 422 antes de chamadas externas.
- Energia desconhecida é descartada quando há exclusões; `parsed_query` reflete os filtros efetivos, sem manter a energia originalmente sugerida pela IA quando foi substituída.
- Atualizada versão do ranking local para `local-rules-v2`; documentado contrato atual separadamente dos exemplos planejados no roadmap.

### Arquivos principais alterados
- `api/app/services/music_filters.py`
- `api/app/services/recommendation_service.py`
- `api/app/services/online_recommendations.py`
- `api/app/schemas/recommendation.py`
- `api/app/routes/recommendations.py`
- `api/tests/test_music_filters.py`
- `api/tests/test_recommendations.py`
- `api/tests/test_online.py`
- `api/tests/test_books.py`
- `docs/05-API-Specification.md`
- `docs/eval-reports/2026-09-29-music-filters.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Excluir um nível de energia permite os outros níveis, sem inferir arbitrariamente um único valor oposto.
- `energy` explícito não nulo ou presença de `excluded_energy` substitui as restrições textuais dessa dimensão; lista vazia permite limpá-las. Voz é resolvida independentemente.
- Nenhuma nova dependência, migração ou serviço pago. Providers/IA foram testados com transporte simulado.
- As regras dos modos de leitura permanecem próprias. Comparativos, dupla negação e listas abreviadas não fazem parte do vocabulário garantido do novo parser.

### Estado atual
- 119 testes da API passaram, incluindo 46 novos casos. Ruff e formatação aprovados.
- Smoke/E2E com API real, SQLite e navegação offline passaram; build do frontend aprovado.
- Permanece um aviso de depreciação da integração Starlette/httpx. Qualidade das classificações reais da IA e PostgreSQL não foram avaliados nesta etapa.

### Próximos passos
- Avaliar referências por título: correspondência por palavras completas, títulos negados e diferenças entre seleção da IA e fallback em `api/app/services/online_recommendations.py`.
- Criar julgamentos independentes de relevância para pelo menos 15 consultas por módulo e medir Precision@K/nDCG e diversidade, incluindo os cinco modos de leitura.
- Reconciliar os demais exemplos planejados da especificação e ADRs com o modo online antes de ampliar integrações; manter o modo local gratuito.

## 2026-09-29 — Exclusões coordenadas no parser de recomendações

### Implementado
- Corrigida a interpretação de listas como `sem romance, terror e política`: todos os temas são excluídos.
- Pontuação forte, quebras de linha, adversativas e retomadas explícitas de preferência delimitam a propagação da exclusão.
- Adicionado corpus de 24 consultas e duas verificações de ranking/explicações sem rede; registrado relatório com escopo e limitações.
- Corrigida captura de variável de loop apontada pelo Ruff em um teste online existente.

### Arquivos principais alterados
- `api/app/services/recommendation_service.py`
- `api/tests/test_intent_rules.py`
- `api/tests/test_online.py`
- `docs/eval-reports/2026-09-29-local-intent.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Processar temas na ordem textual e preservar limites de frases antes de normalizar a consulta; propagar negação somente em listas coordenadas.
- Manter o parser determinístico compartilhado pelos modos local e online, sem dependências ou chamadas externas adicionais.
- Preservar a precedência de exclusões e a interpretação conservadora de `pouco`/`menos`; o corpus não equivale ao golden set completo do roadmap.

### Estado atual
- Corpus e ranking passaram; a suíte da API passou com 73 testes. Há um aviso de depreciação da integração Starlette/httpx.
- O código já contém integração online Groq/MusicBrainz/Open Library adicionada no commit `7916989`, posterior ao registro anterior. Esta etapa valida seus testes com fakes, sem chamadas reais ou revisão completa dessa integração.
- Não foram implementados histórico pessoal, feedback, salvos ou interface de conta nesta etapa.

### Próximos passos
- Ampliar o corpus em `api/tests/test_intent_rules.py` para referências e filtros de voz/energia; avaliar negações desses filtros separadamente dos temas.
- Criar julgamentos de relevância para pelo menos 15 consultas por módulo e medir Precision@K/nDCG e diversidade, conforme `docs/12-development-roadmap.md`.
- Reconciliar documentação e ADRs do modo online com `7916989` antes de ampliar essa integração; preservar o modo local gratuito.

## 2026-09-28 — Fluxos públicos funcionais em modo local gratuito

### Implementado
- Implementados os três endpoints usados pela interface: descoberta de músicas, descoberta de livros e trilha de leitura, com explicações dos critérios reais.
- Catálogo de 18 livros e 25 músicas, busca de título/autor, ranking por temas, referências, exclusões simples, filtros de voz/energia e diversidade por criador. Nenhuma chamada a LLM ou serviço pago.
- `api/local.py` aplica migrações SQLite e mantém banco/segredo em `api/.local`; `start-local.ps1` inicia API e frontend, verifica portas/prontidão e oferece instalação explícita de dependências gratuitas.
- Readiness valida todas as tabelas e aceita SQLite sem pgvector. Open Library/PostgreSQL continuam opcionais.
- Interface informa catálogo local e duração estimada. Links musicais são buscas externas, sem áudio ou duração de gravação inventados.
- Testes de recomendações sem rede, filtros, exclusões, expiração, validação e persistência após reinício; E2E com API real, SQLite temporário e recursos externos do navegador bloqueados.

### Arquivos principais alterados
- `api/app/providers/local_catalog.py`
- `api/app/services/recommendation_service.py`
- `api/app/schemas/recommendation.py`
- `api/app/routes/recommendations.py`
- `api/app/services/book_service.py`
- `api/app/routes/books.py`
- `api/app/core/config.py`
- `api/app/main.py`
- `api/local.py`
- `api/.env.example`
- `api/.gitignore`
- `api/tests/test_recommendations.py`
- `api/tests/test_local.py`
- `api/tests/test_books.py`
- `api/tests/test_migrations.py`
- `frontend/src/lib/api.ts`
- `frontend/src/pages/Discovery.tsx`
- `frontend/src/pages/ReadWithMusic.tsx`
- `frontend/tests/live.mjs`
- `frontend/package.json`
- `start-local.ps1`
- `README.md`
- `api/README.md`
- `docs/adr/0013-free-local-mode.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Modalidade local sem Docker, chaves externas, embeddings ou LLM, conforme a restrição de custo. Catálogo editorial limitado, sem prometer interpretação semântica avançada.
- Iniciador isola banco/provider de configurações externas; dados/segredo são ignorados pelo Git. Migrações usam conexão explícita para não atingir `DATABASE_URL` externo.
- Resultados anônimos ficam em memória por uma hora, até 256 buscas por processo; explicações usam o resultado armazenado.
- Trilhas estimam cinco minutos por faixa, não repetem itens para completar duração e avisam quando a seleção fica curta. “Poucos vocais” usa instrumentais conservadoramente.

### Estado atual
- 34 testes de backend, smoke/E2E do frontend com API real e build passaram. Verificação visual desktop/celular sem overflow; detector da skill de interface sem achados nas alterações.
- Iniciador completo verificado: frontend em `127.0.0.1:5173`, API em `127.0.0.1:8000`, readiness 200 e CORS correto. A checagem de portas respeita uma instância existente em IPv6 sem bloqueá-la ou encerrá-la.
- Os três fluxos públicos funcionam sem rede após instalação. Auth funciona na API com persistência, sem tela de conta. Histórico pessoal, feedback, salvos, reprodução/exportação de playlists e deploy público continuam pendentes.
- PostgreSQL/pgvector e concorrência de refresh entre processos permanecem sem validação real. Links de terceiros exigem conexão, mas não são necessários para gerar sugestões.

### Próximos passos
- Expandir `api/app/providers/local_catalog.py` e criar consultas de avaliação de relevância, exclusões e cobertura do parser antes de prometer compreensão mais ampla.
- Para ampliar catálogo pela rede, concluir ADR-0012 e validar provider sem contratar serviços; preservar modo offline e testes sem rede.
- Para personalização, integrar auth à interface e persistir recomendações/feedback com isolamento por usuário, migrações e testes antes de expor histórico ou salvos.
- Antes de deploy, validar PostgreSQL real, migrações reversas, concorrência de refresh e rate limiting compartilhado; configuração local não é destinada a múltiplas instâncias públicas.

## 2026-09-28 — Cache persistente de busca externa de livros

### Implementado
- Criada a migração `0004_external_search_cache` com chave por tipo, provider, consulta normalizada e limite, resposta JSON e expiração em milissegundos Unix.
- A busca de livros reutiliza respostas válidas entre reinícios da API quando há banco configurado. Novas buscas persistem catálogo e cache na mesma transação; entradas vencidas são removidas nas gravações. Sem banco, o cache em memória continua ativo.
- Testes cobrem reutilização após reinício, separação por limite, resposta vazia, expiração, upgrade/downgrade SQLite e geração SQL PostgreSQL.
- Iniciada a avaliação do provider musical no ADR-0012 com documentação oficial e uma pequena amostra real da API MusicBrainz.

### Arquivos principais alterados
- `api/alembic/versions/0004_external_search_cache.py`
- `api/app/models/external_search_cache.py`
- `api/app/models/__init__.py`
- `api/app/providers/base.py`
- `api/app/services/book_service.py`
- `api/tests/test_books.py`
- `api/tests/test_migrations.py`
- `api/README.md`
- `docs/04-Data-Model.md`
- `docs/05-API-Specification.md`
- `docs/12-development-roadmap.md`
- `docs/adr/0012-music-provider-selection.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- A tabela suporta múltiplos tipos de entidade, mas a integração atual é só de livros. O TTL é o mesmo do cache em memória (`BOOK_SEARCH_CACHE_TTL_SECONDS`); valor zero desabilita ambos.
- Respostas normalizadas são armazenadas após o upsert do catálogo na mesma transação. O cache persistente evita novas chamadas ao provider e não prolonga sua validade ao ser lido.
- O MusicBrainz ainda não foi escolhido como fonte definitiva: a amostra mostrou campos de duração e tags incompletos, e falta comparar Last.fm com chave e avaliar licenças e cobertura para G1.

### Estado atual
- A busca de livros funciona com cache persistente em banco migrado e com cache em memória sem banco. Os testes em SQLite, lint e formatação passam.
- O caminho PostgreSQL/pgvector e a concorrência entre processos não foram validados neste ambiente. O provider musical permanece em avaliação, sem endpoints musicais implementados.

### Próximos passos
- Em ambiente com Docker, rodar `alembic upgrade head` e `downgrade base` em PostgreSQL com pgvector descartável; testar reutilização e expiração do cache com duas instâncias da API.
- Completar a matriz do ADR-0012: obter chave de desenvolvimento Last.fm, medir amostra de estilos variados, cobertura de tags/gêneros/duração e latência, e confirmar obrigações de licença/atribuição para os campos usados.
- Após fechar G1, implementar `MusicProvider`, catálogo de músicas e `GET /music/search`/`GET /music/{id}` com normalização e testes de contrato.

## 2026-09-28 — Metadados de descrição e assuntos na busca de livros

### Implementado
- A busca Open Library solicita descrição e assuntos junto dos campos bibliográficos e normaliza esses dados no `BookItem`.
- Descrições são limitadas a 2.000 caracteres; até 12 assuntos únicos são mantidos, com até 120 caracteres cada. O catálogo existente persiste esses campos e o detalhe por ID os devolve.
- Testes cobrem o contrato do provider, limites de tamanho e leitura dos metadados persistidos.

### Arquivos principais alterados
- `api/app/providers/open_library.py`
- `api/tests/test_books.py`
- `api/README.md`
- `docs/05-API-Specification.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- Os campos são obtidos na mesma chamada de busca, evitando consultas adicionais por obra. Valores ausentes ou inválidos permanecem vazios; `genres` não é inferido a partir de assuntos.
- Os limites de tamanho controlam o volume de resposta e de dados armazenados. O cache de consultas externas continua em memória por processo.

### Estado atual
- Busca e detalhe retornam descrição e assuntos quando a Open Library os fornece. `pytest` passou com 19 testes; Ruff e formatação passaram.
- Docker Engine continua indisponível neste ambiente; a migração e a persistência em PostgreSQL com pgvector ainda não foram validadas.

### Próximos passos
- Em ambiente com Docker, subir `api/compose.yaml`, executar `alembic upgrade head` e `downgrade base` em banco descartável e validar busca e detalhe no PostgreSQL.
- Avaliar cache persistente com TTL para consultas externas e medir a latência da busca com os novos campos em uma consulta real.
- Prosseguir com o spike e a implementação do provider musical conforme `docs/adr/0012-music-provider-selection.md`, incluindo normalização, cache e endpoints de busca musical.

## 2026-09-28 — Catálogo persistente de livros

### Implementado
- Criada a migração Alembic `0003_books_catalog` e o modelo `Book`, com unicidade por provider/ID externo e índice por título.
- A busca Open Library persiste ou atualiza os itens no catálogo quando PostgreSQL/SQLite estiver configurado; sem banco, a busca continua disponível sem persistência.
- Implementado `GET /api/v1/books/{id}` para consultar livros já catalogados, com 404 para IDs ausentes e 503 quando o catálogo não está configurado ou acessível.

### Arquivos principais alterados
- `api/alembic/versions/0003_books_catalog.py`
- `api/app/models/book.py`
- `api/app/models/__init__.py`
- `api/app/models/account.py`
- `api/app/services/book_service.py`
- `api/app/routes/books.py`
- `api/app/main.py`
- `api/tests/test_books.py`
- `api/tests/test_migrations.py`
- `api/README.md`
- `docs/04-Data-Model.md`
- `docs/05-API-Specification.md`
- `docs/DEVELOPMENT_LOG.md`
- `docs/12-development-roadmap.md`

### Decisões técnicas
- A chave única é `(provider, external_id)`; upsert nativo de PostgreSQL/SQLite deixa as atualizações idempotentes e o ID público determinístico da Open Library é preservado.
- A persistência síncrona usa o pool de threads do Starlette para não bloquear o event loop da rota assíncrona.
- O detalhe lê somente do catálogo local. Não chama provider por ID porque essa operação ainda não faz parte do contrato de `BookProvider`.
- Descrição, gêneros e assuntos ficam preparados no schema para enriquecimento futuro; o provider atual ainda não preenche esses campos.

### Estado atual
- Busca e detalhe são cobertos com migração e SQLite; `pytest` passou com 18 testes e Ruff/formatação passaram.
- PostgreSQL com pgvector ainda não foi executado neste ambiente por indisponibilidade do Docker Engine. A busca textual do catálogo e os índices GIN permanecem pendentes.

### Próximos passos
- Validar upgrade/downgrade da migração `0003` e persistência no PostgreSQL com pgvector em ambiente com Docker.
- Enriquecer o provider Open Library com descrição e assuntos de forma limitada, e avaliar cache persistente de consultas externas.
- Continuar Fase 2 do roadmap com provider musical, normalização e os endpoints de busca musical; em seguida avançar ao parser e ranking previstos nas Fases 3 e 4.

## 2026-09-28 — Autenticação da API com refresh rotativo

### Implementado
- Criadas as rotas `POST /api/v1/auth/register`, `/login`, `/refresh`, `/logout` e `GET /api/v1/auth/me` com validação de entrada e erros padronizados.
- Senhas usam Argon2id; access tokens usam JWT HS256 de 15 minutos; refresh tokens opacos de 7 dias são armazenados como hash SHA-256, rotacionados a cada uso e revogados por família quando há reuso.
- Adicionado limite em memória por IP/rota e por e-mail em login/registro. Testes cobrem cadastro, login genérico, expiração e adulteração do JWT, rotação, reuso, logout, ownership e `429`.
- Alinhados contrato de entrega dos tokens e decisões de segurança no ADR-0006 e nas especificações de API e segurança.

### Arquivos principais alterados
- `api/app/routes/auth.py`
- `api/app/services/auth_service.py`
- `api/app/core/security.py`
- `api/app/core/rate_limit.py`
- `api/app/core/config.py`
- `api/app/schemas/auth.py`
- `api/app/main.py`
- `api/tests/test_auth.py`
- `api/pyproject.toml`
- `api/.env.example`
- `api/README.md`
- `docs/adr/0006-jwt-authentication-strategy.md`
- `docs/05-API-Specification.md`
- `docs/09-security-specification.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- O cliente recebe access e refresh tokens em JSON e os mantém somente em memória. Cookie `HttpOnly` exige definição futura de domínios e CSRF; recarregar a página encerra a sessão atual.
- `JWT_SECRET` de pelo menos 32 bytes é exigido ao usar auth. Sem ele, essas rotas respondem `503`, preservando a busca pública de livros.
- A rotação bloqueia a linha do token no banco; o limitador atual é local ao processo. Ambos precisam de validação ou substituição adequada antes de escalar a API.

### Estado atual
- Os testes de API passam em SQLite com migrações Alembic e transporte HTTP local. Registro, login, refresh, logout e consulta ao usuário estão implementados.
- O Docker Engine segue indisponível nesta máquina. Migrações, auth e concorrência de refresh ainda não foram testadas em PostgreSQL com pgvector. O frontend ainda não consome as rotas de auth e não mantém sessão.

### Próximos passos
- Em ambiente com Docker, iniciar `api/compose.yaml`, executar `alembic upgrade head` e validar fluxos de auth e refresh concorrente em PostgreSQL; testar `downgrade base` em banco descartável.
- Integrar registro/login/refresh/logout no frontend mantendo tokens em memória, incluindo estados de sessão expirada e uso de `/auth/me`.
- Prosseguir no backend com catálogo local persistido e `GET /books/{id}`; depois implementar os providers e endpoints de recomendações previstos no roadmap. Antes de escalar horizontalmente, migrar o rate limit de auth para armazenamento compartilhado.

## 2026-09-28 — Base relacional e migrações

### Implementado
- Adicionado Compose de PostgreSQL 18 com pgvector e configuração de conexão em `api/.env.example`.
- Criados modelos SQLAlchemy para usuários, refresh tokens, preferências, interações e histórico de busca, com Alembic para extensões e tabelas.
- `GET /health/ready` agora verifica conexão, schema e extensão pgvector.

### Arquivos principais alterados
- `api/compose.yaml`
- `api/alembic.ini`
- `api/alembic/env.py`
- `api/alembic/versions/0001_extensions.py`
- `api/alembic/versions/0002_accounts.py`
- `api/app/models/account.py`
- `api/app/database/session.py`
- `api/app/main.py`
- `api/app/core/config.py`
- `api/tests/test_migrations.py`
- `api/pyproject.toml`
- `api/README.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- As extensões `citext` e `vector` são habilitadas apenas em PostgreSQL; os mesmos scripts migram SQLite para testes locais.
- `recommendation_id` fica sem chave estrangeira até a tabela de recomendações existir. A integridade será adicionada na migração dessa etapa.
- O Compose usa uma imagem versionada do pgvector e porta local 5433 para não conflitar com o PostgreSQL já instalado nesta máquina.

### Estado atual
- Upgrade e downgrade do Alembic passam em SQLite; o Compose passa na validação de configuração.
- O Docker Engine não está disponível nesta máquina; o PostgreSQL local pede credenciais e não tem pgvector. A migração PostgreSQL ainda não foi executada aqui.
- A API de livros continua funcional sem banco. Readiness só responderá 200 após PostgreSQL, pgvector e schema estarem disponíveis.

### Próximos passos
- Implementar registro, login, refresh rotativo, logout e `GET /auth/me` sobre os novos modelos, com Argon2id e JWT HS256; testar expiração, reuso e revogação de família.
- Validar `alembic upgrade head` e `downgrade base` em um PostgreSQL com pgvector, por exemplo com `cd api; docker compose up -d db` onde o Docker Engine estiver disponível.
- Depois da autenticação, implementar rate limiting de auth e persistir cache/catálogo de livros.

## 2026-09-28 — Primeira fatia da API e busca de livros

### Implementado
- Criada a aplicação FastAPI em `api/`, com configuração tipada, CORS explícito, ID de requisição, erros padronizados e rotas de saúde e versão.
- Implementado `GET /api/v1/books/search` com provider Open Library, normalização de livros, limite de chamadas externas e cache curto em memória.
- Adicionados testes sem dependência de rede para rotas, validação, CORS, cache e contrato do provider.

### Arquivos principais alterados
- `api/app/main.py`
- `api/app/routes/books.py`
- `api/app/providers/open_library.py`
- `api/app/services/book_service.py`
- `api/app/schemas/book.py`
- `api/app/core/config.py`
- `api/tests/test_books.py`
- `api/pyproject.toml`
- `api/README.md`
- `frontend/README.md`
- `docs/03-System-Architecture.md`
- `docs/DEVELOPMENT_LOG.md`

### Decisões técnicas
- A raiz é `api/` por solicitação do projeto; a árvore de referência em `docs/03-System-Architecture.md` foi alinhada a esse caminho e às rotas em `app/routes/`.
- A busca usa o parâmetro `title` da Open Library porque o seletor do frontend recebe um título, e apenas obras válidas são normalizadas. IDs UUID são derivados de forma determinística do ID da obra; a persistência local virá depois.
- O cache e a limitação de uma chamada por segundo são locais ao processo e atendem apenas ao início do desenvolvimento. A Open Library recomenda identificação da aplicação e cache para uso frequente.
- `/health/ready` retorna 503 enquanto PostgreSQL/pgvector não estiver configurado, sem indicar prontidão inexistente.

### Estado atual
- A estrutura de API, os endpoints de saúde/versão e a busca de livros estão implementados. Os testes automatizados passaram com provider falso.
- Uma consulta real durante esta etapa excedeu o timeout de 5 segundos e retornou `504 UPSTREAM_TIMEOUT`; a disponibilidade da Open Library neste ambiente não foi confirmada.
- O frontend em `frontend/` já possui Home, descoberta e trilha de leitura com tema escuro padrão. A API ainda não oferece autenticação, recomendações nem geração de trilha; o seletor de livros é o único fluxo do frontend conectado a um endpoint implementado.

### Próximos passos
- Completar a Fase 1 de `docs/12-development-roadmap.md`: PostgreSQL + pgvector, Alembic/migração 0001, modelos iniciais, autenticação JWT com refresh rotativo e testes de migração/autenticação.
- Substituir o cache em memória por cache persistido com TTL e implementar `GET /books/{id}` sobre catálogo local. Verificar em ambiente com rede a latência e disponibilidade da Open Library e configurar contato no User-Agent.
- Seguir a Fase 2 com provider musical validado pelo ADR `docs/adr/0012-music-provider-selection.md`; depois implementar parser, ranking e os três endpoints `POST /recommendations/*` usados pelo frontend.
