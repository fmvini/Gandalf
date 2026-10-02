# Frontend — autenticação, 2026-10-02

## Estado e reserva

Unidade funcional implementada e novamente congelada para revisão/serialização do Maestro. **Auth browser, continuation, live/SQLite e build agora PASS**, após autorização para execução escalada nesta retomada. Node/TypeScript/sintaxe/diff-check já aprovados; módulos Node não repetidos. Sem stage, commit ou push pelo Frontend; permissões Git/serialização são responsabilidade do Maestro. Bloqueios anteriores abaixo são histórico, superados para estes gates específicos.

Reserva original: formulários/cliente de sessão/testes frontend e este relatório; nesta retomada, somente harnesses de testes e este documento. Nenhuma alteração em Backend, dados/processos existentes, chaves, cotas ou documentos compartilhados. Maestro coordena `DEVELOPMENT_LOG.md`, `CONTINUATION.md`, `IMPLEMENTATION_STATUS.md` e Git. Live fez HTTP real apenas contra API offline descartável/SQLite temporário, inclusive auth e recomendações locais; nenhuma chamada à API8000 existente, providers externos ou Groq.

## Retomada autorizada — gates finais

Execução normal tentada antes de cada escalada. Auth/continuation/build falharam em esbuild `spawn EPERM`; live normal falhou no spawn Python, antes de iniciar API. Revisão automática desta rodada autorizou as execuções escaladas seguintes, sem contornar sandbox:

| Comando em `frontend/` | Resultado escalado | Isolamento/evidência |
| --- | --- | --- |
| `node tests/auth.mjs` | PASS | Porta HTTP efetiva55554; mocks, Chromium reduzido; submit login/cadastro único, pré-abort, rotação/concorrência, cancelamento, erro/retry e tokens só em memória |
| `node tests/continuation.mjs` | PASS | Porta64151; fixtures, retry/cancelamento/esgotamento/duração e layout1440/390/320 dois temas |
| `node tests/live.mjs` | PASS | Front54815/API54792; `local.py` offline explícito, SQLite em diretório temporário; cadastro/login/conta/logout, revogação refresh, favoritos/playlist e isolamento entre duas contas |
| `npm.cmd run build` | PASS | TypeScript + Vite2050 módulos; JS504,06kB/gzip158,12kB, aviso não fatal de chunk acima500kB |

- Nenhuma suíte geral, módulo Node já aprovado ou provider/LLM foi repetido nesta retomada. Nenhuma correção adicional de UI ou cliente de sessão necessária: os gates passaram no patch congelado.
- Continuation/live também usam agora Vite middleware sem HMR + listener Node HTTP port0 real/assert diferente5173. Live confere API diferente8000/5432, força `GANDALF_ONLINE=0`/catálogo offline/provider local no processo exclusivo e engloba spawn/cleanup no try/finally. Falha de spawn normal comprovada motivou cleanup também nessa etapa; término aguarda close já registrado do próprio processo, sem matar processos por porta.
- Execução live exit0 inclui encerramento dos recursos próprios e remoção do SQLite/diretório exclusivo. O único diretório vazio deixado pela tentativa normal anterior ao ajuste de cleanup foi identificado por caminho/horário desta rodada, validado sob TEMP e vazio, e removido sem recursão. Nenhum outro diretório temporário alterado.
- Checagem RO final observou frontend25716 em `[::1]:5173` e PG10140/5432. Nenhum listener8000 foi observado naquele instante; não se declarou readiness da API existente nem houve tentativa de iniciar/reparar/reiniciar esse serviço. Informado ao Maestro para coordenação.
- Capturas atuais: **18 auth** em1440/390/320 dark/light, **20 continuation**; fontes prontas e animações finitas aguardadas pelos harnesses. Live usa movimento normal; continuation reduzido, auth mocks também reduzido. Asserções de largura aprovadas. Inspecionadas diretamente `auth-register-320-light.png` e `auth-login-320-dark.png`: labels, campos, botão e ajuda visíveis sem sobreposição/overflow. Isso é QA focada, não certificação integral de acessibilidade ou de gerenciadores de senha.
- Caminhos completos das duas capturas revisadas: `C:/Users/vinic/Documents/Gandalf/.impeccable/review/auth-register-320-light.png` e `C:/Users/vinic/Documents/Gandalf/.impeccable/review/auth-login-320-dark.png`. Demais auth: `.impeccable/review/auth-{login,register,account}-{1440,390,320}-{dark,light}.png`; continuation: `.impeccable/review/continuation-*.png`. Artefatos ignorados, não fazem parte do checkout.
- Sintaxe dos dois harnesses alterados e diff-check finais aprovados; só avisos LF/CRLF. Nenhuma asserção removida/enfraquecida.

