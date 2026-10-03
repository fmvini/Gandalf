# Avaliação G1 de MusicProvider — protocolo offline v1

Estado em 2026-10-03: preparação da avaliação, sem coleta nova ou seleção definitiva. O avaliador mede snapshots normalizados declarados; a decisão G1 continua humana e depende também de termos, cobertura e adequação para embeddings. O [contrato inicial](music-provider-contract.md) está implementado; o [ADR-0012](adr/0012-music-provider-selection.md) permanece em avaliação.

## Entrega validada

CLI e84 testes novos concluídos pelo Backend:84 PASS em0,30s, Ruff e formatação dos dois arquivos PASS. Revisão Maestro incorporou auditoria de identidade antes do descarte de metadados inválidos; conflitos continuam visíveis e excluídos dos denominadores elegíveis, sem vencedor arbitrário. Repetições exatas e variantes têm contadores próprios. Known/null/mixed, taxas com denominador zero=null e proveniência por item permanecem explícitos.

Maestro executou os entrypoints documentados normalmente, sem aplicação/rede: fixture exit0 (6 pares esperados/5 observados/1 erro/1 vazio/3 não vazios/1 ausente/3 linhas), template exit0 (24 ausentes/zero observações), item inválido exit1 e stdin inválido exit2/JSON genérico sem traceback. g1_approved=false em todos. Resultados agregados ignorados em `.impeccable/runtime/music-provider-eval-{fixture,template,invalid_item}.json`; nenhuma amostra real coletada. Não houve repetição da suíte geral/auth, browser/build, runtime, DB ou LLM.

Relatórios: [Backend](backend-music-evaluation-2026-10-03.md), [Banco](database-music-evaluation-2026-10-03.md), [Frontend](frontend-music-evaluation-2026-10-03.md). Banco/Frontend fizeram somente revisão estática de suas reservas; seus pareceres não são testes adicionais ou aprovação do CLI.

## Amostra comum e coleta proposta

[Plano versionado](evaluation/music-provider-g1-plan-v1.json):12 casos, seis grupos, duas modalidades por grupo (referência e tag). Piano, jazz, rock, música eletrônica, brasileira e repertório vocal são estratos exploratórios, não ground truth de gênero/instrumentação. Título/compositor ou artista identifica uma intenção; não garante a mesma gravação entre catálogos. Revisão deve conferir intérprete, versão, duração e identidade externa de cada resultado, sem deduplicar fontes por título/artista.

Todos os candidatos recebem o mesmo case_id/pedido, limit10, offset0, reading=false e instrumental=false. A fase inicial é provider_search, antes de interpretação/classificação pelo serviço de recomendação. Se uma fonte não representa uma operação, registrar erro/não suportado no diário, sem trocar silenciosamente o pedido ou excluir o caso. Um novo adaptador Last.fm ainda não existe: constar como candidato não habilita sua integração ou coleta.

**Coleta não autorizada nem executada por este plano.** Limite proposto para aprovação futura:24 chamadas HTTP (12 por candidato), sem retries, enriquecimento, paginação extra, imagens/áudio ou LLM. Autenticação/configuração legítima e termos devem estar resolvidos antes dessa aprovação. Chamadas de busca e lookup contam separadamente; uma resposta de cache não conta como chamada de rede. Se search sozinho não preencher metadados suficientes, preparar outra fase e orçamento de enriquecimento, sem misturar seus resultados com a busca inicial.

O [template de snapshots](evaluation/music-provider-g1-snapshot-template.json) contém zero observações e24 pares esperados. evidence_kind=recorded indica o formato destinado à futura coleta; arquivo vazio não contém evidência gravada. O [exemplo fixture](evaluation/music-provider-fixture-v1.json) é totalmente sintético, com providers fictícios, desconhecidos, tags/estimativa, erro, vazio e par ausente. Não representa a cobertura do MusicBrainz ou Last.fm.

## Formato e interpretação do avaliador

`api/scripts/music_provider_eval.py` recebe arquivo JSON local ou stdin; não importa a aplicação, abre engine, consulta ambiente, cache ou rede. schema_version1, evidence_kind fixture/recorded, stage provider_search/recommendation, cases(id/group), providers e observations(case_id/provider/outcome/result). Dados livres como queries, prompts, chaves, headers e respostas upstream não pertencem à entrada. IDs públicos opacos identificam o diário separado de coleta; não incluir informação de conta ou credenciais.

```powershell
cd api
.venv/Scripts/python.exe scripts/music_provider_eval.py ../docs/evaluation/music-provider-fixture-v1.json
.venv/Scripts/python.exe scripts/music_provider_eval.py ../docs/evaluation/music-provider-g1-snapshot-template.json
```

stdout é JSON agregado; exit0 significa entrada sem divergência detectada, não provedor disponível ou G1 aprovado. Exit1 indica violações do contrato/identidade; exit2 indica entrada inválida com erro genérico. g1_approved permanece false e g1_status NOT_EVALUATED para fixture e recorded. O CLI não verifica autenticidade da declaração recorded nem substitui o diário/arquivos originais sanitizados e hashes.

