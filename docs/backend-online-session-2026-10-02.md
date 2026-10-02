# Backend — validação online real, 2026-10-02

## Implementado

- Retomada sobre HEAD `ffdd6a6`, árvore inicialmente limpa, após leitura de DEVELOPMENT_LOG/CONTINUATION. API reservada ao Backend, exceto modelos/migrations; Maestro reserva Git e os três documentos compartilhados. Sem stage/commit/push, restart ou duplicação da suíte geral.
- Identidade confirmada fora do sandbox: único listener `127.0.0.1:8000`, PID **31444**, launcher/ParentProcessId **39748**, comando Python312 `python.exe local.py`; banco conhecido `api/.local/gandalf.db` preservado. Status/readiness 200, online, Groq original `openai/gpt-oss-20b`, configured=true, SQLite/schema ok.
- Rodada pública limitada coordenada com Frontend/Banco: uma query Open Library e uma MusicBrainz por cliente/rodada, sem retry de fonte. Interpretação Groq somente após ambas responderem com dados reais. Todos os clientes validaram TLS; nenhum verify=False, CA baixada, proxy global ou segredo alterado.
- Gates adicionais autorizados pelo Maestro: duas requisições MUSIC com cursor/exclusões, uma BOOK e uma MUSIC com queries públicas específicas, uma imagem Open Library. Encerradas todas as chamadas externas/LLM ao atingir esse escopo; depois somente diagnóstico offline da query pública Jazz instrumental.

## Arquivos principais alterados

- `docs/backend-online-session-2026-10-02.md` — este registro exclusivo.

Nenhum arquivo de aplicação, schema, dependência, modelo/migration ou teste foi modificado nesta etapa. Scripts/resultados de diagnóstico ficam ignorados em `.impeccable/runtime/`, sem corpos sensíveis, prompts privados ou chaves.

## Decisões técnicas

- O primeiro probe usou HTTPX padrão/certifi, diferente da aplicação. Falhou em TLS com verify_code20 e não demonstra falha do factory real. Diferença reconhecida antes de propor alteração TLS; Maestro autorizou uma rodada corrigida com **o mesmo `app.core.http.external_client`** da aplicação.
- A aplicação já usa `httpx.AsyncClient(verify=ssl.create_default_context(), timeout=15.0)` e raízes do SO, implementado anteriormente em `7916989`. Nenhum patch TLS necessário: o contexto real funcionou.
- Comparação offline fora do sandbox: contexto SO com 82 certificados/78 CAs, contexto certifi com 121 certificados/121 CAs; ambos `verify_mode=CERT_REQUIRED` (2) e `check_hostname=true`. SSL_CERT_FILE/SSL_CERT_DIR ausentes; HTTP_PROXY/HTTPS_PROXY/ALL_PROXY ausentes no processo elevado. Não removidos proxies reais nem alterado ambiente global.
- `meta.degraded` da aplicação indica avisos de interpretação/seleção/fonte/termo, não indisponibilidade de todas as fontes. `meta.ai_used` indica seleção por IA, não apenas interpretação bem-sucedida. `meta.sources` descreve itens entregues e `meta.hint` é string de texto do servidor/erros genéricos; Frontend avisado por Maestri, sem chamadas externas duplicadas.

## Estado atual e evidências

### Rodada inicial — cliente diferente da aplicação

- 2026-10-02 **17:14:51 UTC**: Open Library `https://openlibrary.org/search.json`, query pública `The Hobbit`, lang=pt/limit=3/fields atuais; MusicBrainz `https://musicbrainz.org/ws/2/recording`, query pública literal `GoGo Penguin AND video:false`, limit=3/fmt=json.
- Ambas falharam antes de resposta HTTP: ConnectError → SSLCertVerificationError, verify_code **20** (cadeia/issuer não confiável no bundle usado). Nenhum payload normalizado nem fallback de recomendação executado. O contexto era HTTPX padrão/certifi, **não o contexto TLS real da API**.
- Groq não chamado pelo gate de fontes; cota RO **2→2/50**. Banco confirmou leitura 17:17:16 UTC, anterior à rodada corrigida. Não concluir chave inválida nem provider offline por essa falha.
- Evidência ignorada: `.impeccable/runtime/backend-online-probe-20261002.json`; script com mesmo nome e extensão `.py`.

### Rodada corrigida — fontes públicas reais e interpretação

