# Piano e detetive no catálogo local

Data: 2026-10-01. Etapa iniciada no commit `39a7395` e validada nesta continuação. Ranking `local-rules-v7`, comparado com `local-rules-v6`.

## Mudança e evidência

O parser reconhece piano e detetive separadamente; detetive deixa de ser somente alias de mistério e integra o desempate por gênero explicitamente pedido nos livros. Sete músicas existentes recebem `piano` e O Cão dos Baskervilles recebe `detetive`. As [fontes por obra](../catalog-metadata.md) sustentam essas etiquetas e registram seus limites. IDs e número de itens permanecem iguais; o hash do catálogo muda pelos metadados.

Não há regra por título, ID ou consulta do corpus. A correspondência total de temas ainda precede os desempates. Piano é tema de uma obra/edição com piano, não promessa de piano solo ou validação da gravação vinculada. Saman permanece sem etiqueta. Exclusões trabalham com dados conhecidos; a cobertura não é completa.

O fallback online sem IA traduz os termos para piano e detective fiction e reconhece etiquetas dos candidatos. Testes usam HTTP simulado e não validam disponibilidade/cobertura real dos provedores. Nenhuma mudança na interface aprovada.

## Comparação estrita v6 → v7

Corpus `local-editorial-v1`: 45 consultas, mesmo SHA-256 `2cbf9336f5699154cb905a8deebcd2321d7746fe08c0acf0ca557318b5010317`, sem mudar julgamentos. Gate estrito retorna 0 em K=5/10; zero regressões agregadas ou por consulta. Apenas b03 e m06 alteram listas/métricas; consultas de leitura preservadas.

| Caso / métrica | v6 | v7 |
| --- | ---: | ---: |
| b03 — Mistério de detetive, nDCG@5 e @10 | 0,526114 | 1,000000 |
| m06 — Piano acolhedor, Precision@5 | 0,800000 | 1,000000 |
| m06 — Piano acolhedor, nDCG@5 | 0,868795 | 1,000000 |
| m06 — Piano acolhedor, Precision@10 | 0,500000 | 0,600000 |
| m06 — Piano acolhedor, nDCG@10 | 0,940890 | 0,994369 |
| m06 — Piano acolhedor, preenchimento@10 | 0,700000 | 0,900000 |

O Cão dos Baskervilles sobe do quarto para o primeiro lugar. Em m06, Gymnopédie No. 1 entra no top-5 no lugar de Concerning Hobbits; em K=10 entram também River Flows in You e Spiegel im Spiegel. Correspondências parciais continuam possíveis depois dos melhores resultados. O teto de Precision@5 em b03 continua 0,4, pois há só dois livros julgados relevantes.

Relatórios completos: `local-v7-piano-detective-k5.json` e `local-v7-piano-detective-k10.json`, com listas antes/depois e deltas. Não apagar baselines anteriores nem as regressões históricas de v5. Estes resultados usam julgamentos editoriais do assistente, motivados por falhas vistas no corpus; não substituem revisão humana ou conjunto reservado.

## Reprodução

Em `api/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --tb=short
.\.venv\Scripts\python.exe -m ruff check app local.py alembic tests
.\.venv\Scripts\python.exe -m ruff format --check app local.py alembic tests
.\.venv\Scripts\python.exe -m app.evaluation.runner --k 5 --baseline ../docs/eval-reports/local-v6-genres-k5.json --fail-on-case-regression
.\.venv\Scripts\python.exe -m app.evaluation.runner --k 10 --baseline ../docs/eval-reports/local-v6-genres-k10.json --fail-on-case-regression
```

220 testes da API aprovados. Os 28 casos acrescentados cobrem interpretação/negação, descoberta, exclusões, referências, explicação, leitura e fallback online com IA indisponível ou sem chave. `test_evaluation.py` protege métricas agregadas e por caso contra v7 em K=5/10. Persiste aviso de depreciação Starlette/httpx. Testes exigiram acesso aos temporários do Windows fora do sandbox; isso não alterou o código da API.

Build e testes smoke/E2E da interface aprovada passaram em uma cópia isolada extraída de `3732389`, usando as dependências já instaladas e o backend atual via SQLite temporário. Capturas desktop/mobile/temas foram geradas nessa cópia. Isso verifica compatibilidade com os três fluxos aprovados, sem validar os novos componentes pausados de outro terminal. O sandbox inicialmente bloqueou subprocessos do esbuild; a execução com permissão adequada passou sem alterar dependências.

Próxima etapa do ranking: revisão humana de b03/m06 e dos cinco modos de leitura, usando os relatórios completos; montar conjunto reservado antes de novo ajuste. Ampliar instrumentação somente com evidência específica da obra/edição. Integrações reais e PostgreSQL/pgvector continuam pendentes.
