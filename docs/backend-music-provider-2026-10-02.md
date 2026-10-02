# Backend — MusicProvider inicial — 2026-10-02

Unidade implementada e congelada para revisão/commit serializado pelo Maestro.
Base consultada: `docs/DEVELOPMENT_LOG.md`, `docs/CONTINUATION.md` e
`docs/adr/0004-external-data-providers.md`. Não conclui toda a Fase 2 nem G1.

## Contrato implementado

`api/app/providers/base.py` define `MusicProvider` estrutural, no padrão de
`BookProvider`, com `name: str` obrigatório e somente este método:

```python
async def search(
    query: str,
    limit: int = 20,
    *,
    by_tag: bool = False,
    offset: int = 0,
    reading: bool = False,
    instrumental: bool = False,
) -> MusicSearchResult: ...
```

O resultado tipado contém `items`, `total`, `provider` e `has_more`.
`total` conserva a semântica MusicBrainz atual: quantidade normalizada da página,
não total global da fonte. `has_more` comunica disponibilidade de outra página;
o consumidor conserva seus limites, offset e cursores atuais.

`MusicItem` contém `id`, `title`, `artist`, `tags`, `duration_ms`, `has_vocals`,
`energy`, `provider`, `external_id`, `links` e `classification_source` opcional.
Duração, voz e energia podem ser `None`; energia informada aceita
`low/medium/high`. `False` permanece instrumental; ausência de evidência
permanece desconhecida. Valores conhecidos não significam medições acústicas.
Proveniência vigente: `provider_tags` ou `ai_estimate`, somente quando informada
ou efetivamente derivada; ausência não é rotulada como catálogo local.

Precondições do adaptador: `name` externo não vazio, diferente de `local`, igual
ao `provider` do resultado e dos itens; UUID canônico estável em namespace da
fonte + identificador externo; normalização/validação de metadados e URLs na
fronteira. MusicBrainz mantém exatamente UUID5 da URL de recording, sem
recalcular IDs legados. TypedDict/Protocol não introduzem validação Pydantic em
runtime: a injeção é de um adaptador confiável que deve cumprir o contrato.
A leitura também verifica consistência de origem no envelope e em cada item.

`links.provider` identifica a gravação na fonte; `links.search` pode estar
ausente. MusicBrainz conserva a busca YouTube atual. Não há promessa de áudio,
novas fontes, `get_by_id`, similaridade ou seleção de adaptador por `.env`.

## Factory, recursos e armazenamento

`create_app(..., music_provider=None)` aceita o adaptador diretamente, sem
remendar `app.state`. Online usa a instância fornecida ou cria MusicBrainz por
lifespan. Busca e serviços de descoberta/leitura recebem a mesma instância.
Offline ignora a injeção e mantém catálogo/ranking/trilha locais, sem abrir
cliente externo quando livros também são locais.

Recursos de um adaptador injetado pertencem ao caller: a factory não chama seu
`aclose`, não fecha seu cliente/store/engine e não administra sua configuração.
O cliente externo criado pela aplicação continua compartilhado entre Groq e
adaptadores default, sendo fechado pelo contexto do lifespan. Apps não herdam
provider, cliente ou store de outra factory; reiniciar o lifespan recria o
MusicBrainz default.

Cache, rate limit, normalização e persistência são responsabilidades do
adaptador. MusicBrainz mantém `OnlineStore`, TTL/chaves de cache, throttling,
User-Agent e filtros de busca existentes. O adaptador injetado deve persistir
itens no catálogo acessível ao `OnlineStore` da aplicação se precisar atender
`GET /music/{id}` e seleção manual de playlist. Apenas devolver itens em
`search` não garante detalhe; a factory não adiciona persistência implicitamente.
O teste de detalhe usa SQLite descartável e recursos fornecidos pelo caller.
Store/modelos/migrations/dados existentes não foram alterados.

## Consumidores e proveniência

- Descoberta preserva valores conhecidos mesmo quando Selection discorda.
  Somente preenchimento válido de voz/energia desconhecida marca `ai_estimate`,
  independentemente da fonte. Choice `unknown` conserva `None`; filtro
  instrumental continua exigindo `False`. Catálogo original não é mutado.
- Hints e explicações identificam a fonte efetiva. Estimativas são descritas
  como preenchimento de atributos desconhecidos, sem alegar que todos os
  atributos conhecidos foram estimados. BOOK conserva seu contrato/texto.
