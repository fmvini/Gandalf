# Backend — preparação G1 offline — 2026-10-03

Unidade implementada e congelada para revisão/serialização pelo Maestro. HEAD
de entrada `df7891ac505a3cf6f230dcf2047da721b79a3a90`, árvore inicialmente limpa.
Consultados DEVELOPMENT_LOG, CONTINUATION e contrato MusicProvider. Proposta
enviada/aprovada via Maestri antes dos edits; ajustes de revisão incorporados.

## Escopo entregue

Somente três arquivos próprios:

- `api/scripts/music_provider_eval.py`: CLI exclusivamente stdlib.
- `api/tests/test_music_provider_eval.py`: testes focados sintéticos/manifestos.
- `docs/backend-music-evaluation-2026-10-03.md`: este relatório exclusivo.

Não altera aplicação, adaptadores, models, schema, deps, CI, runtime ou dados.
Maestro reserva Git e documentação compartilhada. Plano/amostras estão nos
documentos e manifestos preparados pelo Maestro, não modificados pelo Backend.

## CLI e entrada v1

Na pasta `api`:

```powershell
& .venv/Scripts/python.exe scripts/music_provider_eval.py INPUT.json
# Alternativa: passar '-' para ler JSON binário de stdin.
```

A entrada exige exatamente `schema_version=1`, `evidence_kind` (`fixture` ou
`recorded`), `stage` global (`provider_search` ou `recommendation`), `cases`
(`id/group`), `providers` (nomes) e `observations`. Cada observação exige
`case_id`, `provider`, `outcome` (`success/error`) e `result`: MusicSearchResult
normalizado em sucesso, null em erro. Não lê respostas brutas de recomendações
nem coleta/transforma resultados do aplicativo. Fases não podem ser misturadas.

Cases/groups/providers são tokens ASCII `[A-Za-z0-9][A-Za-z0-9_-]*`, até
64 caracteres para cases/groups e 32 para providers. Identificadores únicos,
referências declaradas e campos obrigatórios são verificados. Limites:
4 MiB de entrada, 200 cases, 16 providers, 3.200 observações e 100 itens por
resultado. Cases/providers/observações vazios são permitidos; pares não
observados permanecem missing. JSON recusa chaves duplicadas e NaN/Infinity.

Validação do resultado: envelope/item provider consistente, UUID string
canônica, campos obrigatórios de MusicItem, texto/tags/links com tipos corretos,
voz bool/null, energia enum/null, duração null ou inteiro positivo e
classification_source opcional `provider_tags/ai_estimate`. Bool não é inteiro.
Links aceitam somente HTTP(S) com hostname/porta válidos, sem credenciais ou
controles/whitespace. Classificação ausente não é acrescentada ou medida.

`total` é inteiro declarado **>= len(items)**; `has_more` é apenas bool declarado.
O avaliador não soma totais, não infere tamanho global nem esgotamento do
catálogo. No MusicBrainz atual, `total=len(items normalizados)` e count upstream
serve ao cálculo de has_more; o avaliador genérico aceita também outros totais
declarados, como o total30 deliberadamente fictício da fixture do Maestro.

## Saída, métricas e identidade

stdout contém somente JSON agregado determinístico. Não retorna títulos,
artistas, external_id, UUIDs, URLs, payloads, caminhos de entrada ou mensagens
do upstream. Somente os tokens públicos validados de provider/group voltam
como chaves; violações usam códigos fixos e contadores. Falha de JSON/IO/schema/
limites retorna erro genérico sem traceback ou detalhes em stderr.

Exit codes: **0** entrada avaliada sem violações de contrato, **1** relatório
com violações, **2** entrada/IO inválidos. Erro declarado, missing e sucesso
vazio são estados distintos válidos; nenhum deles constitui aprovação G1.
`g1_approved=false` e `g1_status=NOT_EVALUATED` são invariáveis, inclusive para
evidence_kind recorded e mesmo que todos os atributos estejam preenchidos.

Agregações totais, por provider e por group/provider:

- Matriz de pares expected/observed/missing/ambiguous. Repetir a mesma observação
  case/provider não acrescenta cobertura; todas ficam ambíguas, sem vencedor.
- Observações error/success_empty/success_nonempty/invalid_result. Contagens de
  observações podem superar pares observados quando há duplicatas explícitas.
