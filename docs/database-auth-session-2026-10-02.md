# Auditoria de persistência e concorrência auth — 2026-10-02

## Adendo Maestro — regressão versionada aprovada às 22:32 UTC

Após a liberação deste relatório pelo Banco, Maestro concluiu `api/scripts/postgres_auth_gate.py` e `api/tests/test_postgres_auth_gate.py`. A coleta executada corretamente em `api` passou: **20 testes offline**, mais **12 recusas CLI**, Ruff/formatação e actionlint PASS. O snapshot início/fim conserva a proteção contra fontes alteradas durante o gate, sem pins permanentes da sessão. O lifecycle Docker permanece em runner ignorado separado.

**Nova execução REAL do script versionado: PASS PostgreSQL18.6/READ COMMITTED**, mesmas fontes congeladas e quatro grupos abaixo. Mesmo-token200/401/zero ativos/chain consistente; ancestral rotação200/replay401/bloqueio observado/zero ativos; seis constraints/digests e ownership/logout antigo/expiração/cascata aprovados. Executado literalmente também o trecho Python da CI que valida a identidade e cria outro DBUUID vazio com Identifier; aprovado. Nenhum schema anterior reutilizado.

- Instância única desta terceira rodada: `gandalf-auth-gate-247930c87b604d54bec3645e5e0f0698`, ID `17a5651946630d28e86d8a9807c2fb934a96c9e5cc132f8a7c03c9e784af09b7`; DB auth `gandalf_gate_df70aeec66094161bb658925226b02a3`, além do DB inicial exclusivo da instância. Mesma imagem oficial local/digest abaixo, pull=never, labels UUID, tmpfs e bind127.0.0.1:55432.
- Identidade conferida antes/depois, removida somente essa instância; início22:32:49UTC/fim22:32:54UTC, `removed_identity_verified=true`. Segredo descartável não aparece nas evidências; arquivo temporário de ambiente da etapa CI removido no finally.
- Evidências distintas ignoradas: `.impeccable/runtime/auth-postgres-versioned-result.json`, `auth-postgres-versioned-stages.json`, `auth-postgres-versioned-container.json`. Before/after do Banco preservados.
- Workflow passa a coletar `postgres-auth-gate.json` e usar segundo banco vazio no serviço descartável da CI. **CI hospedada não executada**; limites de HTTP duas apps, rollout/mistura de versões e demais corridas permanecem. Os registros de entrega pendente abaixo descrevem o checkpoint anterior a este adendo.

## Resultado consolidado — antes NOT_PASSED, depois PASS real

**O harness ignorado passou no PostgreSQL18.6 após o patch Backend, nos quatro grupos abaixo.** A mesma reprodução controlada de replay ancestral versus rotação descendente que deixou um token ativo antes da correção terminou com **zero ativos** depois. Foram duas execuções sequenciais, cada uma em **uma instância exclusiva diferente**, ambas removidas após reconferir identidade. Nenhum schema/model/migration alterado pelo Banco; não usada a instância PostgreSQL5432 nem seus dados/volumes.

| Evidência real / READ COMMITTED | Antes — 22:12 UTC | Depois — 22:19 UTC |
|---|---|---|
| Constraints e digests | PASS, seis negativas | PASS, mesmas seis negativas |
| Mesmo refresh em duas sessões | 200/401, zero ativos, cadeia consistente | 200/401, zero ativos, cadeia consistente |
| Ancestral replay × descendente refresh | Espera confirmada; rotação200/replay401; **um ativo**, critério FAIL | Espera confirmada; rotação200/replay401; **zero ativos**, critério PASS |
| Ownership / expiração / logout / cascade | PASS | PASS |
| JSON terminal | **NOT_PASSED** | **PASS** |

### Correção Backend e segunda execução