- Leitura aceita somente fonte externa coerente com `music.name`, duração
  inteira informada entre 90 e 600 segundos, diversidade e filtros atuais.
  Não usa duração estimada nem catálogo local para completar sessão online.
  Tags só preenchem voz/energia quando `None`, marcando `provider_tags` quando
  a derivação realmente ocorre. Não sobrescrevem `True` ou energia conhecida.
  Tags descrevem atmosfera/evidência editorial, não medição acústica.
- Paginação, limite de páginas/faixas/artista, exclusões cumulativas, IDs,
  fallback de descoberta e regras de duração são preservados. Adaptador diverso
  não é atribuído ao MusicBrainz nas fontes/explicações/hints.

## Arquivos da unidade

- `api/app/providers/base.py`
- `api/app/providers/musicbrainz.py`
- `api/app/main.py`
- `api/app/services/online_recommendations.py`
- `api/app/services/online_soundtrack.py`
- `api/tests/test_music_provider.py` (novo)
- `api/tests/test_continuation.py`: somente fixture `Music`, autorizada pelo
  Maestro, com `name="musicbrainz"` e envelope `provider/total`; algoritmos e
  asserções intactos. Sem origem default para compensar fixture sem contrato.
- `docs/backend-music-provider-2026-10-02.md` (este relatório)

`test_reroll.py` não precisou ser alterado. Arquivos dos colegas, documentação
compartilhada, auth/security e schema permaneceram fora desta unidade.

## Evidência offline

Todas as execuções em `api`, normais, sem elevação. Plugin temporário existente
substitui somente `tmp_path` por diretório que herda ACLs do workspace; não muda
aplicação, algoritmo ou asserções. Testes usam catálogos sintéticos, FakeAI e
HTTPX MockTransport: nenhum request real a API8000, fonte externa ou LLM.

Antes da correção de tags, reprodução seletiva de três casos retornou
**3 failed / 25 deselected**: voz conhecida sobrescrita (`200` em vez de `503`),
energia conhecida sobrescrita (`503` em vez de `200`) e proveniência ausente
após derivação. Os três casos passaram no subset final.

```powershell
$env:PYTHONPATH='../.impeccable/runtime'
& .venv/Scripts/python.exe -m pytest -q -p no:tmpdir -p no:cacheprovider -p maestro_pytest_temp tests/test_music_provider.py tests/test_online.py tests/test_continuation.py tests/test_reroll.py tests/test_ai_selection.py tests/test_music_filters.py --tb=short
```

Resultado: **163 passed / 1 warning em 26.61s** (29 novos + 134 existentes
afetados). Abrange argumentos/flags, search via factory, descoberta/reroll,
trilha, fontes, conhecidos/desconhecidos/proveniência, gates de duração e voz,
offline, isolamento entre apps, lifecycle/client e cache/IDs default.

Após correção equivalente `dict(...)` → literal exigida pelo Ruff no novo teste,
somente `tests/test_music_provider.py` foi reexecutado com os mesmos flags:
**29 passed / 1 warning em 2.01s**. Warning existente é depreciação Starlette/
HTTPX TestClient; não houve troca de dependência.

```powershell
& .venv/Scripts/ruff.exe check app/providers/base.py app/providers/musicbrainz.py app/main.py app/services/online_recommendations.py app/services/online_soundtrack.py tests/test_music_provider.py tests/test_continuation.py
& .venv/Scripts/ruff.exe format --check app/providers/base.py app/providers/musicbrainz.py app/main.py app/services/online_recommendations.py app/services/online_soundtrack.py tests/test_music_provider.py tests/test_continuation.py
```

Ruff **PASS**, format **7 arquivos conformes**; diff seletivo revisado e
`git diff --check` seletivo **PASS**. Não foi repetida suíte geral/auth.

## Freeze e limites

Código, testes e relatório liberados ao Maestro, sem stage/commit/push pelo
Backend. Nenhum processo existente, configuração, chave, modelo, quota, TTL,
schema ou dado real foi alterado; nenhum probe/restart foi feito.

Isto valida integração por port com fontes simuladas, não qualidade de outra
fonte real nem ranking online novo. Maestro serializa commits, documentação
compartilhada e eventuais gates posteriores. Ampliar métodos/fontes/configuração
exige outra unidade; responsabilidade de persistência deve continuar explícita.
