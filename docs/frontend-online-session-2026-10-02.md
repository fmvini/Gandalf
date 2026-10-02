# Frontend — tentativa degradada de renovação — 2026-10-02

## Estado final

Código e documento congelados/liberados ao Maestro para commit seletivo. Maestro aprovou build final de 2.050 módulos (aviso não fatal de bundle 503,12 kB) e revisou capturas mobile Música/light e Livros/dark. Alteração de produto restrita à mensagem do re-roll vazio degradado, compartilhada por Música/Livros. Sem redesign, CSS, componente/dependência nova, alteração de API/contrato/cursor/dados ou quota. Frontend não fez stage/commit/push, build ou suíte geral. Docs compartilhados e Git continuam exclusivos do Maestro.

Baseline consultado: HEAD `ffdd6a6`, árvore inicialmente limpa; entradas atuais de `docs/DEVELOPMENT_LOG.md`, `docs/CONTINUATION.md`, contrato implementado `docs/05-API-Specification.md` §§6.1–6.3 e serviços/metadados reais no código. Impeccable/taste aplicadas como auditoria/refinamento da direção existente; contexto da sessão preservado, sem reparar sidecar/design ou introduzir estética nova.

## Auditoria dos três fluxos e um problema comprovado

Auditoria em contexto de navegador separado sobre o frontend existente `http://localhost:5173`. Todas as requisições de API foram interceptadas por fixtures, sem encaminhamento. Artefatos ignorados, dentro do escopo frontend: `frontend/.impeccable/online-audit.mjs` e `frontend/.impeccable/online-audit/evidence.json`; seis capturas da auditoria no mesmo diretório. Não incluir estes artefatos no commit.

- **Música/Livros — fallback local e fontes parciais:** `meta.hint` da seleção é apresentado; fixtures com `ai_used=false/sources=['local']/degraded=true` mostraram classificação por regras/catálogo local, e fontes parciais mostraram seu aviso. Não foi encontrado motivo para substituir essas mensagens nesta unidade.
- **Ler com Música:** fixture de sucesso com durações conhecidas e IA indisponível mostrou ordenação por temas/atmosfera via hint. `503 SOUNDTRACK_INCOMPLETE` limpou faixas anteriores, mostrou contagem/minutos e preservou livro/formulário; nenhuma playlist parcial apresentada como sucesso. Página não alterada.
- **Problema único — re-roll vazio degradado:** depois de uma seleção com hint de IA/fonte, resposta nova `items=[]`, `degraded=true`, `has_more=false` conservava corretamente lista/retry/snapshot, mas dizia somente “Não encontramos novas músicas/livros nesta tentativa. Tente novamente para continuar a busca.” O hint da tentativa limitada era descartado, e o hint visível continuava descrevendo a seleção anterior. Faltava distinguir limitação desta tentativa de ausência normal de novas opções e tornar explícita a preservação da lista. Reprodução confirmada nos dois fluxos, sem falha de persistência/IDs/cursor.

## Semântica confirmada pelo Backend

Confirmação por leitura do código, sem probes adicionais: `degraded = bool(warnings)` pode refletir interpretação/parser IA, seleção IA ou uma fonte/termo; não significa todas as fontes offline. `ai_used` informa seleção por IA, não apenas interpretação bem-sucedida. `sources` descreve os provedores dos itens efetivamente entregues e pode incluir catálogo local. `hint` é string no contrato local/online, composta por texto servidor e mensagens genéricas, sem corpo upstream/chaves/SQL; eventual apresentação deve ser texto React, nunca HTML.

No re-roll sem opções novas, manter `data`/hint anteriores é correto: descrevem a seleção que continuou visível. Não substituímos esses metadados pelo erro da tentativa atual.

## Fix mínimo autorizado e implementado

`frontend/src/pages/Discovery.tsx`: somente quando não há opções novas e `meta.degraded` é verdadeiro, a mensagem agora é:

> Esta tentativa teve uma limitação e não trouxe novas opções. Sua seleção anterior continua aqui. Tente novamente.

O aviso continua no `role=alert`/`aria-atomic=true` existente. Não atribui indisponibilidade a todas as fontes/IA. O hint novo não foi acrescentado: a mensagem necessária é estável mesmo sem hint, e o hint antigo continua ligado à seleção preservada. Casos não degradados de retry/esgotamento mantêm a mensagem anterior. Comentário técnico corrigido para refletir limitações de uma etapa/fonte, sem mudança de estado.

## Testes e QA executados

