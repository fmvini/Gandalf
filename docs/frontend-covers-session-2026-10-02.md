# Frontend: capas e regressões de responsividade — 2026-10-02

## Estado e responsabilidade

Código congelado; documento final liberado ao Maestro para consolidação e commit separado de capas. Rodada final do Maestro aprovada, conforme resultados abaixo. Frontend não executou suíte geral/build, stage, commit ou push; não editou API, dados, chaves, cotas ou processos existentes. Este é o documento exclusivo de Frontend; os três registros compartilhados continuam reservados ao Maestro.

Snapshot pré-capas preservado, sem nova cópia: `.impeccable/runtime/frontend-pre-covers-20261002-093847`, 63 arquivos com SHA256 verificado na criação, `manifest.json`, `frontend-before.patch` e `HEAD.txt`. Permite separar a integração anterior das capas. Não incluir artefatos ignorados no commit.

## Diagnóstico real antes da correção

- Relatório: `.impeccable/runtime/covers-before-real.json`; navegador sobre o `dist` existente, servido temporariamente em porta efêmera, sem iniciar Vite duplicado em 5173. Requisições encaminhadas à API existente em 8000.
- Home: JPEGs locais HTTP 200, visíveis e carregados. Duna `dune.jpg` 265×475; O Hobbit `hobbit.jpg` 330×500; O Jardim Secreto `secret-garden.jpg` 361×500. Home e assets não foram alterados.
- `GET /api/v1/books/search?q=Duna&limit=6`: resposta 200 com Duna, Frank Herbert, `provider=local`, `cover_url=null`, ID `2e59b23c-8acd-5423-897c-6edddf2c3859`. Ler com Música não criava `<img>` nem requisitava a capa local, tanto na lista quanto na seleção. Usava somente `cover_url`, apesar do JPEG válido já disponível.
- O diagnóstico também fez `POST /api/v1/recommendations/books` com “Fantasia com aventura”, retornando sete itens locais em fallback de transporte. Este endpoint pode reservar chamada Groq automaticamente. **Não afirmar zero consumo LLM**: a leitura RO posterior do Maestro observou `ai_usage` de 2026-10-02 com **2 chamadas de limite 50**. Nenhuma chave/cota foi alterada.
- Não foi comprovada uma URL externa quebrada com status/dimensões nesta sessão. A auditoria Banco/Backend mostrou o defeito puro de edição `cover_i=0/-1` apagando capa válida e URLs legadas sem `default=false`; isso não prova que todas as imagens de catálogo estejam quebradas.
- Antes da instrução final de cessar chamadas, um diagnóstico posterior fez apenas GET público de busca sobre a fonte nova: HTTP 200, mas não encontrou Duna com `provider=local` no resultado atual e falhou a asserção de alvo. **Não há confirmação real pós-correção por esse diagnóstico**. Nenhuma nova chamada API/externa/LLM será feita por Frontend nesta etapa.

## Correção de capas

- `BookCover` unifica Books/Discovery, favoritos e lista/seleção de Ler com Música. URL informada nos metadados tem prioridade. Asset local por título só é permitido com `provider=local`, evitando atribuir a edição local a um homônimo externo.
- Erro HTTP/network usa o ícone neutro de livro. `onLoad` também detecta largura ou altura natural ≤1: Open Library legado pode devolver imagem branca HTTP 200, sem disparar `onError`.
- Falha pertence à URL, não ao livro/componente inteiro. Uma URL diferente carrega mesmo depois de falha; a regressão mantém o componente montado, sem mascarar o estado com remount. Sem loop de retry ou alteração de metadados/identidade.
- Título e autoria continuam textuais. Imagens redundantes em favoritos/picker/seleção mantêm alt vazio; Discovery conserva o alt existente. CSS reserva o espaço de capa e centraliza o fallback.
- Patch Backend é separado: valida inteiro positivo, preserva capa da obra quando a edição não oferece capa válida e usa `?default=false` em novas URLs. Não reescrevemos catálogo/cache/snapshots legados. Ver `docs/backend-covers-session-2026-10-02.md` e `docs/database-covers-session-2026-10-02.md`.

## Duas regressões de baseline/responsividade

- Foco reroll: teste antigo usava `.focus()` após clique, ainda em modalidade pointer, e não ativava `:focus-visible`. `tests/reroll.mjs` agora navega com Tab real e verifica controle ativo; a asserção de outline permanece. Maestro executou reroll completo: PASS.
- Favoritos 320px: “Buscar no YouTube” dentro de `.favorite-row-actions` herdava `margin-left:89px` destinado ao link externo da linha de resultado. Reprodução: página 320, scrollWidth347, link right347.375. `.favorite-row-actions .result-link { margin-left:0; }` resultou em scrollWidth320, right258.375 e nenhum elemento excedente. Relatórios `favorites-overflow-before.json` e `favorites-overflow-current-css.json` em `.impeccable/runtime`; confirmação inicial aplicou exatamente a folha atual sobre o dist anterior. A regressão de capas depois confirmou a fonte completa nova com esse link.
- Maestro identificou “Cinematográfica” invadindo “Calma” no cartão em 320px, apesar de scrollWidth correto. Fix restrito: `.reading-mode strong, .reading-mode span { min-width:0; overflow-wrap:anywhere; }`. Fonte/tamanho preservados. O teste agora mede cada retângulo de linha dentro do seu próprio botão, além da largura da página.

