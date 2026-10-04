# Frontend — auditoria Vercel Services

## 04/10/2026 — smoke público real PASS

Unidade autorizada somente para o harness ignorado `.impeccable/runtime/frontend-vercel-smoke.mjs` e este documento. **Freeze final:** produto, configuração raiz e `frontend/tests/deployment.mjs` intactos. Nenhum build repetido, Git ou publicação pelo Frontend. Skill webapp-testing aplicada com Playwright Node e Chromium já instalado, sem instalação.

Origem literal permitida: `https://gandalf-gray.vercel.app`. Antes do navegador, o harness exige `GANDALF_VERCEL_SMOKE_ALLOW=public-coordinated-one-account` e `GANDALF_VERCEL_SMOKE_BASE_URL` exatamente igual à origem; verifica readiness JSON200/catalog online/IA não configurada. Browser bloqueia outras origens, APIs fora da lista e qualquer POST além do quinto. Não há mocks de resposta.

Comando executado após definir somente os dois guards temporários: `node --use-system-ca .impeccable/runtime/frontend-vercel-smoke.mjs` (**exit0**, 8,44 s). Pré-checagem inicial com Node padrão falhou em readiness, sem abrir navegador, POSTs ou criar conta; diagnóstico sanitizado não identificou o código específico. O GET com `--use-system-ca` retornou200 antes da rodada real; TLS permaneceu validado, sem certificado copiado ou desativação de verificação. Esse problema da pré-checagem local não foi atribuído à aplicação publicada.

Sete checks PASS:

- API mesma origem respondeu200 em `/api/v1/system/status`; catálogo online e IA não configurada.
- GETs diretos `/`, `/music`, `/books`, `/read-with-music`, `/account`, `/account/favorites`, `/register`, `/login`: HTML200 e aplicação montada; páginas protegidas conduziram ao login. Não foram submetidas buscas.
- JS/CSS, duas fontes locais WOFF2 e três capas JPEG retornaram200 com `application/javascript`, `text/css`, `font/woff2` e `image/jpeg`, respectivamente. O artifact contém os caminhos públicos/MIMEs, sem corpo.
- Uma conta sintética: cadastro201; login200 e conta visível com identidade conferida somente em memória.
- Refresh real200 disparado por “Atualizar dados” após avançar apenas `Date.now()` do cliente em900s; ambos os tokens rotacionaram e o perfil seguinte respondeu200. Clock restaurado; API intacta.
- Logout204 referenciou o refresh atual; UI voltou a `/login`; tentativa real de reutilizar esse refresh respondeu401.
- Exatamente **cinco POSTs auth** no total; zero requests externos bloqueados, zero erros de página ou console inesperados. Local/session storage e cookies sem credenciais nos três checkpoints autenticados/final.

Exceções observadas e comprovadas: Chromium emitiu um erro de recurso401 para a tentativa obrigatória de refresh revogado; somente esse URL/código foi reconhecido como esperado. Um `requestfailed net::ERR_ABORTED` ocorreu no mesmo objeto Request do logout comprovado por204, token vigente, UI login e refresh401; nenhum outro abort foi tolerado. Contadores explícitos no artifact evitam declarar ausência absoluta desses eventos esperados.

Artifact sanitizado: `.impeccable/runtime/frontend-vercel-smoke-result.json`; pré-checagem preservada em `.impeccable/runtime/frontend-vercel-smoke-preflight.json`. Stdout contém somente status/checks e IDs; artifact adicional registra método/caminho/status público, MIME e contadores. Sem tokens, e-mail, senha, headers, texto bruto de console/erro, DOM ou screenshots. Credenciais aleatórias e pares de tokens ficaram apenas em memória; browser encerrado.

Identidade para limpeza pelo Maestro:

- `user_id`: `7952ee31-abf8-44f5-b1d2-3fa56727ac23`
- `fixture_uuid`: `290ccab6-5e03-4e6d-975a-486e67ce5bf4`
- E-mail sintético reconstruído pelo algoritmo no harness, sem impressão. Após a entrega do Frontend, o Maestro confirmou conexão/identidade/TLS e removeu somente essa conta por ID e identidade reconstruída; artifact `frontend-vercel-cleanup.json` PASS. SQL final somente leitura confirmou ausência da conta e dos seus registros dependentes em `vercel-final-cleanup-sql.json`. Nenhuma nova rodada de browser.

Limites: esta prova não certifica descoberta externa/qualidade, Groq, consumo/cota, isolamento entre duas contas, persistência de favoritos/playlists, mobile/temas/acessibilidade visual completa, restart/rollout ou SQL Neon independente. Zero chamadas a recommendations, fontes externas ou LLM nesta unidade. O status não expõe `AI_DAILY_LIMIT` ou migration head; valores0/head0008 permanecem evidência comunicada pelo Maestro, não verificados por este smoke.

## Checkpoint anterior — auditoria e build local