- Autorizada especificamente pelo Maestro e executada **17:17:39 UTC** fora do sandbox, com `external_client()` real e TLS validado por raízes SO; mesmas queries/limit=3, uma requisição por fonte, sem retries. Sem alteração de código/configuração.
- **Open Library HTTP 200**, application/json, **três livros normalizados**, provider=open_library. Amostras reais:
  - “O Hobbit”, autores `J.R.R. Tolkien`, work `OL27482W`, UUID `8fb8e5cb-c79d-5dc6-bad4-c34d64115d04`, cover_url `https://covers.openlibrary.org/b/id/14849956-M.jpg?default=false`.
  - “The Hobbit”, autores Charles Dixon/Sean Deming/J.R.R. Tolkien, work `OL219602W`, UUID `f6c5a15e-858f-5fe4-8e4e-02fe732fbb5b`, cover_url `https://covers.openlibrary.org/b/id/8406766-M.jpg?default=false`.
- **MusicBrainz HTTP 200**, application/json, **três gravações normalizadas**, provider=musicbrainz. Amostras reais:
  - “HF”, GoGo Penguin, MBID `49ce19f1-f97e-4ea0-a679-4324d946623c`, UUID `fa5c09ff-f029-5f1a-86bd-e8f4714af0e2`, duração informada pela fonte **396.426 ms**.
  - “All Res (radio edit)”, GoGo Penguin, MBID `a5beb33c-372c-457f-b8ff-f924715772a0`, UUID `891af23e-75f4-5dd1-8d20-833a74108d02`, duração **257.026 ms**.
- **Uma interpretação Groq real HTTP 200**, query pública “Músicas calmas para estudar”, provider/modelo/chave/cota originais, resposta validada como Intent pelo cliente implementado. Cache miss, uma resposta do provedor, sem retry. Search terms públicos: calm study music/ambient/instrumental; vocals=optional/energy=any. Não recomenda títulos inventados: essa operação somente interpreta.
- Cota RO **2→3/50** no dia UTC 2026-10-02. Contagem inclui tentativa do provedor conforme OnlineStore; nenhum reset/ampliação. Cache Intent gravado pelo fluxo normal de Groq; catálogo de livros/músicas não atualizado pelo diagnóstico de normalização pura.
- Status/readiness da API existente permaneceram 200; nenhum restart. Evidência ignorada `.impeccable/runtime/backend-online-appclient-probe-20261002.json`, script `.py`.
- Comando corrigido executado de `api/` via execução elevada autorizada:

```powershell
.\.venv\Scripts\python.exe ../.impeccable/runtime/backend-online-appclient-probe-20261002.py
```

### Limites da rodada corrigida inicial

- Prova **transporte/fontes normalizadas/interpretação reais**, não seleção/ranking/re-roll/trilha reais da API. Queries públicas diretas não geraram resposta de `/recommendations/*`; portanto `meta.ai_used/degraded` de uma recomendação não foi medido. Flags de diagnóstico `ai_used=false/degraded=false` significam ausência de ranking/falha no probe, não são o `meta` da API. Groq Intent válido também não prova seleção por IA.
- cover_url real veio dos metadados, mas **imagem/status/dimensões externas não foram consultados** nesta rodada. HTTP200 da Search API não comprova HTTP200 da imagem.
- A diferença de CAs explica por que o probe certifi falhou e o factory SO funcionou, mas não identifica qual certificado específico participou da cadeia; certificados privados não foram exportados ou impressos.
- Nenhuma indicação de credencial/modelo inválido; sem necessidade de trocar LLM/key/model/limite. PostgreSQL/pgvector real e validade global das fontes continuam gates separados.
- Não repetir fakes/suítes gerais já aprovadas para apresentar como evidência online. Nenhum defeito reproduzível novo no código de integração demonstrado nesta fase.

### API real — MUSIC e re-roll, seleção local

