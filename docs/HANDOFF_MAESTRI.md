# Passagem de contexto — 2026-10-01

## Atualização — integração concluída

Este handoff foi atendido na continuação de 01/10/2026. O relato abaixo registra a pausa original e deve ser lido como histórico; **não executar novamente** `.impeccable/integrate-components.py`.

- Radix instalado com `NODE_OPTIONS=--use-system-ca`, mantendo a validação TLS. Accordion, Toggle Group e Skeleton integrados; todos os usos de `Why` substituídos por `Explanation`.
- Preferências têm navegação por teclado, seleção obrigatória, limpeza, aviso de mudança e registro dos filtros usados. Explicações de músicas/livros/trilhas carregam ao abrir, reutilizam o resultado e oferecem retry explícito; requisições são abortadas ao desmontar.
- Testes de integração em `frontend/tests/components.mjs`; smoke e E2E real atualizados. Créditos e licença em `frontend/THIRD_PARTY_NOTICES.md`. Nenhuma nova consulta de código ao 21st nem acesso à chave nesta continuação.
- Backend paralelo preservado e registrado separadamente no commit `f120676`; esta sessão também confirmou 220 testes, Ruff/formatação e comparação estrita v6→v7 em K=5/10 sem perdas.
- Validação frontend e revisão visual descritas na entrada mais recente de `docs/DEVELOPMENT_LOG.md`. Capturas reproduzíveis em `.impeccable/review/components-*`, ignoradas pelo Git. Servidores existentes em 5173/8000 preservados; os testes usam servidores/SQLite temporários isolados.
- Continuar por revisão humana de ranking/modos e gates de provedores/CI, ou persistência e conta na interface conforme o roadmap. A integração descrita neste handoff não é mais uma pendência.

O usuário pediu análise da documentação, continuidade do desenvolvimento, mais componentes do 21st.dev usando a chave existente e execução local. Depois pediu documentação para o Maestri e **interrompeu explicitamente o trabalho** para continuar em outro terminal. Esta passagem registra uma implementação parcial, não uma entrega validada.

## Retomar primeiro

1. Ler este arquivo, `docs/DEVELOPMENT_LOG.md`, `docs/IMPLEMENTATION_STATUS.md`, `PRODUCT.md` e `DESIGN.md`.
2. Conferir `git status --short` e `git diff`. Há alterações sem commit desta sessão; preservá-las. O último commit visto foi `39a7395` (`add alguns arquivos incompletos ainda`). Não desfazer trabalho anterior.
3. Corrigir a instalação de dependências e concluir a integração dos componentes antes de testar ou commitar.

**Alterações adicionais observadas ao encerrar:** a última conferência de `git status` mostrou mudanças em `api/app/providers/local_catalog.py`, `api/tests/test_books.py`, `api/tests/test_evaluation.py`, `api/tests/test_online.py` e `api/tests/test_recommendations.py`, além de novos `docs/catalog-metadata.md` e relatórios `docs/eval-reports/local-v7-piano-detective-k5.json`/`local-v7-piano-detective-k10.json`. Essas mudanças não foram feitas nem revisadas nesta sessão; aparentemente outro trabalho está acontecendo no mesmo checkout. Preservar e inspecionar sua origem antes de integrar ou commitar, sem incluí-las automaticamente no commit de UI.

## O que foi feito

