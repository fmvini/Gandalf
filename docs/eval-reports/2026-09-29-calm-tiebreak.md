# Experimento aceito: desempate do modo Calma

Data: 2026-09-29. Ranking `local-rules-v4`. Dataset `local-editorial-v1` e baselines v3 preservados.

## Hipótese e alteração

FOCUS e CALM tinham as mesmas regras locais. Ambos continuam exigindo energia baixa, e a preferência vocal permanece explícita (FOCUS força instrumental). Em CALM, empates de afinidade com livro/contexto favorecem etiquetas atmosféricas e reduzem preferência por etiquetas cinematográficas: `reading_mode = 1[atmosférico] - 1[cinematográfico]`. A ordem usa contexto primeiro, depois esse valor, depois título.

Não há ajuste por nome de faixa, livro ou ID do corpus. O desempate não remove candidatos, não enfraquece filtros e não supera maior afinidade contextual. `scores.reading_mode` e a explicação indicam esse critério, que é uma preferência editorial, não medição de áudio. Afeta somente leitura no modo local; descoberta e seleção online não foram alteradas.

## Resultado

| Métrica | v3 | v4 |
|---|---:|---:|
| CALM Precision@5 | 0,800000 | 0,933333 |
| CALM nDCG@5 | 0,920740 | 0,979737 |
| Leitura Precision@5 | 0,800000 | 0,826667 |
| Leitura nDCG@5 | 0,911473 | 0,923273 |
| Leitura Precision@10 | 0,540000 | 0,540000 |
| Leitura nDCG@10 | 0,946039 | 0,950154 |

Nenhuma regressão nos agregados por módulo ou modo em K=5/K=10. Descoberta de música/livros e os outros modos preservam resultados. FOCUS e CALM agora diferem na ordem top-5 dos três livros avaliados; em Duna também muda a seleção. Isso não significa que os modos sempre produzirão listas diferentes: catálogos sem candidatos empatados com etiquetas relevantes podem continuar iguais.

Testes verificam diferenciação via API com os mesmos filtros rígidos e um cenário sintético em que contexto maior precisa vencer a preferência de modo. A suíte também compara contra os resultados aceitos de v4, para não perder os ganhos mantendo apenas o limiar antigo.

## Reprodução

Em `api/`:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.runner --baseline ../docs/eval-reports/local-v3-baseline-k5.json
.\.venv\Scripts\python.exe -m app.evaluation.runner --k 10 --baseline ../docs/eval-reports/local-v3-baseline-k10.json
.\.venv\Scripts\python.exe -m pytest -q
```

Resultados completos: `local-v4-calm-k5.json` e `local-v4-calm-k10.json`. O corpus continua pequeno e editorial, sem revisão humana independente; a melhoria não prova qualidade geral nem fecha G4. Próximo experimento: modo CINEMATIC, com a mesma política de comparação e sem reescrever julgamentos.