- **17:23:23 UTC**, API 31444 novamente identificada antes do gate, no máximo dois POST `/api/v1/recommendations/music`, mesma query acentuada do artefato de interpretação e limit=3. Segundo POST permitido somente após itens/has_more do primeiro, usando IDs cumulativos/cursor reais. Orçamento máximo quatro novas tentativas Groq incluindo retries; efetivamente **duas**, uma por POST.
- Cache Intent exato `99bb96730c19eab4aebfc125bc85068670b7f9d8e35655ae1dd03382edbe3adf`, LIVE antes/depois, TTL **86.057.914→86.051.523 ms**. Não renovado manualmente; query extraída do artefato para identidade exata.
- Primeiro POST offset=0: **200**, ai_used=true, degraded=false, sources=[local], has_more=true/next_offset=15. Três itens: Ambre (`dc9ea2e3-11c8-5547-b5d2-8e4d99434a97`), An Ending (Ascent) (`b1162ac5-765d-54ac-8ecb-713b3389a341`), Avril 14th (`21f67d35-cc41-5bbe-aced-19cf08ca8482`). Uso **3→4/50**.
- Segundo POST offset=15, excluindo os três IDs: **200**, ai_used=true, degraded=false, sources=[local], has_more=true/next_offset=30. Clair de lune (`d5a22d81-5cbc-50e0-a4b0-810c70afe72c`), Comptine d'un autre été, l'après-midi (`fb7a3b7b-7041-5b29-92fc-662c31d14248`), Gymnopédie No. 1 (`a8c889bf-35a7-5486-a9e6-b9c3daac817b`). Uso **4→5/50**.
- Seis UUIDs únicos, sem repetição entre lotes, metadados locais has_vocals=false/energy=low; duração real não informada e não inventada. Hint identifica catálogo local. Prova seleção IA/cursor/exclusões reais nessa amostra, **não seleção entregue de músicas externas nem esgotamento**. Parada após dois lotes autorizados, mesmo com has_more=true.
- Evidência ignorada `.impeccable/runtime/backend-online-api-music-gate-20261002.json`; Banco confirmou uso 5 em leitura RO **17:24:49 UTC**, antes do gate seguinte.

### Capa externa real

- Uma GET autorizada da URL exata do Hobbit obtida na rodada corrigida, `https://covers.openlibrary.org/b/id/14849956-M.jpg?default=false`, pelo factory da aplicação/TLS validado.
- **HTTP 200**, image/jpeg, **25.626 bytes**, dimensões **180×285**, sem placeholder 1×1. Leitura por stream limitada a **1 MiB**; dimensões obtidas por header JPEG/PNG/GIF com limites, sem executar conteúdo. SHA-256 `6d6c30780580701256ce58f40e7e10976bc7fb65993f8c2d8773b26807c08f50`.
- Imagem ignorada `.impeccable/runtime/open-library-OL27482W-cover-14849956-20261002.jpg`; bytes da imagem não impressos na saída. Nenhuma busca adicional de livro/capa nesse gate.
- Maestro confirmou uma única GET adicional **no navegador** do frontend existente, demais APIs simuladas com metadados públicos e outras fontes bloqueadas: HTTP200/naturalWidth180/naturalHeight285, imagem visível, zero erros/requests inesperados/LLM. Evidências dele: `.impeccable/runtime/online-cover-browser-20261002.json` e `.impeccable/review/online-cover-hobbit-390-20261002.png`. Não repetido pelo Backend.

### API real — BOOK externo e Jazz sem escolhas

- **17:25:48 UTC**, mais uma descoberta BOOK e uma MUSIC autorizadas, limit=3, sem reroll/busca manual extra. Orçamento máximo oito novas tentativas internas combinado; primeiro com erro HTTP/consumo>4 cancelaria segundo. Efetivamente **quatro**, duas por POST.
- POST `/api/v1/recommendations/books`, query pública exata “Livros de fantasia e aventura em portugues”: **200**, ai_used=true/degraded=false, sources=[open_library], has_more=true/next_offset=15. Três livros reais em português:
  - A guerra da papoula, R. F. Kuang, `OL19351054W`, UUID `ced2a1be-b94e-5b9d-a599-eec2c2cb7308`.
  - O Olho do Mundo, Robert Jordan, `OL7924103W`, UUID `29600e01-6f07-58ef-aa88-5c92581bee76`.
  - O Caminho dos Reis, Brandon Sanderson, `OL15358691W`, UUID `cd534057-a9b1-53b2-8b8e-2f7184108c44`.
- Cota **5→7/50** para BOOK. Prova seleção externa BOOK real com IA nessa consulta; URLs de capa vieram da fonte mas essas três imagens não foram buscadas.
- POST `/api/v1/recommendations/music`, query pública exata “Jazz instrumental”: **200**, ai_used=true/degraded=false, **sources=[]/items=[]**, has_more=true/next_offset=15. Hint indica nenhum item compatível/ampliar filtros. Cota **7→9/50**. Não inferir fonte offline: query direta MusicBrainz já respondeu 200 e o replay offline abaixo confirmou candidatos.
- Nenhuma tentativa extra para perseguir resultado. Ao final, status/readiness locais 200; API 31444/configuração/banco preservados. Evidência `.impeccable/runtime/backend-online-discovery-gate-20261002.json`.

