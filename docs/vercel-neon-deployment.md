# Publicação gratuita: Vercel e Neon

## Estado em 2026-10-04

Projeto `fmvini-projects/gandalf` criado e vinculado pela CLI oficial 62.2.0; usuário conectou o GitHub `fmvini/Gandalf`. A equipe foi verificada no plano **Hobby**, com raiz de build do repositório, sem override de frontend. Deployment público ainda pendente nesta preparação.

Usuário forneceu o projeto Neon `round-rice-47636561`, branch `production` (`br-dark-poetry-b6lwlbso`), em `aws-sa-east-1`; organização verificada no plano **Free**, PostgreSQL 18.6. Não foi criado outro projeto ou recurso marketplace. O pedido anterior de aceite de termos da integração Vercel foi substituído pelo vínculo manual solicitado.

Arquitetura preparada: frontend Vite estático e API FastAPI no mesmo projeto/domínio, via [Vercel Services](https://vercel.com/docs/services), disponível em todos os planos e ainda em beta. PostgreSQL Neon **Free**, com `citext` e `vector`, conserva SQLAlchemy, migrations e autenticação existentes. Não contratar upgrade, adicionar cobrança automática ou ativar trial pago. Os planos gratuitos têm limites de uso; não representam disponibilidade ou capacidade ilimitadas.

`vercel.json` usa região `gru1` para API próxima do banco em São Paulo. O frontend é distribuído pela CDN. Não foram alterados os outros projetos Vercel da conta.

CLI Neon 8.0.5 instalada conforme pedido; login concluído, skills locais e MCP configurados pela CLI. `neon link` vinculou projeto/branch e salvou somente variáveis Neon em `.env.local`, ignorado. `neon config init` criou manifest/lock; `neon.ts` foi substituído pelo conteúdo exato solicitado `defineConfig({})`. `neon config plan` e `neon deploy` PASS sem mudanças remotas, apenas Postgres. MCP `-y` instalou a chave no escopo de conta nos clientes detectados; nenhum valor da chave entrou no Git/artifacts/upload.

## Contrato de execução

- Serviço `api`: raiz `api/`, FastAPI, `vercel_app:app`; Python 3.12, igual ao ambiente dos testes e Docker. Settings exclusivamente do ambiente, PostgreSQL Neon/TLS e JWT obrigatório. Não executar `local.py` nem `deploy.py` como função Vercel.
- Serviço `frontend`: raiz `frontend/`, `npm ci`, build com `VITE_API_BASE_URL=/api/v1`, saída `dist`; fallback SPA somente nesse serviço. Rewrites raiz encaminham `/api/*` e `/health*` à API antes do frontend, conservando os caminhos originais.
- Nenhuma migration no import, request ou cold start. Preparar o banco uma vez, pela URL **direta**, antes de publicar. Runtime da API usa a URL **pooled** da mesma base. JWT deve ser aleatório, estável e privado, com pelo menos 32 bytes.
- `.vercelignore` exclui dotenv, credenciais, bancos locais, dependências, testes e artefatos de agentes. `.vercel/` e arquivos privados de provisionamento permanecem ignorados pelo Git. Nenhum segredo em `VITE_*`, Git, argumentos de CLI ou logs.

## Retomada do provisionamento

1. Preservar `.neon` na branch `production`; não criar outra integração/projeto e não imprimir `.env.local`. URLs direta/pooled foram conferidas contra o mesmo banco/usuário/endpoint, TLS ativo e schema inicial vazio.
2. Migrations já PASS em branch temporária `br-late-fog-b6791v9q`, filha de production, e depois em production: head `0008_favorites`, `citext 1.8`, `vector 0.8.6`, identidade/TLS/lock serial/SQL RO aprovados. A branch temporária foi removida por ID/parent/nome revalidados; produção preservada. Não repetir o bootstrap como evidência nova sem mudança de schema.
3. CLI de migrations: `GANDALF_NEON_MIGRATE=owned-project` e `NEON_DATABASE_URL_UNPOOLED` somente childenv; stdout JSON sanitizado. O CLI não lê dotenv nem aceita credenciais em argumentos. Artifact ignorado `neon-production-migration.json` contém head/ext/checks, sem DSN.
4. Configurar `DATABASE_URL` pooled e JWT privado via stdin; `CORS_ORIGINS=[]` pois navegador/API compartilham origem. Catálogo online/Open Library habilitado; Groq ausente e `AI_DAILY_LIMIT=0` garantem que a publicação não executa IA paga. Recomendação mantém fallback existente por regras; IA só será habilitada com chave gratuita e orçamento explícitos.
5. Reexecutar `vercel deploy --dry --json` e verificar a lista de arquivos antes do upload final. Publicar pela CLI, sem `git push`. Validar HTTPS, assets/MIME, rotas SPA diretas, readiness e erros JSON da API; autenticação/refresh/logout, favoritos/playlists e ownership contra o Neon real. Não declarar sucesso pela página inicial ou health isoladamente.
6. Registrar URL real, revisão, resultados e limitações em DEVELOPMENT_LOG/CONTINUATION. Commit local das evidências sanitizadas; nunca copiar tokens, senhas, e-mails ou DSNs para docs/artifacts. GitHub conectado não envia os commits locais: a regra do usuário continua proibindo push automático.

## Evidências preparatórias

- Backend: 43 testes focados PASS, Ruff/formatação PASS; Settings/TLS/normalização/import sem dotenv e lifecycle com engine fake. [Relatório](backend-vercel-session-2026-10-03.md).
- Frontend: build TypeScript/Vite PASS com API relativa; 49 fontes inalterados, localhost ausente no bundle. Aviso não fatal de chunk acima de 500 kB. [Relatório](frontend-vercel-session-2026-10-03.md).
- CLI dry inicial PASS: 151 arquivos não vazios, sem arquivos privados. Scripts de gates foram posteriormente excluídos e Python fixado; repetir a lista final antes de upload. Artifact local ignorado `.impeccable/runtime/vercel-upload-verification.json`.
- Banco: 60 testes focados offline/Ruff/formatação PASS; preflight Neon real PASS com zero tabelas públicas, URLs pareadas e TLS cliente ativo. Migrations reais trial/production PASS e cleanup trial confirmado. [Relatório](database-neon-session-2026-10-03.md).
- Nenhum teste HTTPS/Vercel publicado concluído nesta preparação. Pooling e rate limiter permanecem por instância; Services beta, limites Free e disponibilidade precisam acompanhamento próprio. Gates locais anteriores não certificam hospedagem pública.
