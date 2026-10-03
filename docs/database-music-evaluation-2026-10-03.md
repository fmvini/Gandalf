# G1 offline — identidade e amostra comparável, 2026-10-03

## Escopo e resultado

Banco disponível para revisão **somente leitura** de app/modelos/store/contrato; reserva única deste documento. Base informada pelo Maestro: HEAD `df7891a`. Não executados avaliador, scripts, diagnósticos anteriores, DB, rede/API/LLM, Docker, runtime nem testes. Não produz resultado de amostra, aprovação de CLI ou fechamento G1.

Foram lidos contrato MusicProvider, TypedDict MusicItem/MusicSearchResult, normalizador MusicBrainz, OnlineStore, modelos e contexto G1/ADR-0012. Nenhum outro arquivo editado. **Desvio inicial registrado:** a consulta incluiu status/log Git em leitura somente, além do limite desta unidade; nenhuma mutação e nenhuma nova consulta Git após identificar o desvio. Não alterados docs compartilhados. Escopo e achados iniciais enviados ao Maestro via maestri ask.

Conclusão: snapshots permitem aferir **formato, coerência de identidade e disponibilidade de campos na amostra**. Não provam determinismo temporal, constraints/persistência, isolamento/TTL do cache, catálogo completo, verdade dos atributos ou qualidade de uma fonte. A documentação distingue o catálogo local por obra de recordings externos; não usar esses dois universos como se fossem a mesma unidade experimental.

### Coordenação aceita pelo Maestro

Maestro aceitou matriz **cases/providers** e **stage global**, distinguindo `provider_search` de `recommendation`; o avaliador não misturará essas fases. Estados missing/error/empty permanecem separados. `g1_approved` será **false** mesmo se todos os checks offline passarem: o resultado não certifica a escolha da fonte.

Maestro prepara plano comum de **12 casos/6 grupos**, ainda sem coleta. Isso é desenho de amostra futura, não12 casos avaliados, fonte alternativa medida ou cobertura comprovada. Coleta somente com budget explicitamente autorizado; **zero chamadas nesta unidade**. Achados de duplicatas/conflitos/proveniência foram encaminhados ao Backend pela conexão maestri.

## Achados do contrato que afetam o avaliador

- MusicItem requer id/title/artist/tags/duration_ms/has_vocals/energy/provider/external_id/links. Duração, vocais e energia admitem null; classification_source é opcional provider_tags/ai_estimate. Campos ausentes não são o mesmo que null válido.
- MusicSearchResult contém items/total/provider/has_more. Adapter.name, envelope.provider e item.provider devem ser consistentes, externos e diferentes de local. O snapshot pode não conter adapter.name; nesse caso sua igualdade com o adaptador é **não verificável**, não aprovada por inferência.
- MusicBrainz preserva UUID5 da URL canônica recording/MBID. Seu total é len(items normalizados daquela resposta), não total do catálogo remoto. has_more é indicação de continuação remota; itens de uma página podem ser descartados ao normalizar/filtrar.
- Store musical usa PK string36+JSON e upsert somente id. Provider/external_id não são colunas com constraints próprias. Cache usa chave composta entity_type/provider/query/result_limit, com modalidade/página na chave criada pelo adaptador; cache hit devolve o corpo normalizado. Nada disso está demonstrado por validar o JSON exportado.
- Snapshot de catálogo, busca reading com derivações por tags, recomendação após IA e catálogo local têm estágios/proveniências diferentes. Há preenchimento de unknown com provider_tags/ai_estimate; comparar fases distintas pode atribuir à fonte cobertura criada por regras/IA.
- classification_source é **do item**, não de cada atributo. Se apenas energia foi inferida enquanto vocais já eram conhecidos, ai_estimate não prova que ambos foram inferidos. Sem snapshot anterior ou proveniência por campo, não atribuir precisão/origem de cada atributo.

## Requisitos mínimos de comparabilidade

Manifesto ou registros associados devem declarar os campos abaixo. Se faltarem, reportar limitação/não comparável; não inventar defaults históricos nem importar configuração/runtime.

