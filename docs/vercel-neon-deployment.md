# Publicação gratuita: Vercel e Neon

## Estado em 2026-10-04

Projeto `fmvini-projects/gandalf` criado e vinculado pela CLI oficial 62.2.0; usuário conectou o GitHub `fmvini/Gandalf`. A equipe foi verificada no plano **Hobby**, com raiz de build do repositório, sem override de frontend. **Publicado e validado:** [https://gandalf-gray.vercel.app](https://gandalf-gray.vercel.app).

Deployment `dpl_4dWeCn2dWxYoWUgRbprmJ4hd62kY`, READY/production, revisão `813436c24f259ec3195e139b51271ae9e956e119`, região de execução `gru1`. Build hospedado passou: frontend Vite5,13s e FastAPI/Python3.12/uv, 25s total. O build executou em iad1; isso não altera a região gru1 confirmada no deployment. A URL production é pública sem bypass; a URL efêmera do deployment tem proteção Vercel.

Usuário forneceu o projeto Neon `round-rice-47636561`, branch `production` (`br-dark-poetry-b6lwlbso`), em `aws-sa-east-1`; organização verificada no plano **Free**, PostgreSQL 18.6. Não foi criado outro projeto ou recurso marketplace. O pedido anterior de aceite de termos da integração Vercel foi substituído pelo vínculo manual solicitado.

Arquitetura preparada: frontend Vite estático e API FastAPI no mesmo projeto/domínio, via [Vercel Services](https://vercel.com/docs/services), disponível em todos os planos e ainda em beta. PostgreSQL Neon **Free**, com `citext` e `vector`, conserva SQLAlchemy, migrations e autenticação existentes. Não contratar upgrade, adicionar cobrança automática ou ativar trial pago. Os planos gratuitos têm limites de uso; não representam disponibilidade ou capacidade ilimitadas.

`vercel.json` usa região `gru1` para API próxima do banco em São Paulo. O frontend é distribuído pela CDN. Não foram alterados os outros projetos Vercel da conta.

CLI Neon 8.0.5 instalada conforme pedido; login concluído, skills locais e MCP configurados pela CLI. `neon link` vinculou projeto/branch e salvou somente variáveis Neon em `.env.local`, ignorado. `neon config init` criou manifest/lock; `neon.ts` foi substituído pelo conteúdo exato solicitado `defineConfig({})`. `neon config plan` e `neon deploy` PASS sem mudanças remotas, apenas Postgres. MCP `-y` instalou a chave no escopo de conta nos clientes detectados; nenhum valor da chave entrou no Git/artifacts/upload.

## Contrato de execução

- Serviço `api`: raiz `api/`, FastAPI, `vercel_app:app`; Python 3.12, igual ao ambiente dos testes e Docker. Settings exclusivamente do ambiente, PostgreSQL Neon/TLS e JWT obrigatório. Não executar `local.py` nem `deploy.py` como função Vercel.
- Serviço `frontend`: raiz `frontend/`, `npm ci`, build com `VITE_API_BASE_URL=/api/v1`, saída `dist`; fallback SPA somente nesse serviço. Rewrites raiz encaminham `/api/*` e `/health*` à API antes do frontend, conservando os caminhos originais.
- Nenhuma migration no import, request ou cold start. Preparar o banco uma vez, pela URL **direta**, antes de publicar. Runtime da API usa a URL **pooled** da mesma base. JWT deve ser aleatório, estável e privado, com pelo menos 32 bytes.
- `.vercelignore` exclui dotenv, credenciais, bancos locais, dependências, testes e artefatos de agentes. `.vercel/` e arquivos privados de provisionamento permanecem ignorados pelo Git. Nenhum segredo em `VITE_*`, Git, argumentos de CLI ou logs.

## Operação e próxima publicação

1. Preservar `.neon` na branch `production`; não criar outra integração/projeto e não imprimir `.env.local`. URLs direta/pooled foram conferidas contra o mesmo banco/usuário/endpoint, TLS ativo e schema inicial vazio.
2. Migrations já PASS em branch temporária `br-late-fog-b6791v9q`, filha de production, e depois em production: head `0008_favorites`, `citext 1.8`, `vector 0.8.6`, identidade/TLS/lock serial/SQL RO aprovados. A branch temporária foi removida por ID/parent/nome revalidados; produção preservada. Não repetir o bootstrap como evidência nova sem mudança de schema.
3. CLI de migrations: `GANDALF_NEON_MIGRATE=owned-project` e `NEON_DATABASE_URL_UNPOOLED` somente childenv; stdout JSON sanitizado. O CLI não lê dotenv nem aceita credenciais em argumentos. Artifact ignorado `neon-production-migration.json` contém head/ext/checks, sem DSN.
4. `DATABASE_URL` pooled e JWT privado configurados como secrets via stdin; flags públicas configuradas separadamente. `CORS_ORIGINS=[]` pois navegador/API compartilham origem. Catálogo online/Open Library habilitado; Groq ausente e `AI_DAILY_LIMIT=0` garantem que a publicação não executa IA paga. Recomendação mantém fallback existente por regras; IA só será habilitada com chave gratuita e orçamento explícitos.
5. Em novas versões, verificar schema e lista final `vercel deploy --dry --json` antes de publicar. Não migrar em requests/cold starts nem repetir bootstrap por rotina. Smoke público desta versão já PASS conforme abaixo; não repeti-lo como prova nova sem mudança/falha específica.
6. GitHub conectado não envia commits locais: **nenhum push realizado**. A publicação atual veio da CLI, com as fontes do commit813436c. Para deploys futuros pelo GitHub usarem essa configuração, solicitar autorização explícita para enviar os commits locais; manter as mesmas variáveis privadas na Vercel.

## Evidências preparatórias

- Backend: 43 testes focados PASS, Ruff/formatação PASS; Settings/TLS/normalização/import sem dotenv e lifecycle com engine fake. [Relatório](backend-vercel-session-2026-10-03.md).
- Frontend: build TypeScript/Vite PASS com API relativa; 49 fontes inalterados, localhost ausente no bundle. Aviso não fatal de chunk acima de 500 kB. [Relatório](frontend-vercel-session-2026-10-03.md).
- CLI dry final PASS: **146 arquivos não vazios/3.226.939 bytes**, privados ausentes; scripts de gates e skills/contexto Neon excluídos, fontes/runtime/assets necessários presentes. Artifact local ignorado `.impeccable/runtime/vercel-upload-verification-final.json`.
- Banco: 60 testes focados offline/Ruff/formatação PASS; preflight Neon real PASS com zero tabelas públicas, URLs pareadas e TLS cliente ativo. Migrations reais trial/production PASS e cleanup trial confirmado. [Relatório](database-neon-session-2026-10-03.md).
- HTTPS real inicial: raiz/login/account HTML200; health/ready JSON200 com database/schema/pgvector ok e system/status online/Groq unconfigured. Sem bypass de autenticação Vercel.
- **Browser público PASS:** sete checks, oito caminhos SPA diretos, JS/CSS/WOFF2/JPEG200 com MIME correto, cinco POSTs exatos (register201/login200/refresh200/logout204/revogado401). Tokens apenas em memória; erros JS/console inesperados/bloqueios externos0. Console401 esperado e logout ERR_ABORTED correlacionado ao mesmo request/status204/token/UI/revogação são registrados explicitamente. A pré-checagem Node sem CA do sistema falhou antes de browser/POST; rodada com TLS validado `--use-system-ca` passou. Conta sintética removida por UUID+email/username reconstruídos e conexão/identidade/TLS verificados.
- **HTTP/SQL público PASS:** seis checks/24 requests, duas contas sintéticas, busca real Open Library, favorito/playlist persistentes e isolados, playlist de duas faixas em ordem, refresh/logout/revogação. SQL independente direto/canônico do mesmo projeto/branch: users2/fav1/playlist1/tracks2/refresh3/**AI0**. Guard compara o URL local ao resolvido pela CLI autenticada, valida endpoint/TLS e revalida identidade/TLS no cleanup. Ambas as contas removidas; caches e catálogo público gerados permanecem e seguem o TTL do aplicativo.
- Primeiro smoke HTTP não passou porque esperava404 no DELETE de favorito de outro owner; o contrato existente retorna204 idempotente/opaco. Sem patch de produto: teste ajustado exige204 e preservação do favorito do dono. Primeiro cleanup confirmado, resultado NOT_PASSED preservado em arquivo separado; somente a rodada final é PASS.
- SQL final somente leitura, após cleanup e com identidade/TLS revalidados: zero registros das três contas finais em users/favorites/playlists/refresh_tokens/user_preferences/interactions/search_history e zero faixas da playlist de teste. AI calls0; não foram removidos dados de usuários reais.
- Esta execução comprova os fluxos acima na revisão publicada. Pooling/rate limiter permanecem por instância; Services beta, disponibilidade contínua, carga/escala, rollout/mistura de versões e IA não foram certificados por esta rodada.

## Artifacts sanitizados locais

Arquivos ficam em `.impeccable/runtime`, ignorados; contêm checks/IDs públicos/contagens, sem credenciais ou PII. O artifact trial não inclui parent/nome para conferência independente; as verificações estão no harness preservado, antes da remoção por ID. Não ampliar essa evidência para uma auditoria independente de toda a conta Neon.

| Arquivo | SHA256 |
| --- | --- |
| `vercel-deployment-result.json` | `4193fa6c88d67c7b699e7c2f9211741c8ac2fa9e9ddd97fbf66a752e637da18a` |
| `neon-production-migration.json` | `98bb0aea5a1823254e88f5afead7fdadc647c49fce30025e796587da5b441d7d` |
| `vercel-upload-verification-final.json` | `df8fc75aee4d681ed0e748e7fea2f832180eff696e769771340beeed52ee56dc` |
| `frontend-vercel-smoke-result.json` | `6b3122dc6e1b0f8772942c87411cfff4ce94175390a58010025410ab9059a371` |
| `frontend-vercel-cleanup.json` | `55154293a25fe25eec79632434a396a3c5cdd59eb11982f59d5b08e35faed9a7` |
| `vercel-public-api-result.json` | `72e7772cc6c5fc599d20592d03676a5ce8ab5980a83d0272acd14e1519017d8b` |
| `vercel-final-cleanup-sql.json` | `2e4db0c6ea0c9fa0c3789d2d85c7979df263b25af692f192afdf0162133c7ebe` |
