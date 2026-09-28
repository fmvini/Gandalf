# Contribuindo

Este projeto ainda está na fase de especificação. O repositório contém o escopo, o README e os documentos técnicos; os diretórios de código e comandos de desenvolvimento descritos abaixo são **planejados** e só se aplicam quando existirem. Comece pelo [escopo detalhado](docs/00-Escopo-Detalhado.md), pelo [roadmap](docs/12-development-roadmap.md) e pelo [índice de ADRs](docs/adr/README.md).

## Antes de começar

1. Verifique se há uma tarefa correspondente no roadmap ou descreva claramente o problema, a proposta e o critério de aceitação.
2. Para mudanças de comportamento ou arquitetura, identifique os requisitos afetados no [PRD](docs/01-PRD.md) e na [SRS](docs/02-SRS.md). Uma decisão com alternativas e consequências duradouras deve ganhar ou atualizar um ADR.
3. Faça uma mudança pequena e coerente por vez. Não acrescente funcionalidades pós-MVP ao fluxo principal sem registrar a motivação e o impacto no roadmap.

## Preparando o ambiente (quando o código estiver disponível)

Use o [guia de deploy](docs/11-deployment-guide.md) para pré-requisitos, variáveis de ambiente e Docker Compose. Copie os exemplos de `.env` quando forem criados e mantenha segredos fora do Git. Os comandos previstos são:

```bash
docker compose up --build
docker compose exec backend alembic upgrade head
docker compose exec backend pytest -m "unit or integration"
```

Para trabalhar sem o Compose completo, siga a seção de execução local do [README](README.md). Confirme os scripts reais em `backend/pyproject.toml` e `frontend/package.json` antes de executá-los: esses arquivos ainda não existem nesta fase.

## Fluxo de contribuição

1. Crie uma branch a partir de `main`, com nome que descreva a tarefa (por exemplo, `feat/music-discovery` ou `fix/refresh-token`).
2. Altere o código e a documentação relacionados. Mantenha migrations Alembic junto da mudança de modelo e atualize contratos de API, exemplos e ADRs quando a decisão mudar.
3. Execute as verificações aplicáveis descritas abaixo. Na fase atual, valide links, nomenclatura e coerência entre os documentos alterados.
4. Revise o diff e abra um pull request com objetivo, solução, referências de requisitos, testes executados e riscos ou pendências. Inclua capturas de tela se a interface mudar.
5. Aguarde a revisão antes de integrar em `main`; resolva comentários no mesmo PR. Não inclua segredos, dados pessoais, artefatos gerados nem respostas reais de provedores sem verificar licença e privacidade.

### Commits

Use commits por unidade lógica com tipo `feat`, `fix`, `refactor`, `docs`, `test` ou `chore`, seguido de resumo curto e corpo que explique mudança e motivo. Revise `git diff`, rode as verificações disponíveis e adicione somente os arquivos pertinentes. Não faça push automaticamente: o envio ao remoto é uma ação separada.

## Padrões de implementação

- **Camadas:** `api` valida e serializa; `services` orquestra; `recommendation` contém regras de domínio sem HTTP ou SQL; `providers`, `ai` e `repositories` encapsulam integrações. Veja [Arquitetura do Sistema](docs/03-System-Architecture.md).
- **Contratos:** use tipos e schemas explícitos (Pydantic no backend e TypeScript no frontend). Não coloque regras de ranking em rotas, componentes React ou no prompt do LLM.
- **Conteúdo real:** resultados devem vir de providers ou do catálogo local. O LLM interpreta a intenção e explica fatores calculados; não fabrica itens recomendados.
- **Dados e segurança:** valide entradas e saídas externas, proteja recursos por `user_id`, não registre tokens, prompts sensíveis ou dados pessoais, e respeite limites e termos das APIs. Veja [Security Specification](docs/09-security-specification.md).
- **Mudanças de esquema:** use migrações Alembic revisáveis e teste `upgrade` e `downgrade` quando houver banco. Para alteração de embeddings, documente a dimensão, a migração, o reprocessamento e a reindexação.

### Adicionando um provider

1. Implemente o contrato `MusicProvider` ou `BookProvider` descrito na [arquitetura](docs/03-System-Architecture.md), sem expor o formato bruto da API ao restante do sistema.
2. Normalize IDs, metadados e URLs; descarte dados inválidos e preserve a origem do item. Considere deduplicação entre fontes.
3. Trate timeout, rate limit, retry, cache e fallback conforme os guias de [arquitetura](docs/03-System-Architecture.md) e [segurança](docs/09-security-specification.md).
4. Crie testes de contrato com fixtures sem credenciais e documente limites, atribuição e termos de uso. Para a escolha do provedor musical, registre a avaliação no [ADR-0012](docs/adr/0012-music-provider-selection.md).

## Verificações (quando as ferramentas existirem)

| Área | Comandos previstos | Critério |
|---|---|---|
| Backend | `ruff check .`, `ruff format --check .`, `mypy app`, `pytest -m "unit or integration"` em `backend/` | Lint, tipos e testes passam |
| Frontend | `npm run lint`, `npm test -- --run`, `npm run build` em `frontend/` | Lint, testes e build passam |
| E2E | Playwright conforme configuração futura | Fluxos afetados passam |
| IA e APIs reais | `pytest -m "ai_eval or live"`, sob demanda | Resultados e custos revisados; fora da CI padrão |

Testes da suíte padrão devem usar fakes para LLM, embeddings e APIs externas, mantendo execução sem rede e sem custo. Mudanças no ranking precisam de testes de casos relevantes e, quando afetarem qualidade, comparação com o *golden set*. Consulte a [Testing Strategy](docs/10-testing-strategy.md).

## Documentação e ADRs

Atualize o documento dono do assunto, em vez de copiar requisitos divergentes para vários lugares. Mantenha links relativos funcionais e marque claramente o que é proposta, decisão aceita ou questão em aberto. Para registrar uma decisão arquitetural, siga o [formato e processo de ADR](docs/adr/README.md); nunca apresente a escolha de fornecedor, modelo ou parâmetro pendente como validada.

## Reportando vulnerabilidades

Não abra uma issue pública com detalhes de exploração, credenciais ou dados pessoais. Contate o mantenedor por um canal privado indicado no perfil do repositório; se ainda não houver canal publicado, solicite um contato privado sem divulgar os detalhes técnicos. Inclua impacto, reprodução mínima e versão afetada. O mantenedor deve confirmar o recebimento e coordenar correção e divulgação conforme a [especificação de segurança](docs/09-security-specification.md).
