# Backend — auditoria e correções de autenticação — 2026-10-02

## Estado e reserva

Código/testes congelados e entregues ao Maestro para gate final. Base consultada: `13e0a495bf8e3a1391d4484a42a29a5e845e0a3a`, `docs/DEVELOPMENT_LOG.md`, `api/README.md`, ADR-0006, especificações API/security e instruções AGENTS fornecidas pelo usuário. Não houve stage/commit/push pelo Backend; Git e documentos compartilhados pertencem ao Maestro, que informou bloqueio de escrita Git nesta sessão.

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
- Hipótese pendente: em READ COMMITTED, replay de ancestral versus refresh simultâneo de descendente pode deixar novo filho fora do snapshot do `UPDATE` de revogação da família. Não reproduzida nesta sessão; não foi adicionada serialização por família ou migration especulativa. O Banco preparou harness ignorado com `before_commit`/`pg_blocking_pids`; executar apenas com permissão futura e banco exclusivo.
- Logout/refresh concorrentes em PostgreSQL, rollouts entre instâncias, rate limit distribuído, recuperação de senha e verificação de email continuam fora desta validação. Não declarar auth certificada para produção por testes SQLite.
- Maestro executou a suíte API final acima e consolida os documentos compartilhados; build/browser estão bloqueados. Não alterar estes quatro arquivos de código/testes nem repetir execuções após o gate. Código está WIP local sem commit nesta entrega; backend em execução permanece intocado e não carrega o patch por esta auditoria.
- Banco recebeu contrato/freeze e mantém modelos/schema intactos; relatório `docs/database-auth-session-2026-10-02.md` distingue seus guards offline das reproduções Backend. Consolidar commits locais seletivos quando a escrita Git estiver habilitada; nenhum push autorizado.