Backend implementou descoberta de family_id sem row lock, `pg_advisory_xact_lock` com chave int64 signed derivada de SHA256(namespace+UUID), depois releitura SELECT FOR UPDATE/populate_existing. Refresh e replay seguem essa ordem; SQLite CAS e logout somente do token informado permanecem. Banco não editou AuthService. Na reprodução pós-patch mantiveram-se hooks `before_commit`/`pg_blocking_pids`, sessões/conexões independentes e critério zero ativos; agora T2 espera a serialização da família antes de ler/buscar as linhas a revogar. Não houve mock do algoritmo nem redução de assertions.

Freeze final recebido e conferido antes de rodar; snapshot final das fontes iguais ao inicial:

| Fonte pós-patch | SHA256 |
|---|---|
| `api/app/core/security.py` | `78471D057A8440A1ED785214C1821CB73D461EBF96BA2F089A5FF479A59117F1` |
| `api/app/services/auth_service.py` | `86DDFB61F7639433319BD40ACB2F2890CCD74C241D37DA7B14837275861577ED` |
| `api/tests/test_auth.py` | `23B40CC451932B6D2679412FA2658CE8E26C07C9C4D995F4BB001F31501A5E7B` |
| `api/tests/test_security.py` | `F813B64AD7452C105982CADF48E3B67B3B4DC189907D7A7B3B4264564DD89D29` |

Os **52 PASS auth30/security22** informados pelo Backend são evidência separada SQLite/fakes, não a execução Banco PG. Banco não duplicou aquela suíte. Antes de executar novamente, 12 recusas offline e dois checks de freeze passaram; Ruff do harness passou. SHA256 do harness ignorado efetivamente usado depois: `6355B6E4E3495496F8F8B2F3F9B9AB8211D8DC129A98BB2A186306008B719E05`.

### Identidade e cleanup pós-patch

- Container `gandalf-auth-gate-46953088037c42c582855e650a1c390f`, ID completo `63a8f6156bab0a59f5a6e3ef86062be2063dc5c442c46093b5db8dafbf9b74c5`; DB vazio `gandalf_gate_46953088037c42c582855e650a1c390f`, usuário gandalf_gate e senha nova somente na memória/ambiente dos filhos.
- Imagem oficial **local/pull=never**, digest/image ID `sha256:2ba9ca5f2e7daa0f0e7723cba1ee9167bab54efd3640516a44ac1a928dd67e7a`; labels disposable-gate=true/auth-gate=UUID, único tmpfs `/var/lib/postgresql`, único bind127.0.0.1:55432→5432. ID/nome/labels/image/mount/porta verificados antes do harness e antes da remoção específica.
- Início **22:19:55 UTC**, evidência e remoção concluídas **22:20:00 UTC**. Consulta posterior: container ausente/inventário vazio, 55432/55433 livres; PostgreSQL5432 PID10140 observado. Não houve prune, volume geral, instalação, pull, LLM nem comando de escrita em serviço/banco existente.
- Evidências sanitizadas preservadas: `.impeccable/runtime/auth-postgres-gate-after-fix.json` (**PASS**), `auth-postgres-container-after-fix.json` (identity/removed_identity_verified=true). SHA256 JSON pós-patch `B2D1D7D909B65A8CC200D7A5A9593E496271A3506AD4DCB42C0EC342C89FF76D`. Artefatos before-fix abaixo preservados separadamente. Nenhum segredo/DSN/SQL foi incluído nesses JSONs.

### Regressão versionada — pendente e reservada exclusivamente ao Maestro

Após PASS do harness ignorado, Banco preparou candidatos `api/scripts/auth_postgres_gate.py` e `api/tests/test_auth_postgres_gate.py`, com snapshot de fontes no início/fim e sem pins permanentes da sessão. CLI offline do candidato passou em 12 recusas; Ruff/formatação passaram. **A coleta dos testes, invocada da raiz, falhou com ModuleNotFoundError: scripts; nenhum teste versionado passou naquela tentativa. O candidato versionado não foi executado em PostgreSQL pelo Banco.** Não converter o PASS do harness ignorado em aprovação do candidato.

