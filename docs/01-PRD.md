# Product Requirements Document (PRD)

**Projeto:** {{PROJECT_NAME}} — Plataforma Inteligente de Descoberta de Músicas e Livros
**Versão:** 1.0
**Status:** Draft
**Tipo de projeto:** Portfólio profissional (full-stack + IA)

---

## 1. Resumo Executivo

{{PROJECT_NAME}} é uma plataforma web que permite ao usuário descobrir **músicas** e **livros** descrevendo, em linguagem natural, o que deseja ouvir ou ler. Diferente de sistemas baseados em filtros tradicionais (gênero, artista, título), a plataforma interpreta **intenções subjetivas** ("algo triste, mas reconfortante") e as converte em recomendações reais, ranqueadas por um mecanismo próprio.

A plataforma oferece três funcionalidades centrais:

1. **Discover Music** — descoberta de músicas por linguagem natural ou referência.
2. **Find My Next Book** — descoberta de livros por linguagem natural ou histórico de leitura.
3. **Read With Music** — recomendação de músicas/playlists que combinem com um livro e um contexto de leitura.

> **Princípio orientador:** a IA interpreta; as fontes externas fornecem conteúdo real; o Recommendation Engine decide; o perfil do usuário personaliza; o LLM explica quando necessário. A plataforma **não** é uma interface para um chatbot.

---

## 2. Problema

| # | Problema | Consequência |
|---|----------|--------------|
| P1 | Plataformas de música e livros dependem de filtros rígidos (gênero, artista, categoria). | O usuário não consegue expressar gosto subjetivo ou atmosfera. |
| P2 | Escolher o próximo livro é uma tarefa custosa e frustrante. | Paralisia de decisão; abandono da leitura. |
| P3 | Não há ferramenta que conecte **o que se lê** com **o que se ouve**. | Trilhas sonoras de leitura são montadas manualmente, sem critério. |
| P4 | Chatbots genéricos recomendam conteúdos inexistentes (hallucination). | Perda de confiança na recomendação. |
| P5 | Recomendadores comuns aprendem lentamente e de forma opaca. | Usuário não entende nem controla a personalização. |

---

## 3. Solução Proposta

Um pipeline de recomendação em que:

1. um **Intent Parser** (LLM com structured output) transforma o pedido em critérios estruturados;
2. o **backend busca candidatos reais** em provedores externos (Open Library, MusicBrainz etc.);
3. **embeddings** calculam similaridade semântica;
4. um **algoritmo de ranking próprio** combina similaridade semântica, preferências do usuário, similaridade com referências, contexto e popularidade;
5. o **LLM explica** o resultado apenas sob demanda ("Por que isso foi recomendado?").

---

## 4. Objetivos

### 4.1 Objetivos de Produto

- **O1.** Compreender preferências subjetivas em linguagem natural e convertê-las em recomendações úteis.
- **O2.** Garantir que 100% das recomendações sejam de conteúdos **reais** (existentes nos provedores).
- **O3.** Aprender progressivamente com feedback do usuário, sem treinar modelo próprio.
- **O4.** Oferecer a funcionalidade diferencial *Read With Music*.

### 4.2 Objetivos de Portfólio

- **O5.** Demonstrar Python, FastAPI, PostgreSQL, pgvector, React, LLMs, embeddings e sistemas de recomendação.
- **O6.** Demonstrar arquitetura modular, testes automatizados, documentação profissional e deploy público.
- **O7.** Permitir explicar em entrevista, com clareza, a arquitetura de recomendação (ver seção 12).

### 4.3 Não-Objetivos (MVP)

- Treinar modelo de ML próprio.
- Recomendação colaborativa.
- Reprodução de áudio ou armazenamento de arquivos de áudio.
- Criação automática de playlists no Spotify.
- Aplicativo mobile nativo.
- Funcionalidades sociais.
- Microservices.
- Base própria com milhões de músicas.

---

## 5. Público-Alvo e Personas

