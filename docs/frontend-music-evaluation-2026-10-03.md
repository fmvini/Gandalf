# G1 offline — parecer frontend, 2026-10-03

## Estado e escopo

Parecer concluído e documento exclusivo congelado/liberado ao Maestro. Referência de retomada informada: HEAD `df7891a`; não verificada por comando Git nesta unidade. Revisão estática de helpers, fixtures e contratos atuais, sem executar produto, testes, browser, build, rede, API, LLM ou processos. Nenhuma alteração além deste documento. Maestro reserva manifesto/documentos compartilhados/serialização; Backend reserva avaliador offline.

**G1 permanece não aprovado.** O CLI offline deve registrar `g1_approved: false` sempre, mesmo quando validação/fixture/checks passam. `evidence_kind: fixture` e `evidence_kind: recorded` precisam permanecer explícitos; recorded identifica origem de uma captura, não aprovação automática dos fatos, do áudio ou de G1.

## Proveniência e atributos

| Categoria para a matriz | O que significa | O que não pode concluir |
| --- | --- | --- |
| known | Valor não nulo recebido do catálogo/adaptador e preservado; registrar sua origem/evidência quando disponível | Não equivale a medição acústica, verdade independente ou cobertura universal |
| provider_tags | Derivação de tags da fonte em atributo desconhecido; preservar tags/etapa que sustentam o preenchimento | Tag instrumental não certifica ausência de voz; energia por atmosfera não é medição |
| ai_estimate | Atributo originalmente desconhecido preenchido com escolha válida por IA; registrar antes/depois | Não valida precisão, confiança calibrada ou concordância com áudio; ai_used sozinho não classifica atributos |
| unknown | Null/ausência ou dado sem suporte válido; energia desconhecida continua null no contrato normalizado | Nunca false/instrumental, energia baixa, duração zero ou sucesso implícito de filtros |

`classification_source` atual é **por item, não por atributo** (`frontend/src/lib/api.ts:4–5`, `frontend/src/lib/format.ts:7–13`). A UI mostra esse marcador ao lado de vocais/energia, mas ele não identifica qual campo foi derivado. `api/app/services/online_recommendations.py:251–266` preserva known e marca o item ai_estimate se pelo menos um unknown for preenchido. Reading só deriva unknown por tags (`api/app/services/online_soundtrack.py:134–147`).

Exemplo: vocais=false/energia=null antes; vocais=false/energia=low depois, com ai_estimate. Só energia foi estimada; não contar vocais como estimativa nem os dois campos como metadados objetivos da fonte. Se os snapshots/etapas não permitirem determinar a origem por atributo, registrar **proveniência por atributo indisponível**, sem inventar atribuição a partir do marcador do item. Nenhum redesenho ou mudança de payload proposto aqui.

A matriz deve separar, quando a evidência permitir: valor recebido/normalizado, valor final, origem/evidência por atributo, preservação de known e revisão independente. Known, derivado por tags, estimado e unknown devem ter contagens próprias; não fundir a cobertura normalizada/enriquecida com a cobertura direta da fonte. Para instrumental estrito, contar unknown no denominador e separar False recebido/derivado/estimado de False confirmado por revisão; não aprovar qualidade por mero booleano da fixture.

## Duração e identidade

- `duration(ms?: number | null)` retorna vazio para ausência, não inventa minutos (`frontend/src/lib/format.ts:17–22`). `MusicItem.duration_ms` aceita null (`frontend/src/lib/api.ts:3`). Zero não deve substituir unknown no manifesto, embora o helper também produza vazio para valor falsy.
- Comparar duração numérica em ms da **mesma gravação/versão**, não a string arredondada da UI. Título/artista iguais não bastam para misturar versões live, remaster, remix ou gravações com/sem voz; registrar provider/external_id/UUID e URL canônica.
- Separar presença de duração, validade do valor e concordância com evidência independente. Número preenchido de fonte/fixture não confirma duração do áudio real. Reading online exige duração inteira90–600s da fonte correspondente; o total deve ser soma de faixas aceitas, sem completar com duração inventada.
- Totais locais/salvos podem conter estimativas explicitadas por duration_estimated. Isso não preenche duration_ms individual nem conta como cobertura de duração real externa (`frontend/src/pages/ReadWithMusic.tsx:108`, `frontend/src/pages/Playlist.tsx:60–61`, `docs/music-provider-contract.md`). Registrar duração-alvo, total/shortfall, flags e sucesso/insuficiência separadamente; formatação correta não comprova meta musical de uma seleção real.