Maestro assumiu exclusivamente candidatos, renomeação final para `api/scripts/postgres_auth_gate.py` / `api/tests/test_postgres_auth_gate.py`, runner, testes e gate versionado/CI. Banco não editará/executará esses arquivos nem criará nova instância. Maestro deve resolver a coleta, validar guards e o script versionado em DBUUID vazio próprio e preservar artefato separado, sem reaproveitar schema do gate geral. Esses passos permanecem pendentes neste relatório Banco; nenhuma validação antecipada.

**Freeze/liberação Banco:** somente este documento consolidado nesta entrega final. Reservas de código/runner já transferidas ao Maestro; documento também liberado após envio. Sem Git/shared docs/ADR/contrato. Limites: gate real local cobre os quatro grupos e a interleaving reproduzida, usando threads com sessões independentes; não certifica stress multiprocessos, HTTP entre duas apps, corrida logout/refresh/desativação/exclusão, falhas de commit reais PG, CI hospedada ou segurança integral de produção.

## Adendo — execução real e bug confirmado às 22:12 UTC

Após o usuário corrigir permissões e manter autorização para Docker isolado, normal continuou negando o pipe, mas preflight elevado com auto_review funcionou. `docker ps` vazio e digest oficial local conferido; nenhum pull. **Primeiro gate real auth: NOT_PASSED**, PostgreSQL18.6 (Debian18.6-1.pgdg12+2), READ COMMITTED, hashes congelados exatamente iguais ao adendo Backend abaixo. O risco de replay ancestral deixou de ser apenas hipótese neste caso controlado.

| Check real | Resultado |
|---|---|
| Constraints/digest | PASS: seis rejeições reais (email/username CITEXT duplicados, username curto, senha NOT NULL, digest refresh duplicado, owner inexistente FK); Argon2id/SHA256 e FK CASCADE. replaced_by sem FK confirmado por inspector. |
| Mesmo token / duas sessões | PASS: respostas200/401, zero tokens ativos, duas linhas com replacement do mesmo owner/família. |
| Replay ancestral / rotação descendente | **FAIL do critério**: bloqueio observado, rotação200, replay401, **um token ativo** após ambos commits. Resultado final NOT_PASSED; não erro ambiental nem aprovação parcial. |
| Ownership / expiry / logout / cascade | PASS: outro owner não revoga; token expirado401; logout atual invalida, antigo preserva descendente conforme contrato; excluir conta sintética elimina seus refresh. |

Reprodução exata no harness real: login gera A; refresh(A) gera B. T1 refresh(B) executa UPDATE condicional de consumo e pausa no `Session.before_commit`, antes de inserir/commit do replacement C. T2 refresh(A) reapresenta token consumido e tenta UPDATE de revogação da família. Uma terceira conexão consulta `pg_blocking_pids` e confirma T2 esperando T1; só então libera o commit de T1. T2 termina401, mas C permanece como o único token ativo da família. Não substituído algoritmo AuthService; hooks/barreiras apenas determinam interleaving. Não houve chamada adicional de refresh(C); a evidência é o estado persistido ativo após as duas operações.

### Isolamento, evidências e limpeza