| Dimensão | O que registrar e como interpretar |
|---|---|
| Disponibilidade | Pares esperados, observados e ausentes; erro, sucesso vazio e sucesso com itens separados. Ausente não significa erro/vazio. |
| Cobertura | Linhas e identidades únicas por provider/grupo, duplicatas e conflitos. Não somar total de páginas como tamanho do catálogo; total>=len(items) e has_more são declarações da fonte. |
| Campos | Duração/vocais/energia conhecidos e null, tags presentes e proveniência ausente/provider_tags/ai_estimate. Conhecido sem proveniência não significa medido; tags não equivalem automaticamente a gêneros, descrição ou instrumento. |
| Identidade | UUID canônico e mapas UUID↔(provider,external_id), coerência envelope/item/fonte. Repetição entre pedidos é normal; duplicação dentro de um resultado e identidades contraditórias exigem investigação. Snapshot não prova namespace/determinismo temporal/constraints. |
| Leitura | Duração inteira conhecida90–600s é condição parcial de elegibilidade. Não comprova instrumental, meta total, disponibilidade de áudio ou afinidade com livro. |
| Proveniência | classification_source é por item, não por atributo. Comparar snapshot original/final e registrar evidência de vocais/energia individualmente; não atribuir ambos à IA/tags por um único label. |
| Links | Destino HTTP(S) válido sintaticamente não comprova áudio/licença/gravação correta. Fonte de metadados, destino de busca e reprodução são papéis distintos. |
| Não medido | Latência, cache/rede, qualidade auditiva, descrição/gêneros ausentes do port, utilidade de embeddings, estabilidade entre execuções e termos não são calculados automaticamente. |

Não há percentuais mínimos novos que fechem G1 nesta unidade. Estabelecer critérios de aceitação antes da coleta, por caso/grupo e atributo, em vez de ajustar o corte depois dos resultados. Amostra12 exploratória não substitui conjunto reservado nem os golden sets locais existentes.

## Diário e revisão humana

Para cada par, conservar fora de Git o registro sanitizado: case_id, pedido/flags exatos do plano, fonte/versão do adaptador, horário UTC, outcome, status/código público de falha, duração da chamada, cache_status=network/cache/unknown, quantidade de chamadas e hash do snapshot. Não gravar tokens, API keys, headers, conta ou dados pessoais. Distinguir resultado da busca, normalização e pós-IA; variantes/enriquecimento recebem outra rodada com stage consistente.

A ficha por gravação deve ter provider/external_id/UUID e fonte verificável, correspondência com a referência, variante/intérprete, vocal/energia original e final, evidência por atributo, julgamento independente e motivo. Usar unknown quando não houver evidência. A indicação instrumental de uma tag não é confirmação auditiva. Divergência entre revisores permanece visível; excluir item errado não apaga a falha do caso. Registrar também descrições/gêneros efetivamente fornecidos e permissão de uso para o futuro embedding; o port atual não carrega esses campos separados.

## Termos consultados em 2026-10-03

MusicBrainz separa dados centrais CC0 de suplementares CC BY-NC-SA3.0; tags, associações de gênero e anotações estão no segundo grupo segundo a [página Database](https://musicbrainz.org/doc/MusicBrainz_Database). A [página Data License](https://musicbrainz.org/doc/About/Data_License) agora foi acessada, superando o HTTP429 histórico. Isso exige mapear campos/derivações e finalidade de uso; não autoriza automaticamente publicação comercial ou redistribuição do payload inteiro. Cover Art Archive é fonte separada. O [rate limit](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting) público considera IP, em média1req/s, além de controles da aplicação/carga; User-Agent deve identificar contato. Coleta simultânea à API existente deve coordenar o mesmo egress, mesmo usando outro processo.

Last.fm [track.getInfo](https://www.last.fm/api/show/track.getInfo) exige API key e documenta duração, tags e wiki. O exemplo de resposta não garante cobertura desses campos. Os [termos oficiais](https://www.last.fm/api/tos), §§2.7/3/4.3/4.4, estabelecem atribuição/links e aprovação de páginas públicas, condições comerciais, limite de dados armazenados100MB e cache conforme headers; limites de API são definidos pelo serviço. A introdução pede contato prévio para uso comercial ou pesquisa/acadêmico. Não criar chave, iniciar coleta ou presumir permissão para embedding/publicação nesta etapa. Revisão documental identifica requisitos; aprovação específica e adequação ao produto continuam pendentes.

Nenhuma busca de recordings/faixas, consulta à API8000/PG5432, download de mídia ou chamada LLM foi executada para redigir esta revisão. As consultas web foram somente a documentação pública oficial; não alteram termos nem configuração do produto.

## Próxima prova

Depois dos gates offline: aprovar escopo/orçamento de coleta, resolver acesso/termos do candidato e definir critérios prévios de aceitação. Executar casos comuns em modo comparável, anexar relatório recorded e diário, realizar revisão independente e atualizar ADR-0012 com decisão/fallback/limitações. Até então MusicBrainz segue experimental e G1 aberto.