## Verificação executada por Frontend

- `cd frontend; node node_modules/typescript/bin/tsc -b`: **PASS** após alterações de componentes/páginas; alteração seguinte foi somente CSS/testes/package.
- `node --check tests/covers.mjs`: **PASS** na versão final. `git diff --check -- frontend`: **PASS**, apenas avisos Git de conversão LF/CRLF. Diffs de capas e contra snapshot revisados.
- `node tests/covers.mjs`, escalado por autorização: **PASS** na versão final. Vite e Chromium próprios temporários, fechados no finally. O teste pede `port:0`, mas Vite resolveu **5173** nesta execução (URL registrada nos eventos); não chamar essa porta de efêmera. Não foi iniciado serviço persistente nem interrompido processo existente. O servidor estático do diagnóstico inicial, via Node HTTP, realmente usou porta efêmera. APIs do teste são fixtures; nenhum usuário/favorito/playlist real foi criado ou removido.
- Regressões: HTTP 404 realmente dispara evento error; GIF válido HTTP 200 realmente dispara load com naturalWidth/naturalHeight 1×1 e cai no placeholder. URL válida depois de falha no mesmo componente carrega; metadado explícito prevalece; homônimo externo sem URL não recebe asset local. Books, lista/seleção de Ler com Música e favoritos verificam esses estados; Home verifica assets existentes.
- 60 capturas atuais: cinco estados (`home`, `books`, `reading-picker`, `reading-selected`, `favorites`) × 1440/390/320 × dark/light × reduce/no-preference. Espera por fontes, imagens, fim de animações finitas e dois frames antes da captura. Asserções de overflow em toda matriz e de texto dentro dos cartões em ambos estados de leitura. Zero erros de runtime. `.impeccable/runtime/covers-ui-matrix.json` guarda eventos e geometria; imagens `.impeccable/review/covers-{estado}-{largura}-{tema}-{movimento}.png`.
- Inspeção visual em folhas dos cinco estados e confirmação individual `covers-reading-selected-320-light-reduce.png`, `covers-reading-selected-320-dark-no-preference.png`, `covers-favorites-390-light-no-preference.png`: capas/placeholder, títulos/autoria e ações visíveis; Cinematográfica quebra dentro do cartão após o fix. Revisão limitada a esses estados/fixtures, não aprovação visual global nem online externo.
- Skills Impeccable e design-taste-frontend aplicadas para diagnóstico/refinamento, preservando direção aprovada, Manrope/Newsreader, dois temas e preferências de movimento. Detector executado uma vez nos componentes/páginas/CSS de capas: `[]`, exit0, **antes** do último fix de quebra do cartão; não foi repetido e não equivale a QA visual completa. Sem dependências/novos assets/componentes externos nesta correção; fontes/licenças da unidade anterior permanecem em `frontend/THIRD_PARTY_NOTICES.md`.
- Evidência Maestro anterior: build PASS (2049 módulos, aviso 502.65kB); baseline smoke/components/auth/continuation/playlists/favorites PASS; reroll PASS após Tab. Live anterior falhou no overflow347.
- **Rodada final informada pelo Maestro: continuation, favorites e live PASS**, incluindo integração API real/SQLite, duas contas e temas/mobile; **build PASS, 2050 módulos**, aviso de bundle 502.97kB. Maestro não repetiu covers, aprovado por Frontend. Esses gates aprovam a integração testada; não comprovam imagens externas Open Library nem sucesso online dos provedores/LLM.
- Maestro criou **`137d492`** para integração favoritos+reroll+componentes, usando snapshot de 24 arquivos e docs, sem capas. README atualizado pelo Maestro após gates. Capas permanecem unidade separada, pronta para commit serializado.

## Arquivos mínimos para serialização

1. Integração anterior favoritos+reroll+componentes: usar snapshot pré-capas com `frontend/tests/reroll.mjs` atual e `frontend/src/favorites.css` atual (Tab e margin-left). Preservar package com os nove módulos anteriores antes do hunk de capas.
2. Capas/responsividade: `frontend/src/components/BookCover.tsx`, `frontend/src/lib/showcase.ts`, `frontend/src/pages/Discovery.tsx`, `frontend/src/pages/Favorites.tsx`, `frontend/src/pages/ReadWithMusic.tsx`, `frontend/src/styles.css`, `frontend/tests/covers.mjs`, `frontend/tests/fixtures/book-cover.tsx`, hunk `frontend/package.json` e este documento. Package mantém os módulos anteriores, adiciona covers ao `npm test` e disponibiliza `npm run test:covers`.

## Próximos passos

Maestro consolidar resultados nos docs compartilhados e commitar a unidade separada de capas com este documento final liberado. Código e testes permanecem congelados; nenhum novo teste/probe é necessário nesta etapa. Imagens externas reais seguem não comprovadas; transporte/backend/runtime e auditoria do catálogo pertencem aos agentes responsáveis, sem novas chamadas necessárias para este gate. Sem push.
