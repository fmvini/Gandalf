# PostgreSQL/pgvector real em Docker — 2026-10-02

## Resultado

**PASS real nas duas execuções**: harness local anterior e script reutilizável após adaptação. PostgreSQL **18.6**, pgvector **0.8.6**, citext **1.8**. Nenhum bug de modelo/migration confirmado; schemas, serviços e dados existentes preservados.

| Execução | Evidência |
|---|---|
| Harness ignorado `.impeccable/runtime/postgres_gate.py` | PASS às **17:50:34.250 UTC**, Unix ms `1790963434250`, cinco grupos completos. |
| Reutilizável `api/scripts/postgres_gate.py` | PASS às **17:54:31.045 UTC**, Unix ms `1790963671045`, cinco grupos completos em outro banco vazio **no mesmo container**. |
| Proteções `api/tests/test_postgres_gate.py` | **17 testes passaram**, 1 aviso Starlette/httpx conhecido, 1,29 s; sem rede/banco. |
| Ruff check / format --check dos dois arquivos | PASS; dois arquivos formatados. |
| Stdout do script reutilizável | Um único objeto JSON final PASS; convertido/validado como JSON com cinco checks. Progresso e avisos em stderr. |

Artefato sanitizado local, ignorado: `.impeccable/runtime/postgres-gate-versioned.json`. Não contém senha/DSN. O resultado real substitui a limitação de disponibilidade anterior para **o escopo efetivamente testado**, sem reescrever relatórios históricos de quando Docker estava inacessível.

## Autorização, isolamento e identidade

- Partida em HEAD `8d94c76`; arquivos em progresso de Maestro/Backend/Frontend preservados. Usuário autorizou Docker, pull oficial, um container exclusivo, senha descartável e workers elevados. Banco não fez stage/commit/push.
- Docker elevado: Engine **29.8.0**, Desktop **4.92.0**, Linux/amd64. `docker ps` vazio inicialmente; imagens locais só gandalf-api/frontend. Portas 55432/55433 conferidas livres antes de criar.
- Pull oficial `pgvector/pgvector:0.8.6-pg18` com TLS padrão, sem desabilitar verificação.
- **Digest/imagem**: `sha256:2ba9ca5f2e7daa0f0e7723cba1ee9167bab54efd3640516a44ac1a928dd67e7a`.
- **Único container criado**: `gandalf-pg-gate-8d7b7c36004b4df88bb7f42cfa92f828`.
- **ID completo**: `9c68980b190300fedf9573faa33d6dcb467e3c18135ec6cb3e9f410482611a00`.
- Label `com.gandalf.disposable-gate=true`, publicação exclusivamente **127.0.0.1:55432→5432**; um único mount **tmpfs `/var/lib/postgresql`**, sem bind/volume existente. Identidade/label/mount/porta verificados antes do harness.
- Usuário de teste `gandalf_gate`; primeira base `gandalf_gate_8d7b7c36004b4df88bb7f42cfa92f828`, segunda `gandalf_gate_de48d2f912dd4045a4e256178d8804fa`. Segunda base criada vazia no mesmo container para não relaxar recusa a schema ocupado: downgrade base deixa tabela Alembic na primeira.
- Senha nova aleatória de teste nunca impressa. Estado local com senha, ignorado, usado só para a execução e apagado após a remoção do container. Não usadas credenciais de PostgreSQL18/API/prod.

## Checks reais aprovados

1. `real_migrations_metadata_extensions_readiness`: base→0007, duas contas sintéticas, upgrade→0008/head, paridade metadata/schema sem diffs, READ COMMITTED confirmado, extensões instaladas pela migration. Operações reais de distância vector e igualdade CITEXT; readiness 200 com pgvector `ok` via TestClient local/offline.
2. `multiprocess_upsert_first_snapshot_owner_isolation`: seis criações equivalentes em três processos independentes, um ID e exatamente uma criação; POST repetido mantém primeiro item/data/proveniência; data timezone-aware; DELETE/status por outra conta não alcançam o favorito.
3. `multiprocess_create_delete_returning`: dois processos criando/repetindo e um excluindo, 20 operações por processo; snapshots retornados corretos durante a corrida e contagem final ≤1, com criação final disponível. Usa serviço real/SQLAlchemy/postgresql+psycopg, sem substituir worker por fake/thread.
4. `postgres_advisory_cache_capacity_ttl_snapshot_cascade`: TTL na fronteira e sem renovação em leitura/repetição; três processos publicando/lendo 95 origens cada, capacidade global final **256** pelo lock PostgreSQL real. Favorito permanece após remover origens; cascata de conta elimina seu favorito e preserva outra conta.
5. `downgrade_upgrade_preserves_other_owner_then_base`: downgrade0008→0007 preserva outra conta, upgrade→head, downgrade→base remove tabelas da aplicação e deixa somente Alembic.