- Único container desta primeira execução: `gandalf-auth-gate-81086dd1d3a640a1b129b2854320fee6`, ID `ff9a525dd85c621b6a63737b0df0ea0ec2ea60925dabcfcc78783430dbd3b3d4`.
- DB `gandalf_gate_81086dd1d3a640a1b129b2854320fee6`, usuário gandalf_gate, senha aleatória somente na memória/ambiente de processos filhos; nenhum arquivo de senha.
- Labels disposable-gate=true/auth-gate=UUID; único tmpfs `/var/lib/postgresql`, único bind127.0.0.1:55432→5432; digest/image ID `sha256:2ba9ca5f2e7daa0f0e7723cba1ee9167bab54efd3640516a44ac1a928dd67e7a`. Identidade verificada antes do harness e reconferida antes de remover somente esse ID.
- Início **22:12:34 UTC**, evidência e remoção concluídas **22:12:38 UTC**. Inventário posterior vazio, ID ausente, portas55432/55433 livres. Listener PostgreSQL5432 PID10140 e frontend5173 PID25716 observados. Não observado listener8000 nessa consulta; nenhuma ação Banco o iniciou/parou, sem alegar estado anterior da API por esse snapshot.
- Artefatos sanitizados ignorados preservados antes de próxima rodada: `.impeccable/runtime/auth-postgres-gate-before-fix.json` (cópia do JSON terminal), `auth-postgres-stages-before-fix.json`, `auth-postgres-container-before-fix.json` (identidade/remoção, sem env/senha). Os nomes genéricos result/stages/container são saídas da última execução do runner. SHA256 resultado anterior `58F8677746143D1B1E13025E78B327C6839DBB838D1FF4650B025EF368E3FD7F`.
- Lifecycle separado no runner ignorado `.impeccable/runtime/run_auth_postgres_gate.py`, SHA256 após formatação/checks `8912E579DC84B8D2F3F2A1A13A04EE89394C38EAE78738E609ECD20D7FB805F2`; não versionado. Flags/check=False/comentários sanitizados ajustados após execução sem alterar comportamento. Sem reexecução por esses ajustes de lint. Harness frozen permaneceu `BB403D38A3E3DEBA0FD6427F5F4EF2A3F0E806EE6A9C9DE04BC85ECBD27BD3D8`.

Backend/Maestro receberam JSON/caminhos/hashes e reprodução. Naquele checkpoint Maestro autorizou Backend corrigir serialização antes rowlocks/releitura **sem schema**, e Banco aguardava freeze para executar novamente. A execução posterior e a transferência da regressão versionada ao Maestro constam na consolidação acima. Os registros offline abaixo são históricos.

## Histórico — resultado e escopo da fase offline

**Na fase offline, refresh concorrente PostgreSQL estava pendente.** Docker recusou acesso ao pipe `dockerDesktopLinuxEngine` (`permission denied`); a política então vigente era `approval never`. Maestro confirmou a mesma restrição e determinou entrega offline, sem elevar nem contornar. Nenhum container foi criado ou banco conectado naquela fase. A autorização/permissão posterior e as duas execuções reais estão registradas acima.

Leitura: DEVELOPMENT_LOG/CONTINUATION, ADR-0006, Security Specification, API/Data Model, models/account, migration0002, AuthService/security, session dependency e testes auth existentes. Serviços, modelos, migrations e testes reservados ao Backend não foram editados. Git e documentos compartilhados pertencem ao Maestro; sem stage/commit/push neste terminal.

## Contrato e achados estáticos

