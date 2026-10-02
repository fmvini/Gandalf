# Frontend do Gandalf

Interface dos fluxos públicos e de autenticação definidos em [UX/UI Specification](../docs/08-ux-ui-specification.md) e [API Specification](../docs/05-API-Specification.md).

## Executar

```bash
cd frontend
npm ci
cp .env.example .env
npm run dev
```

No Windows PowerShell, use `Copy-Item .env.example .env`. A API deve estar disponível em `VITE_API_BASE_URL` (padrão: `http://localhost:8000/api/v1`), incluindo o prefixo de versão previsto na especificação.

## O que já existe

- Home com busca em linguagem natural e escolha explícita de música, livros ou trilha de leitura.
- Descoberta de música e livros ligada aos endpoints de recomendação, com estados de carregamento, vazio e erro.
- Busca de livro no catálogo e criação de trilha de leitura.
- Tema escuro padrão, alternância para claro, layout responsivo e navegação por teclado.
- Accordion em preferências/explicações, Toggle Group de vocais/energia e Skeleton nos carregamentos. Fontes e adaptações em [THIRD_PARTY_NOTICES](THIRD_PARTY_NOTICES.md).
- Cadastro em `/register`, login em `/login` e dados da conta/logout em `/account`, com erros, retry e renovação de sessão.
- Salvar a trilha completa na conta, nomear a playlist e consultar a lista paginada em `/account`; detalhe/links externos e exclusão com confirmação em `/account/playlists/:id`.
- Login/cadastro a partir de uma trilha retorna à seleção gerada. Erros de origem expirada pedem uma nova trilha; falhas de conexão e serviço permitem tentar novamente. Requisições privadas são canceladas ao sair ou trocar de conta.
- Favoritos individuais nas sugestões de música/livros e faixas de leitura. Estado salvo consultado em lote; inclusão por origem válida e remoção pelo ID do favorito. O login/cadastro preserva resultado, pedido e controles, sem salvar automaticamente.
- Ver outras músicas/livros usa o pedido e preferências enviados, conservando a seleção durante espera, erro, cancelamento ou fim da amostra disponível. IDs vistos são excluídos cumulativamente até 200, sem histórico pessoal. Um novo pedido reinicia a seleção; retorno do login conserva vistos, página e estado de renovação.
- Coleção em `/account/favorites`, acessível pela conta, com filtros Todos/Músicas/Livros, paginação, links de origem, remoção e retry. Os snapshots salvos permanecem após expiração da recomendação.
- Testes de fumaça, componentes, autenticação, playlists e favoritos com API simulada; E2E com API real, SQLite temporário e duas contas.

A [API](../api/README.md) oferece recomendações, busca de títulos, trilhas, explicações, autenticação, playlists e favoritos persistentes. Histórico, edição/exportação de playlists, feedback e personalização ainda são pendências. Os três fluxos públicos continuam disponíveis sem conta. Favoritos não alteram o ranking nem enviam feedback.

Conforme [ADR-0006](../docs/adr/0006-jwt-authentication-strategy.md), os tokens de acesso/refresh permanecem somente em memória, sem cookies ou armazenamento no navegador. Navegar entre rotas preserva a sessão; recarregar/fechar a página exige novo login. Refresh é rotativo, compartilhado por requisições concorrentes; logout aguarda a renovação e revoga o token atual. Uma falha de conexão ao sair mantém a sessão disponível para tentar novamente.

## Verificar

```bash
npm run build
npm test
```

`npm test` mantém os sete módulos anteriores e acrescenta `tests/discovery-state.mjs` (contratos/limite/deduplicação, sem navegador) e `tests/reroll.mjs` (UI de músicas com API simulada). Os testes Playwright geram capturas em `../.impeccable/review/` em 1440/390/320 px nos dois temas. Favoritos e reroll aguardam fontes, animações finitas e frames de pintura antes das capturas. `tests/favorites.mjs` cobre contratos, erros, retorno da autenticação, filtros/paginação, refresh e cancelamento; `tests/reroll.mjs` acrescenta snapshots enviados, degradação/retry, cancelamento seguido de nova busca e limite 199+1. `tests/live.mjs` exercita API real/SQLite temporário, persistência e isolamento de favoritos entre contas. As instâncias e dados locais existentes são preservados. Na primeira execução pode ser necessário instalar o navegador do Playwright com `npx playwright install chromium`.

Validação em 02/10/2026: helper, smoke, componentes, autenticação, continuation, playlists, favoritos, reroll e live aprovados em rodadas coordenadas. Após corrigir foco de teclado no teste e overflow de Favoritos a 320 px, o Maestro reexecutou continuation/favoritos/live; build final aprovado. Capturas atuais revisadas nos dois temas e tamanhos 1440/390/320 px. E2E usa API real com SQLite temporário; não comprova disponibilidade dos provedores externos. Registro histórico por unidade em `docs/frontend-session-2026-10-02.md`; estado atual em `docs/DEVELOPMENT_LOG.md` na raiz do projeto.