## Contexto e auditoria

- Consultados `docs/DEVELOPMENT_LOG.md`, `docs/05-API-Specification.md`, `docs/09-security-specification.md`, `docs/adr/0006-jwt-authentication-strategy.md`, schemas auth e implementação frontend. Backend confirmou contratos por Maestri, sem probes.
- Registro exige username ASCII 3–32 e senha 10–128; login usa e-mail/senha e retorna access/refresh. Registro não inicia sessão. Senha nunca é trimada. Validação servidor é autoritativa; regra ilustrativa 3–30 do documento security não substitui o contrato implementado.
- ADR-0006 mantém tokens exclusivamente em memória: nenhum novo storage/cookie/log de credenciais. A sessão se perde no reload; store público contém apenas usuário/estado expirado. Logout revoga refresh; access JWT pode permanecer válido até expirar, conforme contrato Backend, sem nova promessa de revogação instantânea.
- Retorno após login já restringe pathname exatamente a `/music`, `/books`, `/read-with-music`, `/account/favorites`; não aceita URL externa, protocol-relative ou query concatenada. Snapshot permitido permanece ligado à navegação interna.
- Labels, descrição dos requisitos, alert com foco, `aria-busy`, disabled durante submit, alternância da senha e mensagens genéricas existentes preservados. Falhas 401/409 não identificam qual credencial existe; 429 tem mensagem própria. Renderização de erro é texto React, nunca HTML.
- Impeccable (`harden`, `clarify`, craft floor) e taste aplicados à reserva estreita, preservando identidade/tokens/tipografia. Sem CSS, redesign ou dependências novas. Contexto impeccable já carregado nesta sessão; não repetido.

## Defeitos reproduzidos e correções

1. **Submit duplicado antes do próximo render.** Em `tests/auth.mjs`, dois eventos submit na mesma tarefa produziram dois POSTs login; asserção `Same-turn submit must produce exactly one login` falhou **2 !== 1**, porta efetiva **51693**, antes da correção. O `pending` de useState ainda era false na closure. `Authentication.tsx` usa agora o ref do AbortController como trava síncrona e libera somente a operação correspondente em finally. Pending/disabled continuam informando a UI; erro libera retry. Registro recebe a mesma proteção.
2. **Chamador já abortado iniciava refresh.** Teste Node executando `src/lib/auth.ts` de produção, HTTP e relógio simulados, falhou **1 !== 0** em `Pre-aborted request must not start a rotation`. `auth.ts` verifica o sinal antes da sessão/refresh, antes de enviar request e depois de aguardar refresh proativo ou após 401. Cancelar um consumidor não aborta a rotação compartilhada de outros; consumidor cancelado não envia retry. Single-flight, revision/ownership, tokens, contratos e logout preservados.
3. **Semântica de campos para autofill.** Inspeção mostrou inputs sem `name` e login e-mail com autocomplete de contato. Adicionados names estáveis email/username/password/password_confirmation e `autocomplete="username"` para o e-mail usado como identificador de login; cadastro mantém email/username/new-password. Atributos verificados em Node; compatibilidade efetiva de gerenciadores de senha ainda não testada no browser.

## Arquivos da unidade