Reserva exclusiva deste documento; execução concluída em 04/10/2026. Produto, configuração raiz, Git e publicação pertencem ao Maestro. Documento e auditoria congelados para consolidação.

## Contrato atual

`frontend/src/lib/api.ts:26` seleciona `VITE_API_BASE_URL` no build e remove a barra final; as requisições concatenam essa base com os caminhos dos endpoints. `/api/v1` é compatível com frontend e API no mesmo domínio. Sem a variável, o código possui fallback `http://localhost:8000/api/v1`, inadequado para o navegador publicado. Configurar `/api/v1` nos ambientes de build usados pelo projeto Vercel; não incluir segredos em variáveis `VITE_*`, expostas ao cliente. [Documentação oficial Vite/Vercel](https://vercel.com/docs/frameworks/frontend/vite).

`frontend/package.json` executa `tsc -b && vite build`; `frontend/vite.config.ts` não personaliza base nem diretório de saída. Nenhum arquivo próprio adicional de produto é necessário nesta etapa.

## Fragmento recomendado ao Maestro

Em `vercel.json` raiz, a configuração do serviço frontend proposta é:

```json
{
  "root": "frontend",
  "framework": "vite",
  "installCommand": "npm ci",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "rewrites": [
    { "source": "/(.*)", "destination": "/index.html" }
  ]
}
```

Esse objeto pertence a `services.frontend`; configuração e entrada do serviço API ficam na reserva Backend/Maestro. Os campos acima são suportados por serviço. A referência consultada não lista `env` como campo do serviço; usar a configuração de variáveis do projeto para a base relativa. [Referência oficial de Services](https://vercel.com/docs/services/config-reference).

Rewrites raiz devem encaminhar `/api/(.*)` para `{ "service": "api" }` antes do catch-all `/(.*)` para `{ "service": "frontend" }`. O serviço recebe o caminho original; não remover `/api/v1`, já esperado pelo cliente/backend. `destination.path` altera a seleção de rota, sem reescrever o caminho observado pelo serviço; não é necessário neste desenho. [Roteamento oficial de Services](https://vercel.com/docs/services/routing).

O fallback SPA fica no serviço frontend. Assim a API tem seu próprio resultado HTTP, e rotas diretas como `/music`, `/books`, `/login` e `/account` podem carregar `index.html`. A recomendação mantém `cleanUrls` no padrão e utiliza rewrites de alto nível, sem `routes` legado. [Fallback SPA oficial](https://vercel.com/docs/frameworks/frontend/vite). Arquivos existentes são resolvidos antes dos rewrites, preservando `/assets/*`, imagens e licenças públicas. [Precedência oficial de arquivos](https://vercel.com/docs/project-configuration/vercel-json).

Services está em beta disponível em todos os planos, incluindo Hobby; isso não certifica custo zero de PostgreSQL, provedores ou IA, nem elimina os limites de execução. [Disponibilidade](https://vercel.com/docs/services), [cobrança de Services](https://vercel.com/docs/services/pricing).

## Execução e evidências

- Maestro confirmou que não havia build/gate frontend ativo.
- Comando lógico: em `frontend`, `VITE_API_BASE_URL=/api/v1 npm run build`. PowerShell definiu a variável apenas durante o comando e restaurou seu estado anterior sem imprimir valores.
- Primeira tentativa normal: bloqueada por `spawn EPERM` no esbuild/Vite antes de carregar a configuração. Não foi aprovação de build.
- Reexecução com `require_escalated`: **PASS, exit 0**; TypeScript e Vite 6.4.3, 2.050 módulos, build Vite 7,23 s. Não houve outro build concluído nem suíte/browser/gate.
- Saída: `dist/index.html` 0,60 kB, CSS 40,48 kB, JS `index-D41yZpWW.js` 504,20 kB (gzip 158,17 kB). Aviso não fatal de chunk acima de 500 kB; nenhuma alteração incidental para suprimi-lo.
- Inspeção estática do JS gerado: `/api/v1` presente e `http://localhost:8000/api/v1` ausente; `dist/index.html` existe. Isso confirma o resultado compilado, não tráfego HTTP hospedado.
- Comparação SHA256 antes/depois de 49 arquivos em `frontend/src`, `frontend/public`, package/lock, Vite/TypeScript e HTML: **zero alterações**. Escritas do build limitadas aos artefatos locais gerados; nenhum produto/configuração editado pelo Frontend.

## Limites e continuação do checkpoint anterior

Não executados publicação, deploy remoto, teste de navegador, HTTPS, roteamento Vercel ou chamadas API/provedores/LLM. Nenhuma leitura de `.env` real, mudança de serviço existente, Git ou push.

Após o Maestro configurar/publicar, validar em origem hospedada: caminhos SPA diretos, assets/fontes com MIME correto, `/api/v1/system/status` retornando JSON e erros API preservados, login/refresh/logout e ownership. Build local não aprova esses comportamentos, disponibilidade pública ou persistência do banco.
