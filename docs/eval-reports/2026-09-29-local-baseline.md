# Baseline editorial local — 2026-09-29

Ranking `local-rules-v3`; dataset `local-editorial-v1`: 45 consultas (15 música, 15 livros, 15 leitura, com três livros nos cinco modos). Não houve ajuste de pesos durante a coleta.

## Reprodução

Em `api/`, com dependências de desenvolvimento instaladas:

```powershell
.\.venv\Scripts\python.exe -m app.evaluation.runner --baseline ../docs/eval-reports/local-v3-baseline-k5.json
.\.venv\Scripts\python.exe -m app.evaluation.runner --k 10 --baseline ../docs/eval-reports/local-v3-baseline-k10.json
.\.venv\Scripts\python.exe -m pytest tests/test_evaluation.py -q
```

`--output caminho.json` grava relatório completo. Os baselines versionados não devem ser sobrescritos para esconder regressões: novos experimentos usam outro arquivo. A comparação exige mesmo SHA-256 do dataset, K e versão das métricas; regressões em qualquer média por módulo ou modo de leitura geram exit code 1. O teste normal do backend compara K=5 e K=10. Cada relatório inclui hash do catálogo, versão do ranking, listas retornadas, violações e métricas por consulta.

## Metodologia

- Julgamentos escritos pelo assistente de desenvolvimento a partir das consultas e características das obras, separados do código e antes de executar o ranking. Não são validação humana independente nem conjunto de teste reservado.
- Catálogo fechado: 18 livros e 25 músicas. Grau 3 = forte adequação, 2 = relevante, 1 = adequação parcial; títulos omitidos recebem zero. Alterar julgamentos exige revisão explícita, versão nova e justificativa.
- Precision@K usa denominador K, inclusive se vierem menos resultados; duplicatas só pontuam na primeira ocorrência. nDCG usa ganho `2^grau - 1`, desconto `log2(posição + 1)` e ideal ordenado dos julgamentos disponíveis. Sem ideal relevante, nDCG é zero.
- Diversidade = criadores distintos / K. Preenchimento = itens retornados / K. Cobertura = proporção de consultas com pelo menos K itens. Listas vazias contam zero nessas métricas e em Precision/nDCG.
- Existência verifica IDs no catálogo embarcado, **não** a disponibilidade atual de links ou gravações externas. Satisfação de restrições usa expectativas explícitas do dataset, sem consultar o parser para produzir o resultado esperado.
- Existência e satisfação são `null` em listas vazias; agregados ignoram esses nulos. `nonempty`, preenchimento e cobertura permitem identificar esse caso sem atribuir sucesso artificial a resultados vazios.
- Médias são por consulta. O comparador permite variações até `0.000001` decorrentes de arredondamento. Ganhos em um modo não podem ocultar regressões em outro, mas médias ainda podem ocultar perdas individuais: revisar também as listas por caso.
- Execução offline, sem banco, LLM ou rede. Não mede conformidade de saída do LLM, latência de providers, preferências de usuários ou qualidade online.

## Resultados

| Módulo | P@5 | nDCG@5 | Diversidade@5 | Cobertura@5 | P@10 | nDCG@10 | Cobertura@10 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Música | 0,6933 | 0,9093 | 0,7600 | 46,67% | 0,4600 | 0,9365 | 26,67% |
| Livros | 0,6533 | 0,8750 | 0,8000 | 66,67% | 0,3667 | 0,8950 | 0% |
| Leitura | 0,8000 | 0,9115 | 0,9867 | 100% | 0,5400 | 0,9460 | 73,33% |

Nos dois valores de K, todas as consultas retornaram itens; existência no catálogo, restrições avaliadas e limite de dois itens por criador ficaram em 100%. A baixa Precision@10 também reflete a falta de dez itens relevantes no catálogo; nDCG não penaliza essa escassez quando o ideal disponível é curto, portanto não deve ser interpretado isoladamente.

FOCUS e CALM retornaram exatamente o mesmo top-5 em Duna, O Hobbit e O Jardim Secreto. CINEMATIC teve P@5 de 0,7333 e nDCG@5 de 0,8479, inferiores aos demais modos. São prioridades de melhoria; o baseline não aprova G4 nem demonstra diferenciação suficiente dos modos.

## Estado dos gates e próximos experimentos

O registro cumpre a medição inicial do caminho local; não conclui G2/G3 do motor completo com embeddings/IA. Próximos passos:

1. Reconciliar a especificação/ADRs com o modo online existente e separar contratos atuais dos planejados.
2. Definir critérios distintos e explicáveis para FOCUS/CALM/CINEMATIC e comparar experimentos sem alterar este dataset para favorecer o ranking.
3. Revisar consultas com baixa precisão (mistério de detetive, romance introspectivo, pedidos de piano) antes de ampliar o catálogo.
4. Obter revisão humana dos julgamentos e criar conjunto reservado para evitar otimização excessiva neste corpus.
