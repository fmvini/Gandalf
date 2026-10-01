# Ponto de retomada — 2026-10-01

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