| Área | Garantia atual / limite concreto |
|---|---|
| Conta | Model e migration0002 concordam: UUID PK; email e username `CITEXT UNIQUE NOT NULL` no PG; username com CHECK de comprimento 3–32. SQLite usa String; casefold no serviço. Validação de formato/comprimento da senha pertence ao schema de entrada, não ao banco. |
| Senha | Coluna TEXT NOT NULL; serviço grava Argon2id com salt da biblioteca e rehash no login. O banco não valida sintaxe Argon2 nem proíbe texto arbitrário inserido diretamente. Não foi examinada nenhuma senha/digest de conta real. |
| Refresh | Digest SHA-256 hexadecimal de token opaco gerado com 48 bytes aleatórios; coluna VARCHAR64 UNIQUE NOT NULL. Índices em user_id/family_id/expires_at. Nenhum CHECK garante hexadecimal ou comprimento exato; isso é invariante do serviço. |
| Ownership | `user_id` referencia users.id com CASCADE. `family_id` é UUID sem entidade/FK própria. `replaced_by_id` é UUID nullable **sem FK** e não garante mesmo owner/família por constraint. O serviço copia owner/família na rotação. Não há bug de schema confirmado nem migration proposta. |
| Tempo/revogação | expires_at timestamptz NOT NULL; revoked_at nullable. Serviço recusa expires_at ≤ agora, conta ausente/inativa e token revogado. Rotação renova prazo de 7 dias por padrão; não há expiração absoluta de família no contrato atual. |
| Mesmo token | SELECT FOR UPDATE serializa a linha no PG. O contrato espera um sucesso e um401; a segunda apresentação de token consumido revoga a família, inclusive o replacement emitido pela primeira. SQLite não fornece esse lock. |
| Logout | Contrato confirmado pelo Backend: revoga apenas o token informado, ativo e pertencente ao owner. Logout de token já rotacionado é no-op204; descendente continua válido. Access token expira naturalmente. Isso não equivale a revogação integral da sessão/família. |

A FK isolada em replaced_by_id não resolveria a serialização da família. Sua eventual inclusão exigiria contrato de ordem de insert/update, possível constraint diferida, ownership e exclusão; nenhuma alteração deve ser feita incidentalmente.

Na leitura inicial, verify_password capturava VerificationError, mas `issubclass(InvalidHashError, VerificationError)` resultou **False** na biblioteca instalada. Register tratava IntegrityError; login/refresh/logout não convertiam todas as falhas SQL em503 com rollback explícito. A dependência fecha a Session no final, desfazendo transação pendente; isso não fornece a mesma semântica de erro do serviço. Esses achados foram enviados ao Backend.

**Evidência Backend, não execução Banco:** seis reproduções antes FAIL e depois PASS — digest inválido401, corrida SQLite com um200/um401 e duas linhas revogadas, quatro falhas de commit com rollback503. Backend informou UPDATE condicional para consumo (`id`, revoked_at NULL, expires_at futuro), além de FOR UPDATE no PG. Seus arquivos estavam WIP durante a preparação; exigir freeze antes do gate. Não duplicada a suíte auth/SQLite/HTTP.

## Histórico — análise do risco antes da reprodução

Sequência proposta: A foi rotacionado para B. T1 rotaciona B, mantém sua linha bloqueada e pausa antes do commit. T2 reapresenta A e tenta revogar os tokens ativos da família. Confirmar com `pg_blocking_pids` que T2 espera T1, então liberar o commit de T1 e observar se o novo C continua ativo.

