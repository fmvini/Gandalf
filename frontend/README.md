# Frontend do Gandalf

Primeira implementação dos fluxos públicos definidos em [UX/UI Specification](../docs/08-ux-ui-specification.md) e [API Specification](../docs/05-API-Specification.md).

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
- Teste de fumaça com respostas simuladas da API.

A [API inicial](../api/README.md) já oferece a busca de títulos usada no seletor de livros. Os endpoints de recomendações e trilhas, assim como login, histórico, salvos e feedback persistido, ainda não foram implementados. Essas ações mostram um estado de erro até a próxima integração, sem recomendações inventadas.

## Verificar

```bash
npm run build
npm test
```

O teste usa Playwright e gera capturas em `../.impeccable/review/`. Na primeira execução pode ser necessário instalar o navegador do Playwright com `npx playwright install chromium`.
