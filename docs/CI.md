# Integração contínua

Workflow: [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). Configurado em 2026-10-01 para pull requests destinados a `main`, pushes em `main` e execução manual pelo GitHub Actions. Esta implementação não faz deploy nem altera proteção de branch.

## Checks implementados

| Job | Ambiente | Verificações |
| --- | --- | --- |
| `API e ranking local` | Ubuntu 24.04, Python 3.12 | Instalação da API com ferramentas de desenvolvimento, Ruff/lint e formatação, pytest com SQLite/provedores simulados, comparação estrita K=5/10 contra v7 |
| `Build e fluxos públicos` | Ubuntu 24.04, Node 24, Python 3.12, Chromium | `npm ci`, instalação do Chromium/bibliotecas, TypeScript/build e `npm test` conforme o script versionado do frontend |

Os testes de navegador usam respostas simuladas e uma API real iniciada pelo E2E com SQLite temporário. `GANDALF_PYTHON=python` aponta para o Python preparado pela Action; não depende de uma `.venv` previamente criada no runner. `GANDALF_ONLINE=0` mantém essa API no modo local. `frontend/tests/live.mjs` é um E2E com API local, apesar do nome; não é uma avaliação real de Open Library, MusicBrainz ou Groq.

A instalação requer rede para dependências, Actions e navegador. Os testes usam catálogo local e HTTP simulado, sem chaves de provedores, conta de IA ou dados de produção. Nenhum segredo de `.env` é usado pela configuração da CI.

Os jobs falham se algum check falhar, sem retry que esconda perdas. A comparação usa `--fail-on-case-regression`: perdas individuais também bloqueiam, mesmo que as médias não caiam. Baselines atuais: `docs/eval-reports/local-v7-piano-detective-k5.json` e `local-v7-piano-detective-k10.json`. Atualizá-los exige uma etapa de ranking validada e documentada; não regenerá-los automaticamente na CI.

## Resultados e diagnóstico

- `api-results`: relatório JUnit do pytest e relatórios JSON K=5/10, quando gerados.
- `frontend-screenshots`: somente PNGs de `.impeccable/review/`, quando gerados pelos testes.
- Os artefatos são coletados mesmo após falha e retidos por sete dias. Se uma etapa anterior impedir sua geração, o upload avisa; o check que falhou permanece vermelho.
- Logs das etapas ficam no run do GitHub Actions. Não há upload de `.env`, banco, segredo JWT ou da pasta `.impeccable/` inteira.
- Uma execução nova do mesmo workflow/ref cancela a anterior. Limites: dez minutos para API e quinze para build/E2E.

## Dependências do workflow

Actions fixadas por SHA completo, com versão em comentário. Os hashes foram conferidos pela API oficial do GitHub contra estes releases:

| Action | Release |
| --- | --- |
| `actions/checkout` | [v7.0.1](https://github.com/actions/checkout/releases/tag/v7.0.1) |
| `actions/setup-python` | [v7.0.0](https://github.com/actions/setup-python/releases/tag/v7.0.0) |
| `actions/setup-node` | [v7.0.0](https://github.com/actions/setup-node/releases/tag/v7.0.0) |
| `actions/upload-artifact` | [v7.0.1](https://github.com/actions/upload-artifact/releases/tag/v7.0.1) |

`contents: read` é a permissão do token; checkout não mantém credenciais para os comandos posteriores. Referência para revisar essas escolhas: [segurança de Actions](https://docs.github.com/en/actions/reference/security/secure-use). A instalação do navegador segue a [documentação de CI do Playwright](https://playwright.dev/docs/ci).

Node instala pelo `frontend/package-lock.json`. Python instala as faixas de versões do `api/pyproject.toml`; ainda não há lock de dependências Python. Os caches são de pip/npm, invalidados pelos respectivos arquivos; não reutilizam `.venv`, banco ou `node_modules`.

## Validação realizada e próximos passos

O YAML passou no [actionlint v1.7.12](https://github.com/rhysd/actionlint/releases/tag/v1.7.12), baixado da fonte oficial com SHA-256 conferido. No Windows, os comandos de Ruff/formatação passaram, 220 testes da API geraram JUnit e os gates K=5/10 contra v7 passaram sem perdas ou mudança de catálogo. `npm run build` e `npm test` (smoke, componentes e E2E com API real) passaram no checkout após a integração de UI `beb7569`, usando as variáveis da CI.

O teste de carregamento responsivo agora espera o layout se ajustar após mudar viewport/tema antes de verificar overflow. A espera é limitada pelo timeout do Playwright e continua falhando se houver overflow persistente. Essa correção de uma linha foi autorizada pelo usuário; componentes, estilos e animações não foram alterados nesta etapa. Novas alterações de autenticação do outro terminal permanecem fora deste commit e precisam de validação própria.

**Ainda não há execução validada no runner hospedado.** O workflow está preparado para um futuro push autorizado; não foi enviado automaticamente. Depois desse envio, verificar os dois jobs e os artefatos. Ubuntu, instalação limpa de dependências e bibliotecas do Chromium precisam dessa confirmação remota.

O gate G6 permanece aberto: CI hospedada verde, auditoria final e deploy público não estão concluídos. PostgreSQL/pgvector, concorrência entre processos, mypy e avaliações online reais também ficam fora deste workflow inicial. O exemplo mais amplo de `docs/11-deployment-guide.md` continua um desenho futuro.