## Fonte de metadados versus destino de áudio

- `provider` identifica a origem do catálogo; provider ausente não vira local/MusicBrainz (`frontend/src/lib/format.ts:4–6`). `meta.sources` agregado não atribui fonte a cada faixa.
- `links.provider` é página canônica da fonte. `links.spotify`/`links.youtube` são destinos fornecidos, não garantia de streaming, playback autorizado ou identidade exata do áudio. `links.search`/fallback são **buscas**, não correspondência encontrada/verificada.
- `musicDestination` conserva ordem spotify → youtube → provider → search → fallback. Search recebe YouTube apenas por hostname youtube.com/subdomínio; outros recebem Buscar faixa, sem visitar URL (`frontend/src/lib/api.ts:61–77`). Reconhecer hostname não prova resposta200, acessibilidade regional, gravação correta, direito de uso ou disponibilidade de áudio.
- Na matriz, distinguir existência/normalização do link, identidade canônica, tipo de destino e eventual verificação independente. Nesta rodada offline, não executar links ou escuta; marcar essas verificações pendentes/não observadas, não aprovadas.

## O que as fixtures atuais sustentam

Inspeção de `frontend/tests/music-metadata.mjs:17–32` e suas asserções finais:14 itens sintéticos, provider alternativo/local/MusicBrainz, known/provider_tags/ai_estimate/unknown, null/ausência, duração null versus180000ms, links.provider/search e hostname enganoso. Duas queries10+4, rótulos/ordem/snapshot, precedência, texto acessível, fonte/contraste/overflow e guard de rede cobrem **consumo/apresentação do contrato**.

Os PASS/browser/build/capturas anteriores pertencem à unidade commitada753a9c1 e estão registrados no relatório de 2026-10-02/log; não houve novo gate nesta revisão. A fixture atribui diretamente valores e respostas. Seu sucesso não transforma essa atribuição em evidência semântica ou estatística de provider real.

Fixtures **não certificam**:

- Disponibilidade externa, latência/falhas, cobertura representativa por gênero/gravação/atributo, precisão vocal/energética, relevância/ranking ou qualidade auditiva.
- Origem factual dos metadados, namespace/cache/persistência de um adaptador real, identidade exata de áudio/link, playback/streaming ou duração real de versões alternativas.
- Confiança da IA, comparação causal entre modelos/fontes, revisão humana, instrumental estrito confirmado ou objetivo de duração em catálogo real.
- Licenças/atribuição por campo, retenção/comercialização, quotas ou rate limit por IP entre processos, operação distribuída e fechamento G1.

`evidence_kind: recorded` offline também não cobre essas lacunas automaticamente: a captura deve ter origem/gravação/etapa/data/artefato identificáveis, e a avaliação deve distinguir fatos observados de inferência, validação estrutural e julgamento humano pendente. Ausência de campo é um resultado a registrar, não autorização para deduzir instrumental.

## Handoff

Manifesto e relatório do avaliador devem manter denominadores e evidência por categoria/atributo visíveis, separar conformidade de qualidade e emitir `g1_approved: false`. Parecer compatível com ADR-0012 e `docs/music-provider-contract.md`; não sugere fonte vencedora nem novo gate UI. Documento liberado ao Maestro para consolidação e commit local; nenhuma edição de produto, contrato público ou arquivo compartilhado autorizada nesta reserva.
