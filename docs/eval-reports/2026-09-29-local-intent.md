# Avaliação de exclusões do parser local — 2026-09-29

## Escopo e reprodução

Corpus determinístico em `api/tests/test_intent_rules.py`: 24 consultas em português com conjuntos esperados de temas positivos e negativos. Execute a partir de `api/`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_intent_rules.py -q
```

Dois testes adicionais verificam as exclusões no ranking e nas explicações, um para livros e outro para músicas. Os casos não dependem de rede, chaves ou modelos externos.

## Resultado

- 24/24 consultas retornam exatamente os temas esperados.
- 2/2 verificações do ranking retornam itens de aventura, sem os temas excluídos romance e terror, e explicações consistentes.
- Cobertura: listas com `e`, `ou`, `nem` e vírgulas; marcadores de exclusão; pontuação e quebra de linha; adversativas; retomada explícita de preferência; caixa/acentos; conflito positivo/negativo; consulta desconhecida.

Antes da correção, `sem romance, terror e política` incluía política como tema positivo, e `sem terror. Fantasia` excluía fantasia indevidamente. O novo processamento segue a ordem dos temas e propaga exclusões apenas por conectores de lista. Pontuação forte e adversativas encerram esse escopo; textos intermediários como `prefiro` também interrompem a propagação.

## Limites

Este é um corpus de regressão do parser, não uma avaliação independente de relevância. Não mede Precision@K, nDCG, diversidade, qualidade da IA online ou todos os modos de leitura. Não satisfaz sozinho os gates G2/G3 do roadmap.

O vocabulário continua limitado a aliases editoriais. Vírgulas entre temas mantêm o escopo da lista; para retomar uma preferência positiva, usar uma frase nova, adversativa ou verbo explícito. Exclusões prevalecem quando o mesmo tema é pedido e rejeitado. `pouco` e `menos` continuam sendo exclusões, não pesos graduais.

Próxima avaliação: construir julgamentos de relevância independentes para pelo menos 15 consultas por módulo, incluindo referências e modos de leitura, antes de ajustar pesos ou ampliar promessas de compreensão.
