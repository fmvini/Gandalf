# Backend — metadados da seleção musical — 2026-10-02

## Estado e escopo

Auditoria offline, proposta e implementação autorizada concluídas; arquivos congelados para revisão/commit seletivo do Maestro. Base consultada: `8d94c76`, `docs/CONTINUATION.md` e `docs/DEVELOPMENT_LOG.md`. Git e os três documentos compartilhados pertencem ao Maestro; PostgreSQL/Docker pertence ao Banco. Nenhum restart, chamada externa/LLM, suíte geral, stage ou commit pelo Backend nesta unidade.

## Evidência concreta

Replay restrito à consulta pública **Jazz instrumental** e aos hashes derivados do gate anterior. SQLite aberto com `mode=ro`/`query_only`; transporte HTTP, reserva de IA e escritas de cache/catálogo recusados pelo harness. Nenhum outro prompt/cache privado foi lido. Artefatos ignorados: `.impeccable/runtime/backend-music-selection-payload-audit-20261002.py` e `.json`.

Comando executado fora do sandbox, na cwd `api`:

```powershell
& .venv/Scripts/python.exe ../.impeccable/runtime/backend-music-selection-payload-audit-20261002.py
```

- Replay completo: 18 candidatos, sendo 15 MusicBrainz e três locais; filtro resolvido `vocals=none`, energia sem restrição, seleção solicita até quatro escolhas para entregar três itens.
- Entrada do seletor: três candidatos possuem vocais/energia conhecidos, todos locais. Os 15 MusicBrainz não possuem esses valores conhecidos nessa amostra.
- Payload efetivamente produzido por `GroqClient.select`: zero ocorrências de `has_vocals`, `energy`, `provider` e `classification_source` nos 18 candidatos. Título/autoria/tags/descrição são enviados; duração é enviada apenas no fluxo de trilha.
- Selection em cache: zero escolhas. Resultado vazio reproduzido antes de rejeições por score, filtros, exclusões ou limite por artista; `ai_used=true`, `degraded=false`, `sources=[]`, `has_more=true`, `next_offset=15`.
- Zero chamadas de rede, reservas de IA e escritas de banco. Último consumo coordenado permanece **9/50**; esta auditoria não executou nova consulta de cota.

A perda de informação no payload é comprovada. A razão da omissão da IA não consta no schema; não atribuir o vazio a essa lacuna como causa demonstrada nem declarar o ranking musical externo aprovado.

## Unidade implementada após coordenação

Lista seletiva exata: `api/app/ai/groq.py`, novo `api/tests/test_ai_selection.py` e `docs/backend-music-selection-session-2026-10-02.md`. Somente seleção MUSIC recebe vocais booleanos ou nulos, energia válida ou nula e, **apenas quando já informados**, provider/origem da classificação. Nenhuma origem editorial/local é atribuída pela ausência de provider; nenhuma provenance é inventada. `provider_tags` e `ai_estimate` existentes são transmitidos literalmente e diferenciados pela instrução. Valores ausentes/inválidos permanecem desconhecidos, sem converter `None`, zero ou strings em instrumental.

A instrução usa classificações existentes como metadados, nunca medições acústicas; `ai_estimate` continua estimativa, provider não constitui evidência de classificação e origem ausente não pode ser inferida. Mapeamento explícito `has_vocals=false` para instrumental e `true` para vocal. Quando os metadados não sustentarem uma inferência de campos ausentes, conservar `unknown`. Relevância e escolha apenas entre os índices fornecidos continuam obrigatórias. Nenhuma obrigação de preencher a lista ou preferir fontes externas.

Payload e instrução BOOK preservados, com regressão da instrução literal. Schema público/Selection, interpretação, filtros estritos, exclusões, score mínimo, diversidade e campos/gates de duração da trilha não foram alterados. Provider/modelo/chave/cota/retries/TTL permanecem iguais. A chave Selection já inclui payload/instrução: o novo contrato muda naturalmente a seleção MUSIC, sem expurgar dados ou alterar Intent.

14 testes novos, sem rede/cache real: preservação de `False` versus desconhecido, energias válidas/inválidas, origem informada versus ausente/estimativa, ausência de mutação de dados, BOOK sem metadados musicais novos/instrução intacta e duração real/estimada da trilha preservada. Integração confirma que valores conhecidos vencem escolhas contraditórias, vocais desconhecidos não passam filtro instrumental e índice fora de candidatos não vira recomendação. Esses testes com fakes não comprovam conformidade da IA real.

Observação fora desta unidade: `online_recommendations.py` marca todo item MusicBrainz aceito como `ai_estimate`, mesmo se já possui `provider_tags`. Nenhuma correção desse contrato/proveniência de saída proposta como efeito incidental desta primeira mudança.

## Validação e limites

Comandos executados fora do sandbox, na cwd `api`:

```powershell
& .venv/Scripts/python.exe -m pytest -q tests/test_ai_selection.py tests/test_online.py tests/test_music_filters.py tests/test_reroll.py tests/test_continuation.py --tb=short
& .venv/Scripts/python.exe -m pytest -q tests/test_ai_selection.py --tb=short
& .venv/Scripts/python.exe -m ruff check app/ai/groq.py tests/test_ai_selection.py
& .venv/Scripts/python.exe -m ruff format --check app/ai/groq.py tests/test_ai_selection.py
git diff --check -- app/ai/groq.py tests/test_ai_selection.py ../docs/backend-music-selection-session-2026-10-02.md
```

- Subset de cinco módulos: **134 passed**, um aviso preexistente Starlette/TestClient sobre HTTPX, 22,34 s. Inclui gates de trilha/continuação, filtros/exclusões, reroll e integração online com fakes.
- Reexecução final dos novos testes após ajuste da instrução explicitando o mapeamento booleano e formatação: **14 passed**, 0,68 s.
- Ruff check PASS; format-check: dois arquivos já formatados. Diff-check seletivo PASS; aviso Git de conversão futura LF/CRLF, sem erro de whitespace.
- Inspeção offline do payload final: mesmos 18 candidatos e três pares conhecidos. `has_vocals`/`energy` presentes nos 18, nulos para valores desconhecidos; provider informado presente nos 15 MusicBrainz; `classification_source` ausente nos 18, preservando a ausência real. Nenhum provider foi inventado para os três locais.
- Artefatos ignorados finais: `.impeccable/runtime/backend-music-selection-payload-after-20261002.py` e `.json`. Mesmos hashes Intent/MusicBrainz públicos existentes; nova chave Selection não possui cache. O harness parou com `OfflineOnly/exact_cache_missing_or_expired`, sem tentar IA, renovar TTL ou escrever. Não reutilizou a resposta antiga como se pertencesse ao novo contrato.
- Nenhuma nova resposta/ranking da IA real foi obtida. Consumo último conhecido **9/50**, sem consumo por esta unidade; API/frontend/PG existentes e configuração preservados.

## Próximo checkpoint e freeze

Código e relatório liberados/congelados para Maestro revisar e serializar o commit local. Uma futura verificação real exige janela/plano de runtime e orçamento coordenados após o commit; nenhum restart ou chamada real autorizado nesta entrega. Mesmo após o payload corrigido, MUSIC externa exige item efetivamente entregue de fonte externa; candidatos/cache/HTTP200 isolados não fecham o gate. Não corrigir incidentalmente a provenance de saída ou perseguir novas consultas para forçar resultado.