- Linhas reported/typed_valid/invalid separadas dos UUIDs e identidades únicos.
  typed_valid refere-se aos campos/envelope, não à identidade global coerente.
- UUIDs, pares únicos `(provider,external_id)`, conflitos e quantidades elegíveis
  explícitos. Duplicata de UUID dentro do mesmo resultado é violação; repetir
  item coerente em cases diferentes é reobservação normal.
- Repetições exatas adicionais, identidades reobservadas, identidades com
  metadados diferentes e variantes extras de metadados têm contadores próprios.
  Mudança de tags/metadados sob a mesma identidade não é colisão por si.

Os mapas UUID→identidades e identidade→UUIDs são construídos antes da agregação,
inclusive quando UUID/provider/external_id são válidos, mas outra metadata ou
o envelope são inválidos. UUID compartilhado por identidades distintas e mesma
identidade com UUIDs distintos geram violações/quarentena global. Mesmo external_id
em providers diferentes não é conflito se UUIDs forem distintos. Não há escolha
arbitrária de payload vencedor; a ordem das observações não muda o relatório.

Cobertura de atributos usa UUIDs elegíveis únicos, excluindo conflitos de
identidade e pares de observação ambíguos. Denominadores aparecem em cada
métrica/provider/group. Atributos são known/null/mixed_null_known; valores
conhecidos divergentes recebem contador próprio. Taxas são null quando o
denominador é zero, nunca uma taxa artificial de sucesso.

Duração 90–600s inclusivos é descrita como in/out/null/mixed entre reobservações.
Isto não aplica filtros nem certifica uma trilha. Classificação tem contadores
missing/provider_tags/ai_estimate/mixed e é **itemwide**: ai_estimate pode marcar
apenas energia inferida e voz conhecida, sem atribuir origem individual a campos.
Tags present exige pelo menos uma string não vazia após strip; não infere gênero,
instrumental ou energia a partir de tags. Known não significa medição ou verdade.

## Validação desta unidade

Executado normalmente, sem elevação, somente novo módulo de testes. Reutilizado
plugin tmp_path existente que herda ACLs do workspace; sem alterar asserções ou
aplicação. CLI main capturado no processo de teste (sem subprocesso). Testes
verificam imports stdlib e bloqueiam socket/entrada em app ou libs de rede/DB.

```powershell
# cwd api
$env:PYTHONPATH='../.impeccable/runtime'
& .venv/Scripts/python.exe -m pytest -q -p no:tmpdir -p no:cacheprovider -p maestro_pytest_temp tests/test_music_provider_eval.py --tb=short
& .venv/Scripts/ruff.exe check scripts/music_provider_eval.py tests/test_music_provider_eval.py
& .venv/Scripts/ruff.exe format --check scripts/music_provider_eval.py tests/test_music_provider_eval.py
```

Final: **84 passed em 0.30s**, Ruff PASS, formato **2 arquivos conformes**.
Rodadas anteriores 77/83 passaram; só foram repetidas após os ajustes novos.
Cobertos strict types/nulls/campos, envelopes/fontes, links, limites e JSON
inválido, stdin/IO, sanitização, conflitos antes de descartar metadata inválida,
quarentena/invariância de ordem, denominadores, repetições e separação de fases.

Manifestos root lidos, sem edição:

- `docs/evaluation/music-provider-fixture-v1.json`: **6 pares expected,
  5 observed, 1 error, 1 empty, 3 nonempty, 1 missing, 3 linhas**; proveniência
  1 missing/1 provider_tags/1 ai_estimate. Fixture nunca aprova G1.
- `docs/evaluation/music-provider-g1-snapshot-template.json`: **12 cases,
  2 providers, 24 pares missing, zero observações**, taxas sem denominador null.
  O nome recorded não transforma template vazio em evidência real.

## Freeze e limitações

Três arquivos liberados ao Maestro. Nenhum stage/commit/push, suíte geral,
coleta/API/LLM/cache/engine/processo, credencial, dado real, CI ou nova dependência.
Testes offline não provam chamadas recentes, disponibilidade, determinismo
temporal, constraints/TTL, precisão dos atributos, qualidade auditiva, licença,
latência ou G1. Orçamento explícito e revisão humana continuam necessários antes
de coletar snapshots reais; a ferramenta nunca decide aprovação desse gate.