- `cd frontend; node --check tests/reroll.mjs`: **PASS**.
- `node tests/reroll.mjs`, com permissão escalada: **PASS**; somente módulo afetado, APIs inteiramente por fixtures. Continuam todas as asserções anteriores: foco Tab/outline, espera/erro/cancelamento, deduplicação, filtros/query enviados, cursor null, login/expiração, esgotamento e 199+1/200 IDs sem truncar.
- Novos casos MUSIC/BOOK cobrem `degraded=true` com `has_more=false/true/ausente`, hint presente/ausente; lista/IDs/hint anteriores, mensagem acessível e retry preservados. Snapshot de erro passa pelo login nos dois fluxos, sem refetch/autosave, conservando rascunho separado do pedido/filtros enviados. Retry reutiliza exatamente o body anterior; sucesso limpa o aviso. Esgotamento não degradado mantém lista, desabilita renovação e usa status distinto.
- Teste isolado agora usa Vite em middleware, sem HMR, sobre listener Node HTTP `port=0`; porta efetiva **50070**, validada como positiva e diferente de 5173 e impressa na execução. HTTP/Vite/browser próprios fechados ao final. Não reiniciamos nem encerramos frontend/API existentes.
- `node node_modules/typescript/bin/tsc -b`: **PASS** após a mudança final. `git diff --check -- frontend`: **PASS**, apenas avisos LF/CRLF. Diff revisado; pacote/npm test não alterado, os novos casos integram o módulo reroll já existente.
- Detector Impeccable executado uma vez em Discovery: `[]`, exit0. Não equivale a aprovação visual global.
- **14 capturas focadas novas**, após restauração do login: Música/Livros × 1440/390/320 × dark/light com movimento reduzido, mais 320/dark com movimento normal em cada fluxo. Espera por fontes, fim de animações finitas e dois frames; asserções de mensagem/lista e largura em todas. Folhas dos dois fluxos e captura individual 320/light inspecionadas: mensagem completa, seleção anterior e botão de retry visíveis, sem overflow. Nenhum erro de runtime. Sem novo E2E online/API real ou suíte global.

### Caminhos absolutos para revisão do Maestro

- `C:/Users/vinic/Documents/Gandalf/.impeccable/review/reroll-music-limited-320-light-reduce.png`
- `C:/Users/vinic/Documents/Gandalf/.impeccable/review/reroll-books-limited-1440-dark-reduce.png`
- Alternativa mobile livros: `C:/Users/vinic/Documents/Gandalf/.impeccable/review/reroll-books-limited-320-dark-reduce.png`
- Todas: `C:/Users/vinic/Documents/Gandalf/.impeccable/review/reroll-{music|books}-limited-{1440|390|320}-{dark|light}-{reduce|no-preference}.png` (normal apenas 320/dark).

## Evidência online separada e limites

Backend informou nesta rodada fontes reais Open Library200/O Hobbit PT e MusicBrainz200/GoGo Penguin usando o cliente da aplicação com raízes TLS do SO; uma interpretação Groq200/Intent válido, quota observada 2→3 nessa etapa. O probe anterior certifi/issuer20 não representava o cliente da aplicação.

Gate real posterior concluído e encerrado pelo Backend: dois POST de música com limit3, exclusões cumulativas e cursor0→15 retornaram200, `ai_used=true`, `degraded=false`, `has_more=true`, `next_offset=15→30`; seis UUIDs únicos sem repetição, quota3→5. **Ambas as respostas entregaram `sources=['local']`**, não músicas externas. A participação da IA na seleção não muda a origem local dos itens; MusicBrainz200 foi prova direta separada. GET real da capa exata O Hobbit/Open Library14849956 retornou200/JPEG180×285,25626bytes, pelo cliente TLS da aplicação. Artefato ignorado pertence ao Backend. Estas evidências são do Backend/API, não uma nova execução de UI pelo Frontend nem aprovação de recomendações musicais externas.

Esta auditoria/fix de Frontend não fez chamadas reais de recommendations, provedores ou Groq, nem leu/alterou quotas. Todos os dados de prova desta unidade são fixtures; não declaramos sucesso online/IA por fallback local. Nenhuma alteração de dados, chave, configuração TLS, processo existente ou contrato.

## Arquivos da unidade e continuação

- `frontend/src/pages/Discovery.tsx`
- `frontend/tests/reroll.mjs`
- `docs/frontend-online-session-2026-10-02.md`

Maestro recebeu freeze, executou somente build final e revisou duas capturas, sem repetir reroll PASS, suíte geral ou probes API/externos. Consolidar docs compartilhados e serializar commit seletivo. Nada adicional previsto nesta unidade. Transporte/seleção online real e PostgreSQL são gates independentes dos agentes responsáveis.