READ COMMITTED procura linhas no snapshot do início do comando e reavalia uma linha alterada após esperar seu lock; isso não torna visíveis todas as inserções concorrentes ao mesmo UPDATE. Assim, revogação por um único UPDATE de família **pode** deixar um descendente inserido depois do snapshot. Na análise inicial isso era inferência aceita pelo Backend, ainda sem reprodução. O gate real acima posteriormente confirmou o escape e validou o patch no mesmo cenário. [Documentação oficial PostgreSQL18](https://www.postgresql.org/docs/18/transaction-iso.html).

Critério do gate: replay401, rotação200, bloqueio observado e **zero tokens ativos** na família após ambas as transações. Se houver escape real, Backend avalia serialização da família antes dos row locks, com releitura/ordem consistente e testes; não aplicar patch especulativo nem nova migration agora.

## Harness ignorado e checks offline

O caminho citado na retomada estava ausente (`Get-Content: PathNotFound`). Reconstruído exclusivamente `.impeccable/runtime/auth_postgres_gate.py`, confirmado ignorado pelo Git. Não versionado nem integrado ao CI.

- Reutiliza validate_target/engine_for/validate_database de `api/scripts/postgres_gate.py`: postgresql+psycopg, loopback, 55432/55433, usuário gandalf_gate, DB gandalf_gate_{32hex}, sem query redirects; identidade real, banco vazio e extensões disponíveis antes da migration. Connection timeout5s/statement15s.
- Flag própria `GANDALF_AUTH_PG_ALLOW=isolated-coordinated-backend-frozen`; URL somente `GANDALF_AUTH_PG_URL`, nunca DATABASE_URL/.env. Settings de teste com segredo novo em memória e provedores offline; não inicia app/HTTP/LLM.
- Planeja upgrade head em banco vazio; constraints negativas CITEXT/unicidade/username/NOT NULL/FK e digest; mesma apresentação em duas sessões; replay ancestral com barreira e bloqueio observado; ownership/logout/expiração/cascade. Hashes das fontes conferidos antes/depois da execução. Threads têm Sessions/conexões independentes: não alegar multiprocessos.
- Stdout: um JSON final PASS/NOT_PASSED; estágios em stderr. Erro mostra apenas classe/etapa, sem exception dump, SQL, DSN ou senha. NOT_PASSED em interleaving não observado ou checks reprovados; sem PASS parcial. Não faz lifecycle Docker nem remoção de banco/container.

Às **21:57:23 UTC**, offline:

```text
{"status":"OFFLINE_GUARDS_PASS","refusals":12,"integration_executed":false}
```

Oito URLs perigosas recusadas antes de criar engine: portas5432/5433/8000, host remoto, query host redirect, usuário postgres, DB sem UUID e driver SQLite. Quatro estados recusados no preflight: banco ocupado, database diferente, usuário diferente, extensão ausente. Execução sem coordenação recusou com NOT_PASSED/coordination/ValueError. Ruff check e format --check passaram. Aviso Starlette/httpx conhecido no import; nenhuma instalação.

SHA256 do primeiro freeze do harness: `04885E1E78DFF1768A258D1410F661298CE5A0757EEB7B4AF551A27B3D2E12CC`, substituído pelo adendo abaixo.

### Adendo — freeze Backend e hashes fixados

Backend confirmou freeze dos quatro arquivos a seguir sobre base HEAD `13e0a495bf8e3a1391d4484a42a29a5e845e0a3a`, com WIP sem commit. Reportou **48 PASS finais: auth26/security22**, exclusivamente SQLite temporário/pluginACL; não execução Banco nem PG. Mesmo token: um200/um401/zero ativos; replay afeta somente a mesma família; logout antigo no-op204 e access JWT continua até expiração. Nenhum family lock hipotético acrescentado; risco ancestral/descendente PG continua pendente.

| Arquivo | SHA256 dos bytes congelados |
|---|---|
| `api/app/core/security.py` | `78471D057A8440A1ED785214C1821CB73D461EBF96BA2F089A5FF479A59117F1` |
| `api/app/services/auth_service.py` | `A9E33814FD91A0CEA8148E1D3B8FD7E6A69BAD4EF9BB905A6D6880B7689E3289` |
| `api/tests/test_auth.py` | `AE143FCFD89CFF02B06E1EDF5BF3E1D03B142C6F86A1C630D49CC7614F05C599` |
| `api/tests/test_security.py` | `F813B64AD7452C105982CADF48E3B67B3B4DC189907D7A7B3B4264564DD89D29` |

Harness ignorado atualizado com `EXPECTED_FROZEN`: exige esses hashes **antes de criar engine/conectar**, além de conferir as fontes novamente ao final. Dois checks offline adicionais passaram: fontes atuais aceitas; alteração simulada recusada antes de criar engine. Resultado: **12 recusas + 2 checks de freeze, integração false**; Ruff check e formatação passaram. Hashes são de bytes, portanto eventual conversão LF/CRLF também exige nova revisão/coordenação antes de fixar outra referência.

SHA256 **atual** do harness congelado: `BB403D38A3E3DEBA0FD6427F5F4EF2A3F0E806EE6A9C9DE04BC85ECBD27BD3D8`. Não executado Docker nem PG neste adendo.

## Receita mínima da próxima sessão com permissão

1. Ler este relatório e confirmar freeze/hash com Backend; revisar o harness ignorado, pois não acompanha o checkout. Conferir Docker autorizado, imagem local/digest, inexistência de instância duplicada e porta livre. Não repetir tentativa elevada na política never.
2. Criar **uma** instância UUID com imagem oficial local `pgvector/pgvector:0.8.6-pg18`, digest esperado `sha256:2ba9ca5f2e7daa0f0e7723cba1ee9167bab54efd3640516a44ac1a928dd67e7a`. Sem pull, compose, bind ou volume. DB gandalf_gate_UUID e usuário gandalf_gate; senha nova descartável transmitida somente no ambiente do processo filho, não literal em comando/log. Os argumentos abaixo são uma receita, **não foram executados**:

```powershell
# UUID, senha e env do processo filho devem ser preparados pelo runner isolado.
docker run --pull=never -d --name $authGateName `
  --label com.gandalf.disposable-gate=true `
  --label com.gandalf.auth-gate=$authGateUuid `
  --mount type=tmpfs,destination=/var/lib/postgresql,tmpfs-size=536870912 `
  --publish 127.0.0.1:55432:5432 `
  --env POSTGRES_USER=gandalf_gate --env POSTGRES_DB=$authGateDatabase `
  --env POSTGRES_PASSWORD pgvector/pgvector:0.8.6-pg18
```

Se55432 ocupado, conferir55433 e adaptar apenas a publicação/URL. Não usar5432/5433. Registrar ID completo retornado. Inspecionar exclusivamente campos seguros: ID/nome/labels, image digest, Mounts e NetworkSettings.Ports; **não imprimir Config.Env**. Exigir único tmpfs e único bind de porta loopback correto antes de conectar. Aguardar pg_isready dentro desse ID, com timeout limitado.

3. Após identidade validada, configurar no processo filho somente as duas variáveis próprias do harness, com URL de teste correspondente; então:

```powershell
.\api\.venv\Scripts\python.exe .impeccable/runtime/auth_postgres_gate.py --guard-checks
.\api\.venv\Scripts\python.exe .impeccable/runtime/auth_postgres_gate.py > .impeccable/runtime/auth-postgres-gate-result.json
```

Guardar JSON sanitizado e hashes; reportar falha ao Backend antes de ampliar patch. Guard de banco vazio impede reaplicar sobre schema da rodada anterior; planejar nova base UUID vazia no mesmo container se uma correção precisar reexecução, sob coordenação. Nenhum downgrade ou limpeza de banco existente automática.

4. Após capturar evidências, reconferir **ID completo + nome + ambas labels + único tmpfs + porta loopback**. Remover somente aquele ID com `docker rm -f $authGateContainerId`; nunca prune/volumes gerais. Apagar somente eventual estado ignorado de senha criado pelo runner com caminho literal verificado e conferir liberação da porta.

## Histórico — limites da entrega offline

Na entrega offline não havia resultado real PG auth; posteriormente ocorreram os dois gates registrados na consolidação. Não foram executados HTTP em duas apps, corrida logout/refresh controlada nem corrida com desativação/exclusão de conta. Logout antigo foi incorporado como caso sequencial conforme contrato. Gate PG anterior de migrations/favoritos/cache continua evidência independente; a evidência auth é a execução própria descrita acima, e a regressão versionada permanece sob responsabilidade exclusiva do Maestro.

Schema/dados/TTL/API8000/PG5432/frontend/credenciais existentes preservados; sem redes externas/LLM. Arquivos entregues: este documento exclusivo e harness ignorado. Freeze Banco: nenhuma nova edição/probe/teste após entrega sem solicitação. Maestro serializa documentação compartilhada e eventual commit quando Git permitir.
