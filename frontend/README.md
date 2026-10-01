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
- Testes de fumaça, componentes, autenticação e playlists com API simulada; E2E com API real, SQLite temporário e duas contas.

A [API](../api/README.md) oferece recomendações, busca de títulos, trilhas, explicações, autenticação e playlists persistentes. Favoritos individuais, histórico, edição/exportação de playlists, feedback e personalização ainda são pendências. Os três fluxos públicos continuam disponíveis sem conta.

Conforme [ADR-0006](../docs/adr/0006-jwt-authentication-strategy.md), os tokens de acesso/refresh permanecem somente em memória, sem cookies ou armazenamento no navegador. Navegar entre rotas preserva a sessão; recarregar/fechar a página exige novo login. Refresh é rotativo, compartilhado por requisições concorrentes; logout aguarda a renovação e revoga o token atual. Uma falha de conexão ao sair mantém a sessão disponível para tentar novamente.

## Verificar

```bash
npm run build
npm test
```

Os testes usam Playwright e geram capturas em `../.impeccable/review/`, incluindo conta/cadastro/login e salvamento/lista/detalhe/exclusão de playlists em 1440/390/320 px nos dois temas. O E2E inicia servidores temporários e usa banco isolado; preserva as instâncias e dados locais existentes. Na primeira execução pode ser necessário instalar o navegador do Playwright com `npx playwright install chromium`.
