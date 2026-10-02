# Frontend — origem e classificação por faixa — 2026-10-02

## Estado

Unidade autorizada implementada e congelada para commit do Maestro. Maestro aprovou build final2.050 módulos (aviso não fatal de bundle503,70kB), reroll completo afetado e revisão das capturas320light/1440dark. UI restrita a uma linha textual por faixa em Discovery/MusicResult. Nenhum CSS novo necessário; sem redesign, dependências, mudanças de estado/ranking/contrato público ou requisições extras. Git e os três docs compartilhados continuam reservados ao Maestro; Frontend não fez stage/commit/push.

Baseline: docs atuais DEVELOPMENT_LOG/CONTINUATION/05 e revisão somente leitura. A UI tinha aviso global sobre fontes/estimativas, mas não diferenciava por faixa os valores conhecidos, ausentes e estimados. Não foi demonstrado que a UI anterior afirmasse medição real ou tratasse unknown como instrumental; o problema autorizado foi a identificação por item.

## Semântica combinada com Backend

- `has_vocals=false`: instrumental; `true`: com voz; `null`/ausente: não informado. Nunca converter ausência em instrumental, nem inferir o booleano das tags.
- Energia conhecida atual: `low`, `medium`, `high`; Choice.energy `unknown` é convertido em `None` no fluxo atual quando não há valor do catálogo. Frontend tipa esses três valores/null; não existe schema backend MusicItem validando essa saída, pois descoberta retorna dicts. Não descrever a tipagem frontend como garantia de schema backend.
- `classification_source=ai_estimate`: mostrar explicitamente “Estimativa por IA”. `provider_tags`: mostrar “Tags da fonte”, sem afirmar medição. Os demais valores/ausência não autorizam rótulo de estimativa. Marker é respeitado literalmente; o backend atual marca descoberta MusicBrainz selecionada como ai_estimate mesmo com valor existente. Essa ressalva permanece unidade separada, sem correção incidental.
- `provider` só identifica origem quando enviado. `musicbrainz` vira “MusicBrainz”; `local` vira “Catálogo local”; outro identificador informado aparece como “Fonte: …”. Ausência não é local, nem deduzida de links, tags, `ai_used` ou `sources` agregadas. Catálogo editorial pode omitir provider.
- `provider_tags` atualmente é escrito na leitura MusicBrainz quando há tag instrumental; a fixture de Discovery com esse marker testa apresentação literal caso o campo seja recebido, não comprova ocorrência real nessa rota. Energia/atmosfera por tags não é medição.

## Implementação

- `frontend/src/lib/api.ts`: campos opcionais `provider`, `has_vocals`, `energy`, `classification_source` em MusicItem, compatíveis com ausência/null. Não exige alteração da API.
- `frontend/src/lib/format.ts`: `musicMetadataLabel` produz texto somente dos campos de cada item. Exemplos: “MusicBrainz · Estimativa por IA · Instrumental · Energia baixa”, “Catálogo local · Com voz · Energia média”, “Vocais não informados · Energia não informada”. Valores conhecidos são apresentados sem alegar que foram medidos.
- `frontend/src/pages/Discovery.tsx`: um `<p className="music-metadata">` em cada MusicResult, depois de artista/álbum. Reutiliza `.result-main > p`, cor `var(--muted)`, fonte .88rem e margem existentes; quebra natural em mobile. Sem badges, ícones, novo componente ou rótulo por cor. Texto React, sem HTML fornecido pelo servidor.
- Hint global e tags originais permanecem; a linha não altera origem dos itens/identidade, classificação, restrições, seleção, favoritos, snapshots ou cursores. Ler com Música/Favorites não receberam alterações visuais nesta unidade.

## Verificações executadas

- `cd frontend; node --check tests/music-metadata.mjs`: **PASS**.
- `node tests/music-metadata.mjs` com permissão escalada: **PASS**, somente novo módulo focado. Dez fixtures cobrem estimativa IA, dados conhecidos sem marker, provider_tags, valores nulos, campos ausentes, catálogo local explícito, catálogo sem origem informada, estimativa sem provider e origem/marker desconhecidos. Tags “instrumental/energia alta” não preenchem campos ausentes. `ai_used=true`/fontes agregadas não autorizam origem ou marker por item.
- Um único POST de descoberta **simulado**, nenhum API/Groq/provedor real. Não testa qualidade da seleção musical nem fecha seu gate online.
- Teste usa Vite middleware/sem HMR sobre HTTP Node port0; porta efetiva **57034**, confirmada diferente de5173. Browser/Vite/HTTP temporários encerrados; nenhum processo existente reiniciado/encerrado.
- `node node_modules/typescript/bin/tsc -b`: **PASS**. `git diff --check -- frontend`: **PASS**, apenas aviso LF/CRLF; diff revisado. Build/suíte geral não executados pelo Frontend.
- Detector Impeccable uma vez nos três arquivos src: `[]`, exit0. Skills Impeccable/taste usadas para refinamento, preservando direção existente, fontes e tokens; scanner não substitui QA.
- **Oito capturas novas**: 1440/390/320 dark/light com movimento reduzido, mais 320 dark/light normal. Espera por fontes, animações finitas e dois frames. Texto visível/accessível confirmado por árvore ARIA de cada faixa; exatamente um parágrafo de metadados por item; fonte mínima **14.08px**, contraste mínimo medido **5.96:1**; largura de página e retângulos de cada linha dentro de sua coluna, em toda matriz. Zero erro de runtime.
- Inspeção visual de 320/light reduzido, 1440/dark, 390/dark, 1440/light e 320/dark normal: rótulos de origem/estimativa/ausência e faixas legíveis, quebra sem sobreposição. QA limitada às fixtures desta unidade, sem alegação de certificação a11y/global ou nova seleção externa real.

## Artefatos de QA — caminhos absolutos

- `C:/Users/vinic/Documents/Gandalf/.impeccable/review/music-metadata-320-light-reduce.png`
- `C:/Users/vinic/Documents/Gandalf/.impeccable/review/music-metadata-390-dark-reduce.png`
- `C:/Users/vinic/Documents/Gandalf/.impeccable/review/music-metadata-1440-dark-reduce.png`
- Matriz: `C:/Users/vinic/Documents/Gandalf/.impeccable/review/music-metadata-{1440|390|320}-{dark|light}-{reduce|no-preference}.png` (normal apenas320).
- `C:/Users/vinic/Documents/Gandalf/.impeccable/review/music-metadata-evidence.json`: requisição simulada, porta, contraste/fonte e métricas por variante. Todos esses artefatos são ignorados; não incluir no commit.

## Arquivos e continuidade

- `frontend/src/lib/api.ts`
- `frontend/src/lib/format.ts`
- `frontend/src/pages/Discovery.tsx`
- `frontend/tests/music-metadata.mjs`
- `frontend/package.json`
- `docs/frontend-music-selection-session-2026-10-02.md`

Package mantém todos os módulos anteriores e acrescenta music-metadata ao npm test; `npm run test:music-metadata` executa somente este módulo. Nenhuma dependência/lock alterado.

Código/docs liberados e congelados ao Maestro: build/checks seletivos, revisão das capturas e commit local da unidade. Não duplicar suíte geral ou chamar recommendations/Groq reais para estes rótulos. Qualidade MUSIC/Groq payload e PostgreSQL/Docker permanecem unidades separadas de Backend/Banco; esta implementação não altera nem valida esses gates.