- `frontend/src/pages/Authentication.tsx` — trava síncrona e atributos de formulário.
- `frontend/src/lib/auth.ts` — verificações de sinal; nenhuma mudança em armazenamento/contrato.
- `frontend/tests/auth-session.mjs` — executa módulo TypeScript de produção em VM, com apenas HTTP/relógio simulados.
- `frontend/tests/auth-form.mjs` — executa componente/submit de produção com setters em lote/refs estáveis e dependências explícitas simuladas; não é DOM nem renderizador React de browser.
- `frontend/tests/auth.mjs` — preserva cenários anteriores, adiciona duplicação login/cadastro e pré-abort; middleware Vite sem HMR com HTTP listener port0 real, assert porta diferente5173, cleanup próprio e bloqueio de API incidental.
- `frontend/tests/continuation.mjs`, `frontend/tests/live.mjs` — isolamento port0 real, offline explícito/cleanup do gate live; cenários e asserções anteriores preservados.
- `frontend/package.json` — adiciona ambos módulos Node ao npm test mantendo todos anteriores e `test:auth-state`; sem dependência/lock novo.
- `docs/frontend-auth-session-2026-10-02.md` — relatório exclusivo liberado ao Maestro.

## Validação efetivamente executada

- `node tests/auth-session.mjs` **PASS**: pré-abort sem refresh; registro sem login/normalização da senha; três 401s/uma rotação; cancelamento de um consumidor preserva outro; profile e refresh antigos não substituem dono novo; logout único espera rotação e usa refresh novo; refresh401 expira; logout com falha de transporte permite retry; login cancelado não publica usuário.
- `node tests/auth-form.mjs` **PASS**: submits no mesmo turno em login/cadastro fazem uma chamada; sucesso/erro liberam trava; mismatch não chama API; names/autocomplete; quatro retornos internos com snapshot e quatro destinos recusados.
- `node node_modules/typescript/bin/tsc -b` **PASS**.
- `node --check tests/auth.mjs`, `node --check tests/auth-session.mjs`, `node --check tests/auth-form.mjs` **PASS**.
- `git diff --check -- frontend` **PASS**, avisos LF/CRLF somente. Diff revisado sem arquivos dos colegas.
- Detector impeccable uma rodada para `Authentication.tsx`/`auth.ts`: **[]**, exit0. Não certifica acessibilidade por si só.

## Histórico de bloqueios e limites restantes

- Rodada browser anterior chegou ao defeito duplicação e falhou; isso é reprodução, **não aprovação da unidade**. Tentativa escalada posterior foi rejeitada porque revisão automática atingiu limite de uso e não executou. Após retomada, tentativa normal falhou em esbuild `ensureServiceIsRunning` **spawn EPERM**, antes de qualquer teste/porta/Chromium. Maestro confirmou mesmo bloqueio. Sem contornar sandbox nem repetir aprovação.
- Antes da retomada com permissões corrigidas, `auth.mjs` atualizado só tinha sintaxe verificada; build/live/continuation não aprovados. Esses quatro gates foram executados e aprovados agora, conforme tabela no início; nenhuma suíte integral executada. Maestro dispensou redesign/nova auditoria visual ampla para estes patches sem CSS, e a rodada live produziu QA focada real descrita acima.
- Testes VM provam lógica/handlers de produção nas condições simuladas; não validam constraint validation nativa, foco/teclado/screen reader, autofill/salvamento real de credenciais, rede, backend HTTP ou acessibilidade completa. Native minlength/maxLength contam UTF-16 enquanto servidor conta caracteres Unicode; inputs extremos Unicode e detalhes422 permanecem limites de auditoria, sem correção incidental.
- Consumidor cancelado durante rotação compartilhada ainda aguarda sua conclusão antes de rejeitar; a rotação não é abortada e não há request autenticado posterior desse consumidor. Backend mantém auditoria de refresh entre instâncias/bancos, separada destes testes frontend.

## Próximos passos exclusivos do Maestro

1. Revisar/consolidar resultados finais sem repetir auth/continuation/live/build já aprovados na árvore congelada, salvo nova mudança/falha. Nenhum gate favorites separado foi necessário porque live cobriu duas contas/ownership e não mostrou defeito.
2. Serializar commit seletivo desta unidade com permissões Git, incluindo ambos harnesses alterados e documento; consolidar documentos compartilhados com evidências/limites. Nenhum push autorizado.
3. Coordenar estado da API8000 existente separadamente; Frontend não a utilizou nem reiniciou. PostgreSQL auth/refresh entre instâncias, gerenciadores de senha e acessibilidade assistiva completa continuam escopos próprios.
4. Código/relatório novamente congelados para revisão; nenhuma nova edição/teste/probe sem coordenação.
