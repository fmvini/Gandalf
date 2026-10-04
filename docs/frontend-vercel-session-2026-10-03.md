# Frontend — auditoria Vercel Services

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

## Limites e continuação

Não executados publicação, deploy remoto, teste de navegador, HTTPS, roteamento Vercel ou chamadas API/provedores/LLM. Nenhuma leitura de `.env` real, mudança de serviço existente, Git ou push.

Após o Maestro configurar/publicar, validar em origem hospedada: caminhos SPA diretos, assets/fontes com MIME correto, `/api/v1/system/status` retornando JSON e erros API preservados, login/refresh/logout e ownership. Build local não aprova esses comportamentos, disponibilidade pública ou persistência do banco.