### Persona 1 — Marina, a leitora indecisa
- **Perfil:** 28 anos, lê 1–2 livros por mês, gosta de fantasia e ficção científica.
- **Dor:** passa dias escolhendo o próximo livro; filtros de gênero são amplos demais.
- **Necessidade:** "Quero fantasia medieval séria, sem romance como foco."

### Persona 2 — Rafael, o explorador musical
- **Perfil:** 24 anos, ouve música o dia todo, curte descobrir artistas.
- **Dor:** algoritmos de streaming repetem sempre os mesmos artistas.
- **Necessidade:** "Algo parecido com *Fake Plastic Trees*, mas mais pesado."

### Persona 3 — Camila, a leitora imersiva
- **Perfil:** 31 anos, lê à noite e gosta de ambientação sonora.
- **Dor:** playlists "para ler" são genéricas e não combinam com o livro.
- **Necessidade:** "Estou lendo *O Hobbit*; quero músicas que pareçam viagem pela Terra Média."

---

## 6. Diferencial Competitivo

| Característica | Streaming/Livraria tradicional | Chatbot genérico | **{{PROJECT_NAME}}** |
|---|:---:|:---:|:---:|
| Busca por atmosfera/contexto em linguagem natural | ✗ | ✓ | ✓ |
| Conteúdo garantidamente real | ✓ | ✗ | ✓ |
| Ranking transparente e controlável | ✗ | ✗ | ✓ |
| Aprendizado por feedback explícito | Parcial | ✗ | ✓ |
| Conecta livros e músicas (*Read With Music*) | ✗ | Parcial | ✓ |
| Explicação sob demanda baseada em fatores reais | ✗ | ✗ | ✓ |

---

## 7. Escopo Funcional

### 7.1 Módulos

| ID | Módulo | Descrição | MVP |
|----|--------|-----------|:---:|
| M1 | Discover Music | Busca musical por linguagem natural e/ou música de referência | ✓ |
| M2 | Find My Next Book | Busca de livros por linguagem natural e/ou livros de referência | ✓ |
| M3 | Read With Music | Músicas adequadas a um livro + contexto + modo | ✓ |
| M4 | Feedback | Like/Dislike (e ações estendidas pós-MVP) | ✓ |
| M5 | Perfil e Preferências | Preferências explícitas e aprendidas | ✓ |
| M6 | Histórico | Consulta de recomendações anteriores | ✓ |
| M7 | Autenticação | Registro, login, logout, refresh | ✓ |
| M8 | Playlists persistentes | Salvar e gerenciar playlists | Pós-MVP |
| M9 | Progressão de playlist | Início/meio/fim com curva de energia | Pós-MVP |
| M10 | Integração Spotify | OAuth + exportação de playlists | Pós-MVP |

### 7.2 Modos do Read With Music

| Modo | Prioridade | Objetivo |
|------|-----------|----------|
| **Focus** | Instrumental, ambiente, pouco invasivo | Não prejudicar concentração |
| **Immersive** | Forte afinidade com o universo do livro | Aumentar imersão |
| **Cinematic** | Atmosfera cinematográfica | Sensação épica/visual |
| **Calm** | Faixas tranquilas | Relaxamento / leitura noturna |
| **Custom** | Descrição livre do usuário | Flexibilidade total |

### 7.3 Ações de Feedback

`LIKE` · `DISLIKE` · `SAVE` · `MORE_LIKE_THIS` · `LESS_LIKE_THIS` · `ALREADY_KNOW` · `NOT_INTERESTED`

> **MVP:** apenas `LIKE` e `DISLIKE` são obrigatórios; as demais entram como evolução incremental.

---

## 8. Jornadas do Usuário

### J1 — Descoberta musical
1. Usuário acessa a Home e escolhe **Discover Music**.
2. Digita: *"Quero músicas melancólicas e calmas para madrugada, parecidas com No Surprises."*
3. O sistema interpreta a intenção e exibe resultados reais com links externos.
4. Usuário dá *Like* em algumas faixas e *Dislike* em outras.
5. Nas próximas buscas, o ranking reflete esse feedback.

