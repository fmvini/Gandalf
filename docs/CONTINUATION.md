# Ponto de retomada — 2026-10-01

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