- Documentação e código dos três fluxos públicos inspecionados. O visual ametista/cozy com capas, já aprovado, deve ser preservado.
- Servidores iniciados por `start-local.ps1`: frontend `http://127.0.0.1:5173`, API `http://127.0.0.1:8000`, Swagger `http://127.0.0.1:8000/docs`. Modo local/offline; dados existentes em `api/.local` preservados.
- Chave localizada em `api/.env`, com nome **`API_KEY_21st`** (capitalização exata). Autenticação no endpoint oficial `https://21st.dev/api/mcp` funcionou. Nunca imprimir, copiar para o frontend ou commitar a chave.
- Buscas autenticadas por accordion, toggle group e skeleton realizadas. Baixados via `get_component`: Accordion shadcn, demo 1530; Toggle Group shadcn, demo 252. As duas recuperações gratuitas foram consumidas. Reset informado: `2026-10-02T00:00:00Z`; geração hospedada desabilitada. Não contratar plano nem contornar cota.
- Skeleton consultado na fonte pública: `https://raw.githubusercontent.com/shadcn-ui/ui/main/apps/v4/registry/new-york-v4/ui/skeleton.tsx`; licença MIT, Copyright (c) 2023 shadcn.

## Arquivos e estágio exato

| Arquivo | Estado |
| --- | --- |
| `frontend/src/components/ui/accordion.tsx` | Novo wrapper Radix, um painel expansível, chevron e callback de abertura |
| `frontend/src/components/ui/toggle-group.tsx` | Novo controle Radix de seleção única obrigatória, com marca visual de seleção |
| `frontend/src/components/ui/skeleton.tsx` | Novo Skeleton e placeholders para música, livros e playlist |
| `frontend/src/components/ui/components.css` | Novos estilos com tokens dos dois temas e movimento reduzido; ainda não revisados no navegador |
| `frontend/src/components/Explanation.tsx` | Nova explicação compartilhada com busca ao abrir, retry explícito e abort ao desmontar; não validada |
| `frontend/src/main.tsx` | Já importa o novo CSS |
| `frontend/src/pages/Discovery.tsx` | Integração parcial: imports/opções adicionados e função `Why` removida; **usos de `<Why>` ainda existem e quebram o build** |
| `frontend/src/pages/ReadWithMusic.tsx` | Ainda sem alterações desta etapa |
| `frontend/package.json`, `frontend/package-lock.json` | Instalação falhou; confirmar status antes de retentar |
| `frontend/tests/smoke.mjs`, `frontend/tests/live.mjs` | Ainda usam combobox/select e `.why summary`; precisam acompanhar os novos controles |
| `frontend/THIRD_PARTY_NOTICES.md` | Ainda precisa registrar os três novos componentes e licença shadcn |

Nenhum teste ou build foi executado nesta etapa. Nenhum commit foi feito: a implementação parcial não deve ser commitada como funcional.

## Material temporário útil

Tudo abaixo está em `.impeccable/`, ignorada pelo Git. Os arquivos existem neste checkout, mas não estarão disponíveis por clone.

- `21st-client.py`: cliente temporário que lê a chave de `api/.env` e consulta o MCP. Não armazena a chave no código.
- `21st-accordion-code.json`, `21st-toggle-code.json`: respostas autenticadas com código e cotas.
- `21st-accordion.json`, `21st-toggle.json`, `21st-skeleton.json`: resultados de busca com autores/URLs.
- `integrate-components.py`: script **preparado, ainda não executado**. Revisar antes de executar. Integra filtros, troca `<Why>` por `<Explanation>`, captura preferências usadas na busca, adiciona Skeletons e explicações em faixas de leitura. Executar no máximo uma vez; não é idempotente.
- `review/before-music.png`: captura desktop da tela de música anterior à integração. Outros screenshots podem ser de sessões antigas; não tratá-los como validação destas mudanças.

## Instalação e integração

A tentativa de `npm install @radix-ui/react-accordion @radix-ui/react-toggle-group` falhou com `UNABLE_TO_VERIFY_LEAF_SIGNATURE`. Node instalado: v24.16.0, com suporte a `--use-system-ca`. Próxima tentativa sugerida, em PowerShell, preservando a configuração anterior:

```powershell
cd C:\Users\vinic\Documents\Gandalf\frontend
$previousNodeOptions = $env:NODE_OPTIONS
try {
    $env:NODE_OPTIONS = "$previousNodeOptions --use-system-ca".Trim()
    npm.cmd install @radix-ui/react-accordion @radix-ui/react-toggle-group
} finally {
    $env:NODE_OPTIONS = $previousNodeOptions
}
```

