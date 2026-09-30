# Experimento aceito: desempate do modo Cinematográfico

Data: 2026-09-30. Ranking `local-rules-v5`. Dataset `local-editorial-v1`, catálogo e julgamentos preservados.

## Critério implementado

Na leitura local CINEMATIC, a relevância contextual continua sendo o primeiro critério. Em empates, prioriza-se o artista menos representado na seleção; depois, a presença da etiqueta editorial `cinematográfico`; por último, o título. O limite de duas faixas por artista e os filtros permanecem obrigatórios. `scores.reading_mode` vale 1 para a etiqueta cinematográfica e 0 caso contrário; a explicação descreve o desempate.

O acréscimo do tema cinematográfico ao contexto, já existente, foi preservado. Não se exige energia alta nem se impede uma exclusão explícita como `sem cinema`. Outros modos, descoberta e caminho online não mudaram.

Uma primeira variante que usava somente a etiqueta no desempate foi descartada: reduziu a diversidade CINEMATIC em K=10 de 0,933333 para 0,900000. A variante aceita prioriza a variedade de artistas antes dessa etiqueta em contextos igualmente relevantes. O catálogo é pequeno; a seleção reordena os candidatos a cada faixa para considerar a contagem atual de artistas.

## Resultados

| Métrica CINEMATIC | v4 | v5 |
|---|---:|---:|
| Precision@5 | 0,733333 | 0,733333 |
| nDCG@5 | 0,847934 | 0,854572 |
| Diversidade@5 | 0,933333 | 0,933333 |
| Precision@10 | 0,466667 | 0,500000 |
| nDCG@10 | 0,876961 | 0,921324 |
| Diversidade@10 | 0,933333 | 0,966667 |

Não houve regressão agregada por módulo ou modo em K=5/K=10 contra v3/v4. Leitura agregada Precision@10 passou de 0,540000 para 0,546667 e nDCG@10 de 0,950154 para 0,959027. Os demais modos e os módulos de descoberta preservam resultados.

Isso não significa ausência de perdas individuais: Duna/CINEMATIC (`r07`) perde Precision@5 de 1,0 para 0,8. A política atual de aceitação compara agregados; relatórios completos mantêm as listas e métricas de cada consulta. O corpus é editorial, pequeno e foi consultado durante o desenvolvimento: não é teste reservado nem validação humana independente. G4 continua aberto.

## Validação e reprodução

157 testes da API aprovados, Ruff e formatação aprovados. Cenário sintético verifica prioridade de contexto, diversidade antes da etiqueta e limite de duas faixas por artista. Testes via API cobrem três livros, instrumentais, exclusão de temas e exclusão explícita da própria etiqueta cinematográfica.

Em `api/`:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.runner --baseline ../docs/eval-reports/local-v4-calm-k5.json
.\.venv\Scripts\python.exe -m app.evaluation.runner --k 10 --baseline ../docs/eval-reports/local-v4-calm-k10.json
.\.venv\Scripts\python.exe -m pytest -q
```

Relatórios aceitos: `local-v5-cinematic-k5.json` e `local-v5-cinematic-k10.json`. A suíte compara também com esses relatórios. Próxima etapa: expor perdas por consulta na ferramenta de avaliação e diagnosticar consultas de baixa precisão antes de ajustar vocabulário/catálogo.