### J2 — Descoberta de livros
1. Usuário escolhe **Find My Next Book**.
2. Informa livros de referência e o que deseja ("fantasia medieval, política, construção de mundo").
3. Recebe livros reais com capa, autor, descrição e motivo.
4. Pode clicar em **"Por que isso foi recomendado?"** para uma explicação gerada sob demanda.

### J3 — Read With Music
1. Usuário escolhe **Read With Music**, busca e seleciona *O Senhor dos Anéis*.
2. Define contexto ("antes de dormir"), modo (*Calm*), duração e preferência instrumental.
3. Recebe uma playlist coerente com o livro e o contexto.
4. Abre as faixas via links externos (Spotify/YouTube).

### J4 — Retorno e personalização
1. Usuário retorna, acessa o Dashboard e o histórico.
2. Revisa recomendações antigas e ajusta o perfil.

---

## 9. Requisitos de Alto Nível

### 9.1 Funcionais (resumo — detalhados no SRS)

- **RF-01** Interpretar pedidos em linguagem natural em critérios estruturados.
- **RF-02** Buscar candidatos reais via provedores externos.
- **RF-03** Ranquear candidatos com pontuação calculada pelo backend.
- **RF-04** Recomendar músicas, livros e músicas para livros.
- **RF-05** Registrar feedback e refletir nas recomendações futuras.
- **RF-06** Manter histórico e perfil de preferências.
- **RF-07** Autenticar usuários com JWT.
- **RF-08** Explicar recomendações sob demanda.

### 9.2 Não Funcionais (resumo)

- Arquitetura **monolítica modular**.
- Código tipado, testado e documentado.
- Provedores externos **desacoplados** (Provider Pattern).
- Cache para chamadas externas.
- Observabilidade básica (tempos, contagens, falhas).
- Segurança: hash de senha, JWT com expiração, rate limiting, CORS.

---

## 10. Métricas de Sucesso

### 10.1 Definição de Sucesso do MVP (critério de aceite)

O MVP está completo quando um usuário consegue:

1. criar uma conta;
2. informar algumas preferências;
3. solicitar recomendação musical em linguagem natural;
4. receber músicas reais e relevantes;
5. solicitar um próximo livro;
6. receber livros reais e relevantes;
7. informar um livro;
8. receber músicas adequadas à leitura;
9. dar feedback;
10. receber recomendações posteriores influenciadas por esse feedback;
11. consultar recomendações anteriores;
12. acessar links externos dos conteúdos recomendados.

Além disso: **backend documentado, frontend funcional, banco persistente, testes fundamentais e deploy público.**

### 10.2 Métricas de Produto (pós-MVP)

| Métrica | Definição |
|---|---|
| Recommendation Like Rate | Likes ÷ recomendações exibidas |
| Save Rate | Saves ÷ recomendações exibidas |
| Dislike Rate | Dislikes ÷ recomendações exibidas |
| Repeat Search Rate | Usuários com ≥2 buscas em 7 dias ÷ usuários ativos |
| Playlist Completion | Playlists com ≥1 faixa aberta ÷ playlists geradas |
| Recommendation Diversity | Artistas/autores únicos ÷ itens recomendados |
| Average Recommendation Score | Média do score final dos itens exibidos |

### 10.3 Critérios de Qualidade de uma Recomendação

Uma recomendação é considerada boa quando:

- respeita a intenção do usuário;
- **existe de fato**;
- é semanticamente relacionada ao pedido;
- considera o histórico do usuário;
- evita conteúdos rejeitados;
- apresenta diversidade razoável;
- não repete excessivamente artistas/autores;
- corresponde ao contexto solicitado.

---

## 11. Prioridades

Ordem de prioridade para decisões de trade-off:

1. **Qualidade das recomendações**
2. **Funcionamento correto**
3. **Arquitetura**
4. **Experiência do usuário**
5. **Personalização**
6. **Quantidade de funcionalidades**

> É preferível ter **poucas funcionalidades extremamente bem executadas** a muitas incompletas.

---

## 12. Mensagem Técnica Central (Entrevistas)

> *"Eu não simplesmente pedi para um LLM recomendar conteúdos. Desenvolvi um pipeline de recomendação em que a IA interpreta a intenção do usuário, o backend busca candidatos reais, embeddings calculam similaridade semântica e um algoritmo próprio combina contexto, similaridade e preferências do usuário para gerar um ranking personalizado."*

