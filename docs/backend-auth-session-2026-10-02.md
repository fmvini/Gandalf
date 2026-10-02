# Backend — auditoria e correções de autenticação — 2026-10-02

## Estado e reserva

Código/testes congelados e entregues ao Maestro para gate final. Base consultada: `13e0a495bf8e3a1391d4484a42a29a5e845e0a3a`, `docs/DEVELOPMENT_LOG.md`, `api/README.md`, ADR-0006, especificações API/security e instruções AGENTS fornecidas pelo usuário. Não houve stage/commit/push pelo Backend; Git e documentos compartilhados pertencem ao Maestro, que informou bloqueio de escrita Git nesta sessão.

**Retomada PG sobre `7192c5415311267db7f36494bc49af9fd7ed411c`:** o Banco reproduziu a corrida ancestral/descendente antes hipotética. Correção restrita ao serviço/testes implementada e congelada, **52 testes auth/security aprovados**; novo gate real PostgreSQL do Banco **PASS**, com zero ativos após replay. Registros de bloqueio/permissão anteriores abaixo são históricos; aprovação é limitada aos casos/isolamento descritos no adendo final.

Lista seletiva exata desta unidade:

- `api/app/core/security.py`
- `api/app/services/auth_service.py`
- `api/tests/test_auth.py`
- `api/tests/test_security.py` — novo
- `docs/backend-auth-session-2026-10-02.md` — novo

Rotas/schemas de auth foram auditados e preservados; nenhuma edição de modelos/migrations, main/config/rate limiter, arquivos Frontend/Banco ou documentos compartilhados. Nenhuma chamada externa/LLM, acesso HTTP à API8000, restart ou operação em dados reais. Testes usam credenciais sintéticas e SQLite descartável; fixtures finais configuram explicitamente catálogo local/offline e `_env_file=None`.

## Defeitos reproduzidos e corrigidos

Antes do patch, seis regressões falharam: hash inválido, consumo concorrente do mesmo refresh e quatro falhas de commit em registro/login/refresh/logout.

1. **Hash Argon2 estruturalmente inválido escapava da verificação.** `InvalidHashError` não deriva de `VerificationError` na biblioteca instalada. Login propagava a exceção como erro interno. Agora ambas são tratadas; hash vazio/inválido retorna credenciais inválidas401. A verificação dummy continua para ausência de hash, mas nunca pode autenticar, mesmo recebendo a senha usada no dummy. Nenhum hash/senha foi corrigido ou reescrito em banco real.
2. **SQLite permitia consumir o mesmo refresh duas vezes.** `FOR UPDATE` não bloqueia a linha nesse banco. Duas sessões independentes sincronizadas após validar o token podiam criar sucessores. Agora o consumo usa `UPDATE` condicional por ID, `revoked_at IS NULL` e expiração futura; somente quem altera uma linha pode inserir o sucessor. O perdedor faz rollback, recarrega o estado atual e aplica revogação da família quando detecta token consumido, retornando401. `FOR UPDATE` do PostgreSQL é preservado. O teste SQLite confirma um200/um401, apenas dois registros na família e zero refresh ativos após replay.
3. **Falhas SQL nas operações de auth não tinham tratamento uniforme.** Registro tratava conflito, e `/me` já tratava indisponibilidade; outras leituras/escritas podiam propagar parâmetros SQL para o handler genérico e não faziam rollback explícito. Um contexto interno agora captura `SQLAlchemyError`, faz rollback e retorna503 `SERVICE_UNAVAILABLE` genérico. Conflito de registro continua409 genérico. A geração da resposta de tokens ocorre antes do commit; tokens só são retornados após a confirmação da persistência.

Testes verificam rollback efetivo: não aparece usuário/sucessor extra, refresh original e links de substituição permanecem íntegros se o commit falha, rehash antigo é preservado e nenhum parâmetro sintético sensível aparece no corpo/log da resposta. Falha ao persistir revogação por replay retorna503; não se declara revogação concluída enquanto o banco está indisponível.

## Contratos auditados e preservados