### Diagnóstico offline exclusivo de Jazz instrumental

- Autorizado pelo Maestro após o gate, sem conexão, reserva AI, gravação de catálogo/cache ou mudança de TTL. SQLite mode=ro/query_only; leituras permitidas somente por chaves derivadas dessa query pública e seus dados MusicBrainz. Qualquer cache ausente/expirado, chamada de rede/reserva/escrita abortaria o replay.
- Intent exato `bded185a063e28107a43b8b9627346f6567b14225e59bb9e2cf310c7b5c620f4`, LIVE: termo Jazz, vocals=optional/energy=any, um tema/zero temas excluídos. O parser textual reaplica instrumental e resolve filters.vocals=none.
- Cache público MusicBrainz `tag:jazz`, limit=15/offset=0, LIVE: **15 candidatos externos**, has_more=true. Nenhum termo vazio/sem retorno. Pipeline idêntico produziu **18 candidatos** (15 MusicBrainz + três locais), seleção até quatro; vocais/energia conhecidos somente nos três locais.
- Selection derivada do mesmo pipeline `622f23ef57d334cb08f14535b8bed05929f5f9df16c04fa6d15f3699679b4d86`, LIVE: **zero choices**. Replay reproduziu items=[]/ai_used=true/degraded=false/next_offset=15.
- Causa observável do vazio: a IA não retornou escolhas. **Não houve rejeição por filtros, score, índice/duplicação ou limite por criador**, pois nenhum item chegou a essa etapa. O motivo da omissão não existe no schema Selection e não pode ser determinado nesta evidência; metadados musicais sem vocais/energia podem ter influenciado a seleção, mas isso é hipótese, não causa comprovada nem bug demonstrado.
- Somente contagens/causas/campos públicos permitidos foram registrados, sem dump de cache/corpo upstream/prompt privado. **Zero rede/zero escrita/zero consumo adicional**. Artefato ignorado `.impeccable/runtime/backend-online-jazz-offline-funnel-20261002.json`; replay pelo código real com store restrito/read-only e transporte que aborta qualquer request, não um novo resultado fictício.

### Encerramento do gate

- Consumo da sessão coordenada: **2→3** interpretação, **3→5** dois MUSIC com re-roll, **5→9** BOOK + Jazz; **sete novas tentativas**, limite diário **50 inalterado**. Contagens observadas por leitura RO; nenhuma mudança de chave/modelo/provider/cota.
- Validação real pontual aprovada: transporte Open Library/MusicBrainz pelo factory real, interpretação/seleção Groq, descoberta externa BOOK, capa Open Library HTTP/dimensões/navegador e re-roll MUSIC com seleção local/IDs/cursor.
- **Ranking/seleção entregue de MUSIC externa não aprovado**: a query calma entregou apenas local e Jazz entregou vazio, com causa observável zero choices. Não afirmar qualidade global, esgotamento, re-roll externo, trilha online/duração completa ou PostgreSQL real a partir dessas amostras.
- Chamadas externas/LLM encerradas; sem nova query, restart, patch core ou suíte geral. Relatório exclusivo liberado ao Maestro para revisão/consolidação/commit; demais alterações presentes na árvore pertencem aos terminais coordenados.

## Próximos passos

- Maestro consolidar evidências e consumo final 9/50 nos documentos compartilhados e registrar somente este relatório como unidade documental Backend, sem incluir artefatos ignorados nem mudanças de outros agentes.
- Manter MUSIC externa como gate aberto. Em uma futura janela autorizada, definir avaliação/diagnóstico de cobertura e metadados/seleção para queries instrumentais antes de propor alteração; o replay atual não demonstra bug de filtro/ranking e não justifica relaxar filtros, trocar modelo/provider ou ampliar quota.
- Não realizar outras chamadas externas/LLM nesta entrega. Preservar API31444 e snapshots/cache existentes. BOOK/capa são resultados pontuais; PostgreSQL/pgvector e trilha online completos permanecem gates separados.
- Frontend registrou clareza de tentativa degradada vazia em commit `949f642`, build2.050 PASS informado pelo Maestro. Dados de seleção anterior e aviso da tentativa devem permanecer distintos, sem inferir que todas as fontes ficaram offline.