Não executada suíte SQLite integral nem chamadas externas/LLM neste gate. Nenhuma nova migration necessária.

## Implementação reutilizável e proteções

Arquivos entregues para revisão/commit seletivo do Maestro:

- `api/scripts/postgres_gate.py`: script executável desde a raiz ou `api/`, resolve Alembic pela própria localização e usa `Config.attributes['connection']`, sem escolher alvo por DATABASE_URL/.env. `main()` retorna código de saída; estágios em stderr e único JSON final PASS/NOT_PASSED em stdout; erro informa somente classe/etapa segura, sem dump de exceção/SQL/DSN/senha.
- `api/tests/test_postgres_gate.py`: nove URLs perigosas recusadas **antes de criar engine**, duas portas/UUID de CI aceitos, quatro estados de preflight perigosos recusados **antes de migration/transação de escrita**, execução sem coordenação recusada e saída de falha sanitizada/stdio verificada.
- Este relatório exclusivo; DEVELOPMENT_LOG/CONTINUATION/IMPLEMENTATION_STATUS, `.github/workflows/ci.yml` e `docs/CI.md` pertencem ao Maestro.

Guards: `postgresql+psycopg`, loopback 55432/55433, usuário `gandalf_gate`, DB `gandalf_gate_{32hex}`, sem query de redirecionamento, database/user real conferidos, nenhum objeto de usuário e extensões disponíveis antes de escrever. Flag `GANDALF_PG_GATE_ALLOW=isolated-coordinated`; Python `-O` recusado. Timeout de conexão 5 s e statement 15 s. Recusa/erro gera exit 1, não PASS parcial; em falha deixa banco **descartável** para diagnóstico, sem auto-drop/prune.

O DB de CI proposto pelo Maestro, `gandalf_gate_00000000000000000000000000000001`, é aceito e consta nos testes. Comandos do script, **somente com instância descartável coordenada e variáveis de teste já configuradas**:

```powershell
.\api\.venv\Scripts\python.exe api/scripts/postgres_gate.py
```

```bash
# working-directory: api; env de teste isolado, nunca URL/credenciais existentes
python scripts/postgres_gate.py > postgres-gate.json
```

SHA256 dos arquivos congelados:

- Script: `FAEDD92AC0957F6D1078915F69AD9B3EDC51B0296CDE68ED8582530079E73D68`.
- Testes: `1B988851144605FEFA52A05A84CE2161C3CA1513F5456E45DE1723A6DA225649`.

## Limpeza e preservação final

Após capturar os dois PASSs, conferidos novamente **ID completo + nome + label + único tmpfs + loopback55432**, executado `docker rm -f` somente nesse ID. Consulta por ID não encontrou container restante. Arquivo ignorado de estado com senha removido por caminho literal verificado dentro do workspace; nenhum prune/remoção de imagem/volume/banco geral.

Listeners finais: **PostgreSQL18 PID10140/5432**, **API PID31444/127.0.0.1:8000**, **Frontend PID25716/::1:5173** preservados; 55432/55433 sem listener após limpeza. Imagem oficial baixada permanece local para próximas rodadas, sem outro container criado por Banco.

## Limites e continuidade

- Gate real local aprovado **nos cinco grupos acima**, usando workers Windows elevados contra PostgreSQL Linux no Docker. CI Ubuntu hospedada ainda não executada; job/artefato pertencem à entrega do Maestro. Não declarar CI verde só pelo gate local.
- Stress concorrente não determina todas as interleavings; testes de bloqueio controlado, todas as constraints negativas PostgreSQL, HTTP autenticado entre duas instâncias e refresh concorrente ainda não fazem parte deste harness. Não afirmar certificação integral de produção/migração de dados reais.
- Antes de reaplicar, escolher DB descartável vazio: guard recusa a tabela Alembic deixada por rodada anterior. Usar novo DB/container isolado e senha de teste, nunca PG18/5432/compose volume do usuário.
- Maestro integrar script/testes/relatório e CI/docs sob sua reserva, executar os guards se revisar a implementação, e registrar hashes/resultado nos três documentos compartilhados. Banco libera freeze dos três arquivos acima, sem stage/commit e sem novas edições/testes/probes nesta unidade após entrega, salvo solicitação.