| Dimensão | Informação necessária |
|---|---|
| Caso e unidade | case_id fixo e unidade alvo: gravação, obra ou busca de descoberta. Mesma matriz de pedidos/estratos em todas as fontes; ausência de resposta/resultado continua representada. |
| Pedido | Consulta pública ou referência controlada; mesmos query/limit/by_tag/offset/reading/instrumental e filtros. IDs locais/contextos não contam como recordings externos. |
| Escopo de captura | Search ou lookup/enriquecimento; versão de normalização/adaptador, fase adapter_normalized/reading_tags/post_ai, instante/janela da captura e ordem das páginas. Não comparar lookup enriquecido com search simples sem estrato explícito. |
| Paginação e budget | Mesma política de páginas/limites/chamadas para a comparação, com páginas realmente presentes. Retorno vazio, parcial, erro e captura ausente são estados distintos. |
| Cache | Origem declarada fresh/cache/unknown e chave/tempo de captura quando disponíveis. JSON idêntico não prova cache hit; snapshot sem esse contexto não prova requisição de rede ou frescor. |
| Correspondência entre fontes | Para avaliação pareada por gravação, referência/mapeamento independente com evidência de mesma versão/gravação. Título+artista, UUID de fontes distintas ou mesma obra não bastam para ligar recordings. |
| Julgamento | Rótulos humanos por gravação/caso, evidência e protocolo separado se quiser medir relevância/voz/instrumento. Campos presentes são disponibilidade normalizada, não acurácia, qualidade auditiva ou direitos de uso. |

Buscas idênticas podem retornar gravações diferentes em cada fonte. Isso permite comparar retrieval e disponibilidade **nos resultados retornados**, mas não uma comparação pareada de cobertura sobre um corpus de gravações iguais sem mapeamento. Reportar macro por caso e estrato; não deixar uma consulta prolífica substituir os casos vazios/difíceis. Nenhum tamanho mínimo ou limiar de aprovação G1 foi estabelecido por Banco nesta revisão; Maestro define matriz/critério antes da coleta autorizada.

## Checks de identidade possíveis nos snapshots

| Check | Como observar offline | O que não prova |
|---|---|---|
| UUID canônico | id é string; parse UUID válido e `str(UUID(id)) == id`. Rejeitar representação uppercase/compacta/não-string, sem reescrever silenciosamente a entrada. | Registro real na fonte, estabilidade ou determinismo do gerador. UUID versão5 sozinho também não prova algoritmo/namespace usado. |
| Coerência de fonte | Provider não vazio; igualdade literal envelope/item e adapter declarado; nome compatível com varchar32. external_id é string útil segundo contrato da fonte. Separar local de externo. | Adaptador executado, fonte remota consultada, identidade/corpo autenticados ou isolamento físico do cache. |
| Um id → identidade | Agrupar UUID por `(provider,external_id)`. Mesmo id ligado a pares diferentes é conflito global de identidade dentro da amostra; não escolher um registro vencedor. | Que houve sobrescrita no banco, colisão matemática do UUID5 ou corrupção de dados existentes. |
| Uma identidade → id | Agrupar `(provider,external_id)` e contar UUIDs distintos. Mais de um é contradição à identidade estável assumida pelo port naquele escopo/versionamento. | Nondeterminismo temporal do código por si; snapshots podem misturar versões/aliases capturados. Declarar esse contexto, sem chamar duas strings de prova causal. |
| ID e metadados repetidos | Mesmo par/id com payload igual é repetição exata. Mesmo par/id com título/duração/atributos diferentes é reobservação/variação de metadados; comparar cada campo e fase. | Colisão de identidade quando provider/external_id continuam iguais; qual versão é verdadeira ou mais recente sem contexto. |
| Entre fontes | external_id igual em providers diferentes **não é conflito** se UUIDs separados. Título/artista iguais não são chave de dedup entre fontes. | Quantidade de gravações reais únicas na união; sem correspondência externa esse número é não verificável. |

Mapas devem cobrir o conjunto de snapshots auditado, incluindo repetições entre páginas/casos; contagens de cobertura depois são por fonte/caso. Preservar identificadores originais e posições para localizar erros. Não casefold/trim/coagir external_id ou provider para esconder contradições: aliases/canonicalização específicos exigem regra declarada da fonte.

Para MusicBrainz, comparar opcionalmente com UUID5 da URL/MBID documentados é um **check de consistência com uma regra conhecida**, se esse modo for declarado. Nem esse cálculo a partir do próprio snapshot verifica respostas raw, execução repetida, ID invariável ao renomear título ou validade da gravação. Para outras fontes sem regra conhecida, declarar namespace/determinismo não verificáveis, sem impor UUID5 MusicBrainz a todo adaptador.

## Contagens sem inflação de cobertura

Separar relatório de integridade de relatório de cobertura; não ocultar erro deduplicando antes de inspecionar os mapas. Recomendações de contadores:

- **Entrada:** snapshots/casos/páginas recebidos, estados vazios/parciais/erro/ausente e total de linhas. As mesmas páginas repetidas continuam sendo observações repetidas, não chamadas novas comprovadas.
- **Integridade:** linhas de contrato inválidas; UUIDs não canônicos; grupos id→pares conflitantes e par→IDs conflitantes, além de linhas envolvidas. Os grupos afetados ficam ambíguos; não fazem parte do denominador principal de identidades coerentes. O denominador reduzido e as exclusões devem aparecer, não transformar uma amostra ruim em sucesso.
- **Identidade:** linhas válidas, UUIDs distintos, pares(provider,external_id) distintos e identidades únicas coerentes por fonte/caso. Repetições exatas adicionais e repetições de identidade são métricas separadas/sobrepostas; não somar como categorias disjuntas. Igualdade exata pode ignorar ordem de chaves JSON/whitespace, mas não apagar diferenças de valores/listas/proveniência.
- **Por atributo:** para identidades coerentes na fase comparável, contar known/unknown/invalid ou missing. Cobertura conhecida = known/denominador declarado; denominador zero resulta null/não aplicável, não100%. has_vocals=false é conhecido; null não é instrumental. duration bool/zero/negativo/string não vira duração válida; para leitura contar elegíveis90–600s separadamente de duração conhecida geral. Energy aceita low/medium/high ou null; tags vazio não é cobertura de tags úteis.
- **Proveniência:** contar itens com provider_tags/ai_estimate/sem marca e fases normalizadas separadamente. Isso é contagem de rótulos, não origem comprovada por atributo. Não contar estimativas como disponibilidade direta da fonte ou assumir sem marca = medição acústica.
- **Reobservações:** metadados discordantes sob identidade válida devem aparecer por campo. Não fazer união otimista dos atributos de cache/páginas/fases para construir um item artificial completo. Definir previamente qual observação pertence à amostra principal; disponibilidade “vista ao menos uma vez” pode ser métrica adicional identificada, não substituto da cobertura no snapshot comparável.

Não somar total das páginas para estimar catálogo: MusicBrainz total é tamanho da página normalizada, com possíveis duplicatas entre consultas/páginas. has_more=false indica fim daquele pedido na captura, não exaustão da fonte. Um limite solicitado de20 não implica20 respostas nem20 gravações únicas; len(items) não mede chamadas remotas. Contagens globais de resultados únicos devem vir da dedup de identidades coerentes, com cobertura por caso também preservada.

## Exemplos conceituais, não executados

| Entrada hipotética | Relato correto |
|---|---|
| Uma gravação repetida em cinco páginas, todas idênticas | Cinco linhas, uma identidade única, quatro repetições adicionais; uma unidade no denominador de disponibilidade. Nenhuma prova de cinco chamadas novas. |
| Mesmo UUID em fontes A/B com external_id diferente | Um grupo de identidade contraditório; não apagar uma linha por last-write-wins nem tratar como gravação compartilhada entre fontes. |
| A/x e B/x, UUIDs distintos | Duas identidades de fonte coerentes. Unicidade de gravação real entre ambas permanece desconhecida. |
| Mesmo A/x/id, vocals=null na fonte e false após IA | Fases distintas; não duas gravações e não evidência de vocais conhecidos na fonte. Sem raw/pós-IA pareados, classificação por campo fica não verificável. |
| Fonte A vazia num caso e B com20 resultados | Manter o caso vazio no retrieval/macro por caso; não omitir A por denominador de metadados zero. |

## Claims permitidos e gates pendentes

CLI pode concluir que o arquivo foi lido, o contrato/formato passou ou falhou, mapas de identidade são coerentes **na entrada fornecida** e campos estão disponíveis nos denominadores declarados. Deve distinguir conformidade do snapshot de amostra comparável incompleta e de G1 não avaliado; zero conflitos não equivale a prova global de ausência de colisão.

Prova adicional necessária: determinismo exige execução repetida do adaptador/normalizador com entradas controladas e versões conhecidas; constraints/isolation/TTL/persistência exigem gates de DB/código específicos; comparação real de fontes exige amostra/autorização/termos/operação; acurácia instrumental/voz/energia requer evidência por gravação e revisão humana. Nenhuma dessas provas foi executada nesta unidade; não repetido o diagnóstico de2026-10-02.

Maestro/Backend decidem manifesto/checks/política de duplicatas/conflitos e CLI em suas reservas. Banco não propõe schema/migration nem alterou app/store/testes/arquivos de avaliação. **Documento entregue e freeze/liberado**, sem novas leituras/edições/execuções após envio sem solicitação; Maestro mantém Git/docs compartilhados.
