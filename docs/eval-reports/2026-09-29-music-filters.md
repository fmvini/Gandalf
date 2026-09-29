# Avaliação de filtros musicais — 2026-09-29

## Escopo

Regressões observadas: `não quero instrumental` selecionava instrumentais; `sem energia alta` selecionava energia alta; energia média não era reconhecida localmente. O modo online também usava regras duplicadas e não reaplicava exclusões de energia.

O novo módulo `api/app/services/music_filters.py` resolve os filtros antes do ranking. Os dois modos compartilham o mesmo predicado de aceitação. Filtros explícitos prevalecem; negações de energia mantêm os demais níveis disponíveis, e informações desconhecidas não satisfazem restrições.

## Corpus e execução

Execute em `api/`:

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_music_filters.py tests/test_recommendations.py tests/test_online.py -q
```

- 26 consultas com valores esperados exatos de voz, energia e exclusões.
- Três pedidos contraditórios e um teste de precedência por dimensão.
- Sete consultas verificadas pela API contra os itens reais do catálogo local; teste adicional de validação e exclusões explícitas.
- Quatro cenários online com seleção da IA ou fallback; três cenários com energia baixa, alta ou desconhecida; um cenário confirma rejeição de conflito antes de acessar providers.
- Providers e IA usam transporte simulado. Nenhuma chamada externa ou credencial real é necessária.

Resultado: os 46 novos casos passaram; suíte completa da API com 119 testes aprovados. Ruff, formatação, smoke/E2E com API real e build do frontend também passaram. A suíte da API mantém um aviso de depreciação de Starlette/httpx.

## Limitações

Este corpus verifica restrições e consistência, não relevância semântica. Não substitui julgamentos independentes de Precision@K/nDCG. Comparativos (`menos energia`), dupla negação e listas abreviadas (`sem energia alta ou média`) não fazem parte do vocabulário garantido; usar os filtros estruturados para pedidos não cobertos. Metadados de energia/vocais estimados pela IA continuam sujeitos a erro.

Próxima etapa: avaliar referências por título e construir julgamentos de relevância separados dos testes de implementação, incluindo os cinco modos de leitura.