Não usar `strict-ssl=false` nem `NODE_TLS_REJECT_UNAUTHORIZED=0`. Se persistir a falha, diagnosticar a cadeia de certificados/proxy. O sandbox Windows desta sessão recusou até comandos de leitura com erro de split writable roots; execuções exigiram `require_escalated`. Respeitar o mecanismo de aprovação do próximo ambiente.

Após revisar o script, executar a partir da raiz:

```powershell
.\api\.venv\Scripts\python.exe .impeccable/integrate-components.py
```

Ou implementar manualmente a mesma integração. A intenção é:

- Preferências musicais visíveis como escolhas, botão de limpar e aviso para buscar novamente após mudar filtros.
- Resultados mostram **os filtros submetidos**, não os ajustes posteriores do formulário.
- Accordion reutilizável nas preferências e explicações, com teclado e expansão suave.
- Explicações também nas faixas de leitura, obtidas pelo endpoint já existente; retry quando houver falha.
- Skeletons decorativos nos três fluxos durante requisições, mantendo mensagem/cancelamento reais e reduzindo movimento quando solicitado.

## Validação e fechamento

1. Ajustar seletores dos testes aos papéis reais produzidos pelo Radix; confirmar no navegador. Preservar contratos HTTP de filtros (`none`, `required`, `low`, `medium`, `high`; omitir quando indiferente).
2. Verificar filtros por teclado, limpar, snapshot de filtros usados, explicações lazy/cache/retry, cancelamento e troca de livro, sem resposta antiga sobrescrever busca nova.
3. Testar com API real, modo offline, desktop/mobile 390 e 320, claro/escuro e movimento reduzido. Inspecionar screenshots atuais e console. Testes existentes usam Playwright instalado no frontend.
4. Atualizar `frontend/THIRD_PARTY_NOTICES.md` com URLs do catálogo e licença MIT shadcn; atualizar `docs/IMPLEMENTATION_STATUS.md` somente para o que funcionar.
5. Rodar os checks a partir das respectivas pastas:

```powershell
cd frontend
npm.cmd test
npm.cmd run build
cd ../api
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check app local.py alembic tests
.\.venv\Scripts\python.exe -m ruff format --check app local.py alembic tests
```

6. Atualizar o log no topo com o resultado final, revisar `git diff`, adicionar apenas arquivos intencionais e fazer commit local explicativo conforme as instruções do usuário. **Não fazer push.**

## Servidores

Verificar `/health/ready` e a porta 5173 antes de iniciar outra instância. Não encerrar processos desconhecidos. Se necessário, da raiz:

```powershell
.\start-local.ps1
```

A última verificação confirmou `/health/ready` com status `ok` e HTTP 200 do frontend. Isso confirma processos em execução, **não** a validade da interface parcial. A sessão de execução anterior pode encerrar ao trocar de terminal. O iniciador detecta conflitos de porta. Sem `-Online`, permanece no catálogo local sem chamadas externas em runtime; a consulta ao 21st é apenas ferramenta de desenvolvimento.

## Continuidade depois desta unidade

O estado documentado no início era ranking `local-rules-v6` e catálogo de 18 livros/25 músicas. A etapa anterior registrou 192 testes; nesta sessão esse número não foi revalidado. Esta sessão não alterou ranking, corpus ou metadados, mas a última conferência encontrou mudanças adicionais de backend e relatórios v7 descritos acima, que precisam ser reconciliados antes de afirmar o estado atual. Após concluir esta unidade de UI, consultar os diagnósticos de piano/detetive no log e comparar os experimentos disponíveis por caso em K=5/10, sem sobrescrever trabalho paralelo. Login, persistência de playlists, histórico e personalização continuam pendentes; os gates externos seguem abertos.
