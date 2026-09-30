# Comparação por consulta na avaliação local

Data: 2026-09-30. A ferramenta mudou; ranking, corpus, catálogo e baselines aceitos não mudaram.

## Diagnóstico e política de aceitação

`--baseline` acrescenta `comparison` ao JSON impresso e ao relatório de `--output`. Cada caso alterado inclui ID, módulo/modo, títulos antes/depois, métricas alteradas com delta e `regressed_metrics`. `case_regressions_count` conta casos com ao menos uma perda. Reordenações de títulos aparecem mesmo quando não mudam métricas; a ordem das linhas do relatório não altera o pareamento por ID.

Mantida a política existente: o código de saída padrão é 1 quando alguma métrica agregada por módulo ou modo piora, com tolerância de 0,000001. `--fail-on-case-regression` adiciona o bloqueio por qualquer caso com perda, usando a mesma tolerância. A opção não reclassifica retroativamente o ranking v5 como aprovado por essa política mais estrita.

Métrica antes numérica que fica indisponível (`null`) conta como perda; uma métrica antes indisponível que passa a ser calculada aparece sem delta numérico. Comparações exigem mesmo hash do dataset, K, definições de métricas, grupos e conjunto de IDs; módulos/modos de cada caso devem permanecer iguais. Mudança de catálogo é sinalizada por `catalog_changed`, permitindo experimentos controlados sem ocultá-la.

## Evidência nos relatórios aceitos v4 → v5

Ambos os valores de K têm três casos alterados, todos CINEMATIC; demais casos preservados. Nenhuma regressão agregada, mas K=5 tem um caso com perda e K=10 tem dois.

| Caso | K | Mudanças de métricas |
| --- | --- | --- |
| r07 — Duna | 5 | Precision 1,0 → 0,8; nDCG 1,0 → 0,939212 |
| r08 — O Hobbit | 5 | Precision 0,6 → 0,8; nDCG 0,807928 → 0,815435 |
| r09 — O Jardim Secreto | 5 | nDCG 0,735875 → 0,809068 |
| r07 — Duna | 10 | nDCG 0,991789 → 0,985973 |
| r08 — O Hobbit | 10 | nDCG 0,829542 → 0,815435 |
| r09 — O Jardim Secreto | 10 | Precision 0,4 → 0,5; nDCG 0,809551 → 0,962564; diversidade 0,9 → 1,0 |

As perdas são informações para decisão e revisão, não justificativa para ajustar julgamentos a favor do ranking. O corpus continua editorial, consultado no desenvolvimento, sem revisão humana independente ou conjunto reservado.

## Reprodução

Em `api/`:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.runner --baseline ../docs/eval-reports/local-v4-calm-k5.json --output .local/eval-v5-v4-k5.json
.\.venv\Scripts\python.exe -m app.evaluation.runner --k 10 --baseline ../docs/eval-reports/local-v4-calm-k10.json --output .local/eval-v5-v4-k10.json
.\.venv\Scripts\python.exe -m app.evaluation.runner --baseline ../docs/eval-reports/local-v4-calm-k5.json --fail-on-case-regression
```

Saídas esperadas para o ranking v5: 0, 0 e 1, respectivamente. O relatório é salvo mesmo quando há regressão; entradas incompatíveis falham antes da escrita. Sem baseline, a avaliação independente continua disponível. A proteção de saída compara caminhos resolvidos e impede substituir os arquivos de entrada.

186 testes da API, Ruff e formatação aprovados. Testes cobrem a perda real de Duna, reordenação por ID, métricas nulas, tolerância, relatórios incompatíveis, modo estrito, preservação do gate agregado e proteção de entradas.

Próxima etapa: diagnosticar as consultas de mistério/detetive, romance introspectivo e piano com baixa precisão, separando interpretação, cobertura de catálogo e ordenação antes de propor novo ranking.