- Registro: email válido, username ASCII `[A-Za-z0-9_.-]` de3–32 caracteres, senha10–128; email/username armazenados com casefold. Senha não é aparada/normalizada. Resposta201 apenas ID/email/username/data, sem senha/hash/tokens.
- Duplicidade:409 genérico, sem identificar o campo; login inexistente/senha errada/inativo usa401 `INVALID_CREDENTIALS` genérico. O status409 permite detectar conflito de cadastro e não equivale a uma resposta uniforme contra enumeração; política preservada, com rate limit existente sob reserva Maestro.
- Hash Argon2id, salts distintos e rehash transparente; teste confirma que rehash e criação do refresh são atômicos quando o commit falha. Nenhuma nova regra de composição/bloqueio de senhas introduzida.
- JWT HS256 fixo, segredo mínimo32 bytes, claims obrigatórios `sub/iat/exp/jti/type`, UUID do usuário e `type=access`; expiração default15 minutos. Testes rejeitam assinatura/algoritmo incorretos, `none`, claims ausentes/malformados e data futura. Biblioteca instalada já rejeitou os casos numéricos não finitos testados; nenhuma mudança especulativa de validação JWT foi necessária.
- Refresh opaco aleatório, armazenado somente como SHA256, default7 dias, rotação a cada uso; replay revoga apenas a família afetada. Outro login independente permanece utilizável. Usuário inativo não pode login/refresh/me.
- Logout revoga somente o refresh informado pertencente ao usuário; token antigo já rotacionado é no-op204 e preserva o descendente. Não implementa logout de toda a família ou denylist de access JWT: access continua válido até expirar. Tokens somente em memória no cliente, conforme ADR-0006.
- Limites/password schemas/erros públicos mantidos, sem alterar provider/modelo/chave/cota. Cache headers, sanitização do handler500 auth e retenção de chaves no rate limiter são correções separadas do Maestro; cancelamento/single-flight/troca de owner pertencem ao Frontend.

## Validação

Reprodução inicial, antes das correções, cwd `api`:

```powershell
& .venv/Scripts/python.exe -m pytest -q tests/test_auth.py -k 'corrupt_password or concurrent_refresh or write_failure' --tb=short
```

**6 failed**, oito deselected, um aviso, 29,04s. Regressões selecionadas após o patch: **6 passed**, oito deselected, 3,36s.

Rodada final com permissões atuais, cwd `api`:

```powershell
$env:PYTHONPATH='../.impeccable/runtime'
& .venv/Scripts/python.exe -m pytest -q -p no:tmpdir -p no:cacheprovider -p maestro_pytest_temp tests/test_auth.py tests/test_security.py --tb=short
& .venv/Scripts/python.exe -m ruff check app/core/security.py app/services/auth_service.py tests/test_auth.py tests/test_security.py
& .venv/Scripts/python.exe -m ruff format --check app/core/security.py app/services/auth_service.py tests/test_auth.py tests/test_security.py
git diff --check -- app/core/security.py app/services/auth_service.py tests/test_auth.py tests/test_security.py
```

**48 passed** — 26 auth +22 security — em11,35s. Um aviso preexistente Starlette/TestClient sobre HTTPX; sem falhas. Ruff check PASS, quatro arquivos já formatados, diff-check seletivo PASS. Não foi executada suíte geral pelo Backend. A rodada anterior teve43PASS antes de cinco verificações adicionais de senha/username e isolamento explícito das fixtures.

Plugin ignorado `.impeccable/runtime/maestro_pytest_temp.py`: substitui somente `tmp_path` por diretório temporário dentro do workspace com ACL herdada. Desabilitar `tmpdir` evita criação modo700 que bloqueia o SID restrito no Windows; desabilitar cacheprovider evita cache temporário sem acesso. Aplicação e asserções não foram relaxadas. Nenhuma elevação/contorno das permissões atuais foi solicitado.

Gate complementar **informado pelo Maestro**, sem duplicação pelo Backend: suíte API final com **470 passed /3 failed**. Os três falharam antes das asserções no acesso multiprocessing `Pipe/CreateFile`, `WinError5`: dois favoritos e um cache. Auth/security e os demais casos passaram; não declarar a suíte integral completamente aprovada. Ruff global `app/tests/scripts` e format-check de79 arquivos passaram. Git, build/browser e PostgreSQL continuam bloqueados por permissões nesta sessão.

### Retomada autorizada — três testes multiprocessos

Usuário corrigiu permissões e autorizou somente repetir os três casos antes bloqueados, primeiro normal e depois com escalada segura se necessário. Código/testes congelados permaneceram intactos; nenhum dos470 casos aprovados ou dos48 auth/security foi repetido.

Comando único do subset, cwd `api`, plugin herdado existente:

```powershell
$env:PYTHONPATH='../.impeccable/runtime'
& .venv/Scripts/python.exe -m pytest -q -p no:tmpdir -p no:cacheprovider -p maestro_pytest_temp tests/test_favorites.py::test_concurrent_processes_deduplicate_atomically tests/test_favorites.py::test_concurrent_repeated_create_and_delete_return_detached_snapshots tests/test_recommendation_cache.py::test_concurrent_sqlite_processes_enforce_global_capacity --tb=short
```

- Execução normal: **3 failed**, um aviso, 2,40s; novamente `WinError5` em `multiprocessing.Pipe/_winapi.CreateFile`, antes dos workers. Nenhuma falha de aplicação demonstrada.
- Mesmo comando com `require_escalated` autorizado/revisado: **3 passed**, um aviso preexistente, **10,05s**, exit code0. Deduplicação de favoritos, criação/exclusão concorrente com snapshots e capacidade global do cache passaram com processos reais e SQLite temporário.
- Complementa os470PASS informados pelo Maestro, em execuções separadas; não é uma nova execução integral. Nenhuma asserção, aplicação, plugin, modelo ou dado real foi alterado.
- Freeze devolvido ao Maestro. Atualizado somente este relatório exclusivo; sem Git/stage/commit/push, API8000/restart, LLM ou probes externos. PostgreSQL auth permanece gate separado do Banco; não inferir aprovação PG a partir destes processos SQLite.

## Limites e próximos passos

- Concorrência do mesmo token comprovada **somente SQLite** nesta unidade. Na rodada anterior, PostgreSQL auth/refresh não foi executado por pipe Docker negado e política `never`. Na retomada com permissões corrigidas, o Banco coordena o gate PG no código congelado; nenhum resultado PG foi produzido pelo Backend. Harness/guards offline não são um gate real.
- A hipótese ancestral/descendente foi confirmada pelo Banco na retomada real e recebeu o patch autorizado descrito abaixo; naquele checkpoint anterior não se adicionou correção especulativa. O gate pós-patch permanece separado e deve comprovar zero ativos.
- Logout/refresh concorrentes em PostgreSQL, rollouts entre instâncias, rate limit distribuído, recuperação de senha e verificação de email continuam fora desta validação. Não declarar auth certificada para produção por testes SQLite.
- Maestro executou a suíte API final acima e consolida os documentos compartilhados; build/browser estão bloqueados. Não alterar estes quatro arquivos de código/testes nem repetir execuções após o gate. Código está WIP local sem commit nesta entrega; backend em execução permanece intocado e não carrega o patch por esta auditoria.
- Banco recebeu contrato/freeze e mantém modelos/schema intactos; relatório `docs/database-auth-session-2026-10-02.md` distingue seus guards offline das reproduções Backend. Consolidar commits locais seletivos quando a escrita Git estiver habilitada; nenhum push autorizado.

## Bug PostgreSQL real confirmado e correção autorizada

Evidência produzida/revisada pelo **Banco**, não uma execução Backend: PostgreSQL18.6, READ COMMITTED, threads com Sessions/conexões independentes, serviço real. Resultado pré-patch `NOT_PASSED`: A→B sequencial; T1 rotaciona B e pausa em `Session.before_commit` com B consumido e C pendente; T2 faz replay A e espera no UPDATE de família, confirmado por `pg_blocking_pids`; T1 confirma C, T2 termina401, mas **um refresh permanece ativo**. O UPDATE de revogação iniciado antes do commit não incluiu o novo descendente no snapshot.

O mesmo token já passou com `[200,401]`/zero ativos; seis constraints/digests, ownership/expiração/logout antigo/cascata também passaram no gate pré-patch. Esses sucessos não anulam a falha de família. Artefatos ignorados `auth-postgres-gate-result.json`, `auth-postgres-gate-stages.json`, `auth-postgres-container.json`; SHA256 do resultado pré-patch informado pelo Banco: `58F8677746143D1B1E13025E78B327C6839DBB838D1FF4650B025EF368E3FD7F`. Serviço anterior: `A9E33814FD91A0CEA8148E1D3B8FD7E6A69BAD4EF9BB905A6D6880B7689E3289`. A instância descartável anterior foi verificada/removida pelo Banco; nenhum processo/dado existente foi alterado pelo Backend.

Autorização Maestro: corrigir `auth_service.py` e testes/relatório, sem schema, preservar contratos e reexecutar gate em nova instância/DB UUID vazia sob responsabilidade Banco. Patch:

1. PostgreSQL faz lookup do token **sem row lock**, somente para descobrir a família; token inexistente retorna401 sem adquirir locks.
2. Refresh e replay adquirem primeiro `pg_advisory_xact_lock` com chave signed64 derivada de SHA256(namespace `gandalf:refresh-family:` + UUID da família). A chave é estável entre ancestrais/descendentes e processos; a revogação continua filtrada pelo UUID completo da família. Lock transacional é liberado no commit/rollback.
3. Depois da espera, nova consulta `FOR UPDATE` com `populate_existing=True` relê estado ORM e snapshot em READ COMMITTED. Assim replay começa a revogação após o commit do descendente e enxerga o filho novo; se replay ganha antes, a rotação relê revogação e não emite sucessor.
4. Ordem família→linha uniforme em todas as entradas de refresh/replay; não adquirir linha de descendente antes da família. SQLite mantém o CAS existente, sem executar advisory lock. Logout por token, famílias independentes, JWT/ownership/erros503 e schema permanecem iguais.

Regressões novas, explicitamente **protocolo com SQLite/probe**, não PG real: estado ORM prévio é atualizado após uma revogação simulada durante a espera, impedindo sucessor; mesma chave ao longo de três gerações/replay e família independente preservada; token desconhecido não adquire locks; falha de advisory não chega ao row lock, faz rollback/503 e não consome token. Quatro casos novos acrescentados a `test_auth.py`.

Mesmo comando auth/security/plugin documentado acima: **52 passed** (30 auth +22 security), um aviso preexistente, **12,20s**. Ruff check PASS, quatro arquivos já formatados, diff-check seletivo PASS. Nenhuma suíte geral, teste multiprocessos ou chamada externa repetida nesta correção.

Novo freeze SHA256 dos bytes, enviado diretamente ao Banco:

| Arquivo | SHA256 |
| --- | --- |
| `api/app/core/security.py` — intacto | `78471D057A8440A1ED785214C1821CB73D461EBF96BA2F089A5FF479A59117F1` |
| `api/app/services/auth_service.py` | `86DDFB61F7639433319BD40ACB2F2890CCD74C241D37DA7B14837275861577ED` |
| `api/tests/test_auth.py` | `23B40CC451932B6D2679412FA2658CE8E26C07C9C4D995F4BB001F31501A5E7B` |
| `api/tests/test_security.py` — intacto | `F813B64AD7452C105982CADF48E3B67B3B4DC189907D7A7B3B4264564DD89D29` |

Código/testes congelados durante o gate Banco. Lista seletiva **desta correção**: `api/app/services/auth_service.py`, `api/tests/test_auth.py`, este relatório. Maestro reserva Git/documentos API/security/ADR/shared; nenhuma edição desses documentos, runtime existente, modelos/migrations, harness ou LLM pelo Backend. Todos os workers que participarem de uma família precisam usar a mesma estratégia de lock; mistura de versões anteriores não foi validada.

### Resultado real pós-patch — Banco

Banco executou nova instância PostgreSQL18.6 READ COMMITTED, fontes exatamente iguais ao novo freeze acima, serviço real e mesmas barreiras `before_commit`/observação `pg_blocking_pids`. Resultado **PASS**:

- Replay ancestral versus rotação descendente: espera confirmada, `rotation_status=200`, `replay_status=401`, **`active_tokens=0`**. A falha pré-patch tinha um ativo; agora o descendente não escapa da revogação.
- Mesmo token em duas sessões: `[200,401]`, zero ativos, cadeia consistente.
- Seis constraints negativas/digests, ownership/expiração/logout antigo/cascata passaram. Logout antigo continua preservando o descendente no caso sequencial, conforme contrato.

Evidências ignoradas `.impeccable/runtime/auth-postgres-gate-after-fix.json` e `auth-postgres-container-after-fix.json`; artefato anterior `NOT_PASSED` preservado. Única instância nova `gandalf-auth-gate-46953088037c42c582855e650a1c390f`, ID completo `63a8f6156bab0a59f5a6e3ef86062be2063dc5c442c46093b5db8dafbf9b74c5`, loopback55432/tmpfs/sem pull, removida pelo Banco após identidade reconferida. Nenhuma mudança em schema, serviços ou dados existentes.

Freeze final de código/testes/relatório liberado ao Maestro para revisão e commit seletivo. Nenhum novo teste/probe/Git/restart pelo Backend após essa confirmação; resultado PG é execução Banco revisada, distinta dos52 testes SQLite/probe deste terminal. Não certifica todos os isolamentos, rollout com versões mistas, HTTP auth entre múltiplas apps ou produção. Atualização de documentos compartilhados/API/security/ADR e deploy continuam coordenados pelo Maestro.