---

## 13. Riscos e Mitigações

| # | Risco | Prob. | Impacto | Mitigação |
|---|-------|:---:|:---:|-----------|
| R1 | API de música gratuita com metadados insuficientes (mood/energia) | Alta | Alto | Combinar múltiplas fontes (MusicBrainz + Last.fm tags); gerar embeddings a partir de tags/descrição; ADR de decisão |
| R2 | Limites de requisição (rate limits) das APIs externas | Média | Médio | Cache agressivo; retry com backoff; tabela local de candidatos |
| R3 | Custo/latência de LLM | Média | Médio | Não enviar candidatos ao LLM; explicação sob demanda; cache de parses |
| R4 | Cold start (usuário sem histórico) | Alta | Médio | Onboarding com preferências explícitas; ranking depende mais de similaridade semântica no início |
| R5 | Qualidade ruim de ranking | Média | Alto | Pesos ajustáveis; conjunto de queries de avaliação; testes de regressão do ranking |
| R6 | Escopo excessivo para portfólio | Alta | Alto | MVP estrito; fases; priorização (seção 11) |
| R7 | Mudança de termos de uso de APIs | Baixa | Alto | Provider Pattern; troca sem impacto no core |
| R8 | Estrutura do LLM output inválida | Média | Médio | Validação Pydantic; retry; fallback determinístico |

---

## 14. Premissas e Dependências

**Premissas**
- APIs gratuitas (Open Library, MusicBrainz, Last.fm) permanecem acessíveis durante o desenvolvimento.
- Existe um LLM com suporte a structured output disponível em plano gratuito ou de baixo custo.
- Um modelo de embeddings está disponível (API ou local).

**Dependências externas**
- Open Library / Google Books (livros).
- MusicBrainz / Last.fm (músicas) — *decisão final registrada em ADR-0004*.
- Provedor de LLM e embeddings — *ADR-0005*.
- Hospedagem para frontend, backend e PostgreSQL com pgvector.

---

## 15. Roadmap de Alto Nível

| Fase | Entrega |
|:---:|---|
| 1 | Foundation (repo, backend, DB, auth) |
| 2 | External Data (providers, normalização, cache) |
| 3 | AI Layer (LLM, parser, embeddings) |
| 4 | Recommendation Engine |
| 5 | Music Discovery |
| 6 | Book Discovery |
| 7 | Read With Music |
| 8 | Personalização |
| 9 | Frontend |
| 10 | Polish |
| 11 | Deploy |

> Detalhes em [`12-Development-Roadmap.md`](12-Development-Roadmap.md).

---

## 16. Evolução Futura

```
Music + Books → Movies → Games → Podcasts → Unified Discovery Platform
```

Exemplo: *"Quero algo com atmosfera cyberpunk e melancólica"* → músicas, livros, filmes e games.

> O nome do produto e a arquitetura (entidades e providers genéricos) devem permitir essa expansão.

---

## 17. Documentos Relacionados

| Documento | Arquivo |
|---|---|
| SRS | [`02-SRS.md`](02-SRS.md) |
| Arquitetura | [`03-System-Architecture.md`](03-System-Architecture.md) |
| Modelo de Dados | [`04-Data-Model.md`](04-Data-Model.md) |
| API | [`05-API-Specification.md`](05-API-Specification.md) |
| IA | [`06-AI-Architecture.md`](06-AI-Architecture.md) |
| Recommendation Engine | [`07-Recommendation-Engine-Specification.md`](07-Recommendation-Engine-Specification.md) |
| UX/UI | [`08-UX-UI-Specification.md`](08-UX-UI-Specification.md) |
| Segurança | [`09-Security-Specification.md`](09-Security-Specification.md) |
| Testes | [`10-Testing-Strategy.md`](10-Testing-Strategy.md) |
| Deploy | [`11-Deployment-Guide.md`](11-Deployment-Guide.md) |
| Roadmap | [`12-Development-Roadmap.md`](12-Development-Roadmap.md) |
