# ADR-0012 — Seleção do provedor musical

**Estado:** Em avaliação na Fase 2; MusicBrainz integrado experimentalmente, sem escolha definitiva para G1.

**Protocolo de avaliação em 2026-10-03:** [plano offline G1](../music-provider-g1-evaluation.md) e manifesto v1 definem12 casos/seis grupos comuns, etapas de captura e revisão independente. Nenhuma coleta nova foi executada. O avaliador de snapshots foi entregue com84 testes focados, Ruff/formatação e entrypoints CLI aprovados; conformidade de JSON nunca constitui aprovação G1. MusicProvider inicial e injeção foram concluídos nos commits e5b4d75/753a9c1; atributos conhecidos são preservados e derivações tags/IA identificadas, com limitação de proveniência por item. A licença Data License foi acessada nesta revisão, superando o bloqueio429 anterior; campos suplementares/termos dos candidatos e uso comercial continuam sujeitos à análise específica descrita no plano. Não há novo adaptador Last.fm ou nova fonte habilitada.

**Reconciliação em 2026-09-29:** `api/app/providers/musicbrainz.py` implementa busca textual/por tags, normalização, cache persistente e catálogo por ID. Testes em `api/tests/test_online.py` usam transporte simulado. Isso não fecha a avaliação comparativa, licenças ou cobertura real. Energia/vocais são estimativas da IA identificadas na resposta, não metadados da fonte. Evidências e links datados abaixo são históricos; não houve nova consulta externa nesta revisão. MusicBrainz está em uso experimental; a escolha final permanece pendente.

## Contexto

O fluxo de descoberta depende de metadados suficientes para buscas, embeddings e fatores de contexto como atmosfera, energia e vocais. O [roadmap](../12-development-roadmap.md) define a escolha do provedor musical como portão G1 antes de avançar no motor de recomendação. O [ADR-0004](0004-external-data-providers.md) já define o contrato de integração, mas não escolhe a fonte.

## Decisão a tomar

Avaliar MusicBrainz, Last.fm e outras fontes candidatas em dados e condições reais; escolher fonte primária e, se necessário, uma fonte complementar ou fallback. O resultado deve registrar o que cada serviço fornece diretamente, o que será inferido por regras ou enriquecimento ancorado, limites de uso e obrigação de atribuição. Spotify não é pressuposto como fonte do MVP: a integração de conta/exportação é pós-MVP.

## Critérios de comparação

| Critério | Evidência necessária |
|---|---|
| Disponibilidade e estabilidade | Testes de busca/ID, falhas e comportamento em indisponibilidade |
| Cobertura e qualidade | Amostra de faixas de estilos distintos; título, artista, tags, descrições, duração, links e identificadores |
| Adequação à recomendação | Capacidade de obter atributos para humor/energia/vocais, diretamente ou com proveniência e confiança |
| Limites e custo | Rate limits, quotas, chaves, cache permitido e custo no volume estimado do MVP |
| Termos de uso | Licença de metadados/imagens, atribuição, retenção e uso em produto público |
| Integração | Busca por texto/referência/tags, deduplicação, latência e fallback |

## Alternativas consideradas

- **Uma fonte só:** operação simples; pode deixar lacunas de tags ou cobertura.
- **Fontes complementares:** metadados mais ricos; aumenta deduplicação, latência e manutenção.
- **Catálogo local sem consulta externa:** rápido após aquecimento; falha no início frio e não sustenta a garantia de cobertura.

## Evidência inicial — 2026-09-28

| Fonte | Busca e campos | Limites e acesso | Lacunas para G1 |
|---|---|---|---|
| MusicBrainz | A [busca de recordings](https://musicbrainz.org/doc/MusicBrainz_API/Search) devolve MBID, título, crédito de artista, duração quando cadastrada e releases. O [lookup](https://musicbrainz.org/doc/MusicBrainz_API) pode pedir tags e gêneros em uma chamada adicional. | [User-Agent identificável e até uma chamada por segundo](https://musicbrainz.org/doc/MusicBrainz_API/Rate_Limiting); o serviço público é gratuito para uso não comercial. [Dados centrais e suplementares têm licenças diferentes](https://musicbrainz.org/doc/About/Data_License). | Busca não garante duração, tags ou gêneros; não traz descrições, energia ou vocais diretamente. O enriquecimento por lookup acrescenta latência e exige medir cobertura. |
| Last.fm | [track.search](https://www.last.fm/api/show/track.search) encontra título e artista; [track.getInfo](https://www.last.fm/api/show/track.getInfo) pode trazer duração, tags e texto wiki. | Exige chave de API. [Limites, cache e uso comercial](https://www.last.fm/api/tos) dependem dos termos e podem exigir contato prévio. | Sem chave configurada, a cobertura e a disponibilidade reais não foram medidas; busca simples sozinha não fornece os atributos necessários. |

Foram feitas quatro consultas exploratórias ao MusicBrainz nesta data, espaçadas em pelo menos um segundo: busca por “No Surprises”/Radiohead, “Clair de Lune”/Debussy e “Take Five”/Dave Brubeck (um resultado solicitado por busca), mais lookup com `inc=tags+genres` de um recording de “No Surprises”. As três buscas retornaram identificador, título e artista. A duração faltou no primeiro resultado de “No Surprises”; `tags` apareceram apenas no primeiro resultado de “Take Five”; o lookup de outro recording de “No Surprises” retornou listas vazias de tags e gêneros. Essa amostra pequena confirma o formato e expõe lacunas, mas não mede cobertura nem latência de modo suficiente para escolher a fonte.

**Próxima avaliação:** obter uma chave Last.fm de desenvolvimento e testar a mesma amostra com `track.getInfo`; medir cobertura de tags/gêneros, duração e links em uma amostra maior, além de latência e respostas de falha. Verificar a licença dos campos efetivamente usados e a viabilidade de uso público antes de fechar G1. Música gerada por IA ou atributos inferidos não devem ser apresentados como metadados da fonte.

## Consequências e fechamento

Até a avaliação, os nomes citados nos documentos são candidatos, não escolhas finais. Para fechar este ADR, anexar uma matriz comparativa com exemplos e resultados de testes de contrato, declarar a fonte escolhida e fallback, e atualizar configuração, documentação e critérios de G1. Se nenhum candidato atender, revisar a estratégia de dados antes de prometer qualidade no MVP.

**Referências:** [Escopo §30](../00-Escopo-Detalhado.md#30-fontes-de-dados), [Development Roadmap §4](../12-development-roadmap.md#4-portões-de-qualidade-quality-gates), [Recommendation Engine Specification](../07-recommendation-engine-specification.md).
