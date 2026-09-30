# Diagnóstico e desempate por gênero explícito

Data: 2026-09-30. Ranking `local-rules-v6`; dataset, catálogo e julgamentos preservados.

## Diagnóstico antes do experimento

| Consulta | Evidência em v5 | Causa e limite |
| --- | --- | --- |
| b03 — Mistério de detetive | Só `mistério` é interpretado; cinco obras empatam em 1,0; O Cão dos Baskervilles aparece em quarto | “Detetive” é reduzido ao tema amplo e não há classificação específica no catálogo. Apenas dois títulos têm julgamento positivo: teto de P@5 é 0,4. Requer vocabulário e metadados mais específicos, com proveniência. |
| b06 — Romance introspectivo | Jane Eyre em primeiro; Orgulho e Preconceito em sétimo, empatado em 0,5 com obras apenas introspectivas | Desempate alfabético ignora a distinção entre gênero pedido e atmosfera. Teto de P@5 também é 0,4, por haver dois títulos relevantes. |
| m06 — Piano acolhedor | Só `acolhedor` é interpretado; Concerning Hobbits ocupa a quinta posição e Gymnopédie No. 1 a sexta | Instrumento não existe no vocabulário nem nos metadados locais. River Flows in You, julgado parcialmente relevante, nem entra no conjunto por não ter `acolhedor`. Não inferir instrumentação apenas por artista ou pelo conjunto de avaliação. |

## Mudança aceita

Na descoberta **local de livros**, a quantidade total de temas correspondentes continua sendo o primeiro critério. Em empates, prefere-se a quantidade de gêneros pedidos explicitamente que o item atende; o título permanece o último desempate. Vocabulário: fantasia, ficção científica, mistério, terror, romance, aventura e cyberpunk, já presentes na interpretação e no catálogo.

Gêneros herdados de um título de referência não recebem prioridade extra. Exclusões, remoção das referências e limite de dois livros por autor permanecem obrigatórios. Não se trata de filtro rígido: obras com outros temas ainda podem aparecer depois. Não houve alteração de dados, músicas, leitura ou caminho online experimental.

`parsed_query.preferred_genres` expõe a preferência e `scores.genre` a fração atendida (0–1). A explicação registra o critério quando aplicável. O código usa categorias, sem títulos, IDs ou consultas do corpus como condições.

## Resultados v5 → v6

| Livros | v5 | v6 |
| --- | ---: | ---: |
| Precision@5 | 0,653333 | 0,666667 |
| nDCG@5 | 0,874959 | 0,893544 |
| Diversidade@5 | 0,800000 | 0,813333 |
| Precision@10 | 0,366667 | 0,366667 |
| nDCG@10 | 0,894982 | 0,906162 |

Sem regressões agregadas **ou por caso** contra v5 nos dois valores de K. Comparador estrito retorna 0. Hash do catálogo não mudou; música e os cinco modos de leitura preservam listas e métricas.

- b06: Orgulho e Preconceito sobe para segundo; P@5 passa de 0,2 para 0,4 e nDCG@5 de 0,787155 para 1. Em K=10, nDCG passa de 0,899605 para 1.
- b04 (Terror sombrio): Frankenstein sobe para segundo; nDCG passa de 0,934076 para 1 em ambos os K.
- b02 (Ficção científica com política): em K=10, nDCG passa de 0,988853 para 0,990231; top-5 preservado.

Não é validação humana independente: a regra foi motivada por falhas vistas no corpus editorial. b03 e m06 continuam com os mesmos limites, explicitados acima; não foram “resolvidos” por alterar julgamentos ou apenas renomear resultados.

## Validação e continuidade

192 testes da API, Ruff e formatação aprovados. Testes sintéticos verificam que contexto maior vence o gênero e que exclusões/referências/limite de autor prevalecem. Testes pela API verificam ordem, preferência explícita e explicação; comparação contra os relatórios v6 protege métricas por consulta.

Relatórios: `local-v6-genres-k5.json` e `local-v6-genres-k10.json`, incluindo comparação com v5. Em `api/`:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.runner --baseline ../docs/eval-reports/local-v5-cinematic-k5.json --fail-on-case-regression
.\.venv\Scripts\python.exe -m app.evaluation.runner --k 10 --baseline ../docs/eval-reports/local-v5-cinematic-k10.json --fail-on-case-regression
```

Próxima etapa: obter metadados verificáveis de instrumentos/subgêneros para as obras já existentes antes de ampliar o catálogo; avaliar a interpretação específica de piano/detetive sem alterar o corpus v1. Manter revisão humana/conjunto reservado pendentes.
