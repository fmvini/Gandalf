# Escopo do Projeto — Plataforma Inteligente de Descoberta de Músicas e Livros

## 1. Visão Geral

O projeto consiste no desenvolvimento de uma plataforma web inteligente voltada para descoberta personalizada de músicas e livros utilizando Inteligência Artificial como núcleo principal da aplicação.

A plataforma deverá permitir que o usuário descreva, em linguagem natural, aquilo que deseja ouvir ou ler. A IA deverá interpretar essa intenção, transformá-la em critérios estruturados e utilizar esses critérios para buscar, filtrar e classificar conteúdos relevantes.

O sistema possuirá três funcionalidades principais:

1. Descoberta de músicas.
2. Descoberta de livros.
3. Recomendação de músicas ou playlists que combinem com determinado livro.

A aplicação deverá aprender progressivamente as preferências do usuário por meio das suas interações, como músicas ou livros curtidos, rejeitados, salvos ou utilizados como referência.

O objetivo principal do projeto é servir como um projeto de portfólio completo, demonstrando conhecimentos de Python, desenvolvimento backend, Inteligência Artificial, sistemas de recomendação, integração com APIs externas, bancos de dados relacionais, busca vetorial, autenticação e desenvolvimento frontend.

---

# 2. Objetivo do Produto

Criar uma plataforma capaz de compreender preferências subjetivas expressadas em linguagem natural e convertê-las em recomendações úteis e personalizadas.

Exemplos:

> "Quero músicas melancólicas e calmas para ouvir de madrugada, parecidas com No Surprises."

> "Quero um livro de fantasia medieval sério, com bastante exploração, política e construção de mundo."

> "Estou lendo O Senhor dos Anéis e quero músicas instrumentais, medievais e calmas que combinem com a atmosfera do livro sem atrapalhar minha leitura."

O sistema não deverá apenas enviar a solicitação diretamente para um LLM e apresentar sua resposta.

A aplicação deverá possuir um mecanismo próprio de busca, filtragem, cálculo de similaridade e ranking das recomendações.

A Inteligência Artificial deverá ser utilizada principalmente para:

- interpretar linguagem natural;
- identificar características subjetivas;
- gerar embeddings;
- compreender relações semânticas;
- enriquecer consultas;
- explicar recomendações quando solicitado;
- auxiliar na construção do perfil de preferências do usuário.

---

# 3. Nome do Projeto

O nome definitivo poderá ser escolhido posteriormente.

O projeto deverá possuir uma identidade própria e não ser apresentado simplesmente como "AI Music Recommender".

O nome deve transmitir conceitos relacionados a:

- descoberta;
- música;
- livros;
- atmosfera;
- gosto pessoal;
- inteligência artificial;
- conexão entre diferentes formas de mídia.

O nome deve permitir que o produto evolua futuramente para outras formas de mídia.

---

# 4. Público-Alvo

Usuários que:

- gostam de descobrir músicas novas;
- procuram livros baseados em preferências específicas;
- têm dificuldade para decidir o próximo livro;
- procuram músicas adequadas para leitura;
- gostam de playlists relacionadas a atmosferas ou sentimentos;
- querem recomendações mais específicas do que filtros tradicionais de gênero;
- desejam que o sistema aprenda seus gostos ao longo do tempo.

---

# 5. Diferencial Principal

O principal diferencial da plataforma será permitir buscas baseadas em contexto e linguagem natural.

Em sistemas tradicionais, o usuário normalmente busca:

- um gênero;
- um artista;
- um título;
- uma categoria.

Nesta plataforma, o usuário poderá buscar por conceitos subjetivos.

Exemplos:

### Música

"Quero algo triste, mas reconfortante."

"Quero músicas parecidas com Red Swan, porém menos intensas."

"Quero músicas para estudar que tenham atmosfera de fantasia."

### Livros

"Quero fantasia medieval, mas sem romance como foco principal."

"Quero um livro de ficção científica que passe sensação de solidão e exploração."

"Gostei de Duna e Senhor dos Anéis. Quero algo com construção de mundo profunda."

### Livro + Música

"Estou lendo O Hobbit e quero músicas que façam parecer que estou viajando pela Terra Média."

"Estou lendo Duna e quero algo instrumental, atmosférico e misterioso."

---

# 6. Módulos Principais

## 6.1. Descoberta de Músicas

O usuário poderá descrever em linguagem natural o tipo de música que deseja encontrar.

O sistema deverá interpretar características como:

- humor;
- atmosfera;
- energia;
- gênero;
- instrumentação;
- presença de vocais;
- intensidade;
- contexto de uso;
- período ou estilo;
- artistas ou músicas de referência.

Exemplo:

> "Quero músicas parecidas com No Surprises, mas mais atmosféricas e adequadas para estudar."

O sistema poderá interpretar a solicitação como:

- mood: melancholic;
- energy: low;
- atmosphere: atmospheric;
- vocals: optional;
- context: studying;
- reference_song: No Surprises.

Após a interpretação, o sistema deverá buscar candidatos e calcular um ranking.

---

# 7. Descoberta de Músicas por Referência

O usuário poderá informar:

- nome da música;
- artista;
- uma ou mais músicas favoritas.

O sistema deverá encontrar músicas semanticamente ou musicalmente relacionadas.

Exemplo:

> "Quero algo parecido com Fake Plastic Trees, mas mais pesado."

O sistema deve considerar tanto a música de referência quanto as modificações solicitadas pelo usuário.

---

# 8. Descoberta de Livros

O usuário poderá descrever o tipo de livro que deseja ler.

Exemplo:

> "Quero uma fantasia medieval séria, com exploração, guerras e construção de mundo complexa."

A IA deverá extrair características como:

- gênero;
- subgênero;
- atmosfera;
- temática;
- ritmo;
- complexidade;
- presença ou ausência de romance;
- foco em personagens ou mundo;
- tom emocional.

O sistema deverá consultar uma fonte externa de livros e produzir um ranking personalizado.

---

# 9. Recomendações Baseadas em Livros Anteriores

O usuário poderá informar livros que gostou.

Exemplo:

> "Gostei muito de O Senhor dos Anéis, Duna e As Crônicas de Gelo e Fogo."

O sistema deverá utilizar essas informações como parte do perfil de preferências.

Também deverá ser possível solicitar:

> "Me recomende algo baseado nesses livros."

---

# 10. Funcionalidade Read With Music

Esta será uma das funcionalidades centrais e diferenciais do projeto.

O usuário informa um livro e recebe músicas que combinem com sua leitura.

Exemplo:

> "Estou lendo O Senhor dos Anéis."

O sistema deverá identificar características relevantes da obra, como:

- fantasia;
- aventura;
- ambiente medieval;
- natureza;
- exploração;
- mistério;
- momentos épicos.

Depois, o usuário poderá adicionar um contexto.

Exemplo:

> "Quero músicas para ler antes de dormir."

Neste caso, o sistema deverá adaptar as características musicais.

Possível resultado:

- instrumental;
- fantasy;
- medieval;
- acoustic;
- ambient;
- low energy;
- calm;
- minimal vocals.

---

# 11. Modos do Read With Music

A funcionalidade poderá possuir diferentes modos.

### Focus

Prioriza músicas instrumentais, ambientes e pouco invasivas.

Objetivo:

não prejudicar a concentração durante a leitura.

### Immersive

Prioriza músicas que combinem fortemente com o universo do livro.

Objetivo:

aumentar a imersão.

### Cinematic

Prioriza músicas de atmosfera cinematográfica.

### Calm

Prioriza faixas tranquilas.

### Custom

O usuário descreve livremente o que deseja.

---

# 12. Geração de Playlists

A plataforma deverá ser capaz de gerar conjuntos de músicas organizados como playlists.

O usuário poderá solicitar, por exemplo:

> "Crie uma playlist de uma hora para ler O Hobbit."

A playlist deverá tentar manter coerência entre as músicas.

O sistema deverá considerar:

- duração aproximada;
- energia;
- atmosfera;
- progressão;
- repetição de artistas;
- presença ou ausência de letras;
- contexto informado pelo usuário.

---

# 13. Progressão da Playlist

Uma funcionalidade avançada poderá permitir que a playlist tenha uma progressão.

Exemplo:

início:

calmo e atmosférico;

meio:

aventura e descoberta;

final:

mais emocional ou épico.

Isso diferencia a aplicação de um simples mecanismo de busca por músicas semelhantes.

---

# 14. Links Externos

Inicialmente, o sistema não precisará criar playlists automaticamente no Spotify.

Cada música poderá apresentar links para serviços externos.

Exemplos:

- Spotify;
- YouTube;
- outras plataformas compatíveis.

A exportação direta para Spotify deverá ser considerada uma funcionalidade futura.

---

# 15. Integração com Spotify — Versão Futura

Uma versão posterior poderá permitir:

1. autenticação com Spotify;
2. criação automática de playlists;
3. exportação das recomendações;
4. abertura da playlist diretamente na conta do usuário.

Essa funcionalidade não fará parte obrigatoriamente do MVP.

---

# 16. Perfil do Usuário

Cada usuário deverá possuir um perfil de preferências.

Possíveis informações:

### Preferências musicais

- artistas favoritos;
- músicas favoritas;
- gêneros favoritos;
- atmosferas favoritas;
- músicas curtidas;
- músicas rejeitadas.

### Preferências literárias

- livros favoritos;
- autores favoritos;
- gêneros favoritos;
- livros curtidos;
- livros rejeitados;
- livros já lidos.

---

# 17. Aprendizado de Preferências

O sistema deverá aprender com as interações do usuário.

Possíveis ações:

- gostei;
- não gostei;
- salvar;
- já conheço;
- quero mais como isso;
- quero menos como isso.

Essas ações deverão influenciar recomendações futuras.

O sistema não precisa treinar um modelo de Machine Learning próprio inicialmente.

O perfil poderá ser representado utilizando:

- dados estruturados;
- pesos de preferências;
- embeddings;
- histórico de interações.

---

# 18. Perfil Vetorial do Usuário

Como funcionalidade técnica mais avançada, o projeto poderá manter uma representação vetorial das preferências do usuário.

Exemplo conceitual:

Usuário gosta de:

- fantasy;
- melancholic;
- atmospheric;
- orchestral;
- introspective.

Cada interação poderá atualizar progressivamente esse perfil.

O perfil vetorial poderá ser usado para comparar conteúdos candidatos e aumentar ou diminuir sua pontuação.

---

# 19. Sistema de Recomendação

O sistema de recomendação deverá possuir múltiplas etapas.

Fluxo sugerido:

User Query

↓

Natural Language Interpretation

↓

Intent + Preference Extraction

↓

Candidate Retrieval

↓

Filtering

↓

Semantic Similarity

↓

User Preference Matching

↓

Ranking

↓

Recommendations

---

# 20. Sistema de Ranking

As recomendações não deverão depender exclusivamente da resposta do LLM.

O backend deverá calcular uma pontuação para cada candidato.

Exemplo conceitual:

score =

semantic_similarity * weight

+ user_preference_similarity * weight

+ reference_similarity * weight

+ context_match * weight

+ popularity_factor * weight

- disliked_characteristics_penalty

Os pesos poderão ser ajustados durante o desenvolvimento.

---

# 21. Explicação das Recomendações

O sistema não deverá gerar explicações automaticamente para todas as recomendações.

O usuário poderá clicar em:

"Por que isso foi recomendado?"

Nesse momento, o sistema utilizará os fatores envolvidos no ranking e poderá utilizar um LLM para gerar uma explicação compreensível.

Exemplo:

> "Esta música foi recomendada porque possui uma atmosfera melancólica e lenta semelhante às músicas que você costuma curtir, além de ter baixa intensidade, característica presente na sua busca atual."

---

# 22. Feedback de Recomendações

Cada recomendação deverá permitir feedback.

Exemplos:

Like

Dislike

Save

More like this

Less like this

Not interested

Already know

Esses dados poderão ser armazenados e usados para melhorar futuras recomendações.

---

# 23. Histórico

O sistema deverá manter histórico de:

- pesquisas;
- recomendações;
- playlists geradas;
- livros recomendados;
- músicas recomendadas;
- feedbacks.

O usuário poderá revisitar recomendações anteriores.

---

# 24. Favoritos

O usuário poderá manter coleções de:

- músicas favoritas;
- livros favoritos;
- playlists;
- recomendações salvas.

---

# 25. Autenticação

A aplicação deverá possuir autenticação.

Funcionalidades:

- registro;
- login;
- logout;
- refresh token;
- recuperação de sessão;
- proteção de endpoints.

Tecnologia sugerida:

JWT.

Posteriormente poderá ser adicionada autenticação OAuth.

---

# 26. Modo sem Login

Opcionalmente, algumas funcionalidades poderão funcionar sem conta.

Exemplo:

- realizar uma busca;
- testar recomendação;
- explorar músicas;
- explorar livros.

Entretanto, funcionalidades personalizadas deverão exigir autenticação.

Exemplo:

- salvar preferências;
- histórico;
- aprendizado;
- favoritos.

---

# 27. Inteligência Artificial

A IA terá quatro funções principais.

## 27.1 Interpretação de linguagem natural

Transformar pedidos livres em dados estruturados.

## 27.2 Embeddings

Representar semanticamente:

- solicitações;
- livros;
- músicas;
- preferências.

## 27.3 Explicação

Gerar explicações das recomendações quando solicitado.

## 27.4 Enriquecimento

Auxiliar na identificação de temas, atmosferas, emoções e contexto.

---

# 28. Structured Output

As respostas internas do LLM deverão utilizar dados estruturados sempre que possível.

Exemplo:

```json
{
  "intent": "music_discovery",
  "mood": [
    "melancholic",
    "calm"
  ],
  "energy": "low",
  "context": "studying",
  "vocals": "optional",
  "references": [
    {
      "song": "No Surprises",
      "artist": "Radiohead"
    }
  ]
}
```

Isso facilitará a integração com o sistema de ranking.

---

# 29. Segurança Contra Respostas Inventadas

A IA não deverá ser responsável por inventar músicas ou livros.

O fluxo recomendado é:

LLM interpreta intenção.

↓

Backend busca conteúdos reais.

↓

Sistema de ranking classifica conteúdos reais.

↓

LLM opcionalmente explica os resultados.

Assim, a aplicação reduz problemas de hallucination.

---

# 30. Fontes de Dados

O sistema deverá utilizar APIs gratuitas ou serviços que possuam um plano gratuito adequado ao desenvolvimento.

Para livros, poderão ser avaliadas opções como:

- Open Library;
- Google Books;
- outras APIs públicas.

Para música, deverá ser pesquisada uma fonte de dados compatível com as necessidades da aplicação.

A escolha final deverá considerar:

- disponibilidade;
- limites de requisição;
- possibilidade de pesquisa;
- metadados;
- estabilidade;
- termos de uso.

O sistema deverá ser desenvolvido de forma desacoplada para permitir a troca de provedores.

---

# 31. Provider Pattern

As fontes externas deverão utilizar uma camada de abstração.

Exemplo:

MusicProvider

BookProvider

Implementações futuras:

SpotifyProvider

MusicBrainzProvider

OpenLibraryProvider

GoogleBooksProvider

Isso permitirá trocar APIs sem alterar toda a aplicação.

---

# 32. Arquitetura

Arquitetura inicial sugerida:

Frontend

↓

REST API

↓

FastAPI Backend

↓

Application Services

↓

Recommendation Engine

↓

AI Services

↓

External Providers

↓

Database

---

# 33. Stack Principal

## Backend

Python

FastAPI

Pydantic

SQLAlchemy

Alembic

## Banco de dados

PostgreSQL

## Busca vetorial

pgvector

## Frontend

React

Vite

## Autenticação

JWT

## IA

LLM com suporte a structured output

Embeddings

## Testes

Pytest

---

# 34. Organização do Backend

Estrutura sugerida:

```text
backend/

app/

api/

routes/

auth.py
users.py
music.py
books.py
recommendations.py
playlists.py

core/

config.py
security.py
exceptions.py

models/

user.py
music.py
book.py
playlist.py
interaction.py

schemas/

user.py
music.py
book.py
recommendation.py
playlist.py

services/

auth_service.py
user_service.py
music_service.py
book_service.py
recommendation_service.py
playlist_service.py

ai/

llm_client.py
embedding_service.py
intent_parser.py
recommendation_explainer.py

recommendation/

ranking.py
similarity.py
filters.py
user_profile.py

providers/

music/

book/

repositories/

database/

main.py
```

---

# 35. Recommendation Engine

O mecanismo de recomendação deverá permanecer separado do restante da aplicação.

Possíveis módulos:

CandidateRetriever

SemanticMatcher

PreferenceMatcher

ContextMatcher

RankingEngine

RecommendationPipeline

Isso permitirá testar cada componente individualmente.

---

# 36. Modelo de Banco de Dados

Principais entidades:

User

UserPreference

Music

Book

Playlist

PlaylistTrack

Recommendation

Interaction

SearchHistory

Embedding

---

# 37. User

Campos possíveis:

id

email

username

password_hash

created_at

updated_at

---

# 38. UserPreference

Campos:

id

user_id

preference_type

value

weight

created_at

Exemplo:

music_genre

fantasy soundtrack

0.8

---

# 39. Music

Possíveis campos:

id

external_id

title

artist

album

genres

description

external_url

image_url

metadata

embedding

---

# 40. Book

Possíveis campos:

id

external_id

title

authors

description

genres

subjects

publication_year

cover_url

external_url

metadata

embedding

---

# 41. Interaction

Campos:

id

user_id

entity_type

entity_id

interaction_type

created_at

Tipos possíveis:

LIKE

DISLIKE

SAVE

MORE_LIKE_THIS

LESS_LIKE_THIS

ALREADY_KNOW

---

# 42. Recommendation

Campos:

id

user_id

recommendation_type

query

parsed_query

created_at

---

# 43. RecommendationItem

Campos:

recommendation_id

entity_id

score

semantic_score

preference_score

context_score

position

---

# 44. Playlist

Campos:

id

user_id

name

description

source

created_at

---

# 45. PlaylistTrack

Campos:

playlist_id

music_id

position

score

---

# 46. Endpoints Principais

## Auth

POST /auth/register

POST /auth/login

POST /auth/refresh

GET /auth/me

---

## Music

GET /music/search

GET /music/{id}

POST /music/discover

---

## Books

GET /books/search

GET /books/{id}

POST /books/discover

---

## Recommendations

POST /recommendations/music

POST /recommendations/books

POST /recommendations/read-with-music

GET /recommendations/history

GET /recommendations/{id}

---

## Feedback

POST /recommendations/{id}/feedback

---

## Playlist

POST /playlists

GET /playlists

GET /playlists/{id}

DELETE /playlists/{id}

---

## User Preferences

GET /users/me/preferences

POST /users/me/preferences

PATCH /users/me/preferences

---

# 47. Frontend

A interface deverá ser moderna e minimalista.

A página inicial deverá destacar três funcionalidades.

---

# 48. Home

Título conceitual:

"What are you looking for?"

Cards:

## Discover Music

Find music based on your mood, taste or a reference song.

## Find My Next Book

Describe what you feel like reading.

## Read With Music

Find the perfect soundtrack for your current book.

---

# 49. Barra de Busca Inteligente

Uma barra poderá aceitar comandos diretamente.

Exemplo:

> "Quero músicas atmosféricas para estudar."

O backend deverá classificar automaticamente a intenção quando possível.

---

# 50. Tela Discover Music

Componentes:

- prompt;
- música de referência;
- filtros opcionais;
- resultados;
- feedback;
- salvar;
- adicionar a playlist;
- explicar recomendação.

---

# 51. Tela Find My Next Book

Componentes:

- prompt;
- livros de referência;
- preferências;
- resultados;
- capa;
- descrição;
- autor;
- motivo da recomendação;
- salvar.

---

# 52. Tela Read With Music

Componentes:

- busca pelo livro;
- seleção do livro;
- contexto;
- modo;
- duração;
- preferência por vocal ou instrumental;
- geração da playlist;
- resultados.

---

# 53. Dashboard

O dashboard poderá apresentar:

- recomendações recentes;
- músicas salvas;
- livros salvos;
- playlists;
- histórico;
- preferências aprendidas.

---

# 54. Página de Perfil

Deverá permitir visualizar e editar:

- artistas favoritos;
- gêneros musicais;
- músicas favoritas;
- livros favoritos;
- gêneros literários;
- preferências aprendidas.

---

# 55. MVP

O MVP deverá conter somente o necessário para provar a proposta.

### Funcionalidades obrigatórias

Registro/login.

Descoberta de músicas por linguagem natural.

Descoberta de livros por linguagem natural.

Read With Music.

Sistema básico de ranking.

Embeddings.

Feedback Like/Dislike.

Perfil básico.

Histórico de recomendações.

Links externos.

---

# 56. Funcionalidades Pós-MVP

Após o funcionamento completo do MVP:

- perfil vetorial avançado;
- playlists persistentes;
- progressão musical;
- explicações avançadas;
- Spotify OAuth;
- exportação para Spotify;
- Google login;
- recomendação colaborativa;
- análise de comportamento;
- compartilhamento de playlists;
- sistema social.

---

# 57. Fases de Desenvolvimento

## Fase 1 — Foundation

- repositório;
- estrutura backend;
- configuração;
- PostgreSQL;
- Alembic;
- modelos;
- autenticação.

## Fase 2 — External Data

- provider de livros;
- provider musical;
- normalização dos dados;
- cache.

## Fase 3 — AI Layer

- integração com LLM;
- parser de intenção;
- structured output;
- embeddings.

## Fase 4 — Recommendation Engine

- recuperação de candidatos;
- filtros;
- similaridade;
- ranking;
- testes.

## Fase 5 — Music Discovery

Implementação completa.

## Fase 6 — Book Discovery

Implementação completa.

## Fase 7 — Read With Music

Implementação do módulo diferencial.

## Fase 8 — Personalização

- histórico;
- feedback;
- preferências.

## Fase 9 — Frontend

- autenticação;
- home;
- discovery;
- resultados;
- dashboard;
- perfil.

## Fase 10 — Polish

- testes;
- performance;
- tratamento de erros;
- loading states;
- documentação.

## Fase 11 — Deploy

- frontend;
- backend;
- banco;
- variáveis de ambiente;
- logs.

---

# 58. Testes

O projeto deverá possuir testes automatizados.

Priorizar testes para:

- parser de intenção;
- ranking;
- filtros;
- cálculo de similaridade;
- autenticação;
- endpoints principais;
- services;
- recommendation pipeline.

---

# 59. Observabilidade

O backend deverá registrar informações relevantes.

Exemplos:

- tempo para gerar recomendação;
- API externa utilizada;
- quantidade de candidatos;
- falhas de APIs;
- tempo gasto no LLM;
- quantidade de tokens quando disponível.

Não registrar informações sensíveis.

---

# 60. Cache

Chamadas para APIs externas deverão utilizar cache quando apropriado.

Exemplo:

uma busca repetida pelo mesmo livro não deve obrigatoriamente gerar uma nova requisição externa.

Redis poderá ser utilizado futuramente, mas não é obrigatório no MVP.

---

# 61. Tratamento de Erros

O sistema deverá tratar:

- API externa indisponível;
- conteúdo não encontrado;
- erro do LLM;
- timeout;
- resposta inválida;
- usuário não autenticado;
- rate limits;
- banco indisponível.

O frontend deverá mostrar mensagens compreensíveis.

---

# 62. Segurança

Considerar:

- hash seguro de senhas;
- JWT com expiração;
- refresh tokens;
- validação de entradas;
- rate limiting;
- CORS;
- proteção de secrets;
- variáveis de ambiente;
- prevenção contra SQL Injection através do ORM.

---

# 63. Privacidade

O sistema deverá armazenar apenas dados necessários para personalização.

O usuário deverá futuramente poder:

- limpar histórico;
- apagar preferências;
- excluir conta.

---

# 64. Performance

O sistema deverá evitar enviar grandes volumes de candidatos diretamente para o LLM.

O fluxo deverá priorizar:

database/API search

↓

filtering

↓

embeddings

↓

ranking

↓

small final result

Isso reduz custo e latência.

---

# 65. Estratégia de IA

Evitar arquitetura:

User

↓

LLM

↓

"Me dê 10 músicas"

A arquitetura desejada é:

User

↓

Intent Parser

↓

Candidate Retrieval

↓

Filtering

↓

Embedding Similarity

↓

Personalization

↓

Ranking

↓

Results

↓

Optional LLM Explanation

---

# 66. Critérios de Qualidade

Uma recomendação será considerada boa quando:

- respeitar a intenção do usuário;
- existir de fato;
- estiver semanticamente relacionada;
- considerar o histórico do usuário;
- evitar conteúdos rejeitados;
- apresentar diversidade razoável;
- não repetir excessivamente artistas;
- corresponder ao contexto solicitado.

---

# 67. Métricas Futuras

Possíveis métricas:

Recommendation Like Rate

Save Rate

Dislike Rate

Repeat Search Rate

Playlist Completion

Recommendation Diversity

Average Recommendation Score

---

# 68. Requisitos Não Funcionais

A aplicação deverá possuir:

- arquitetura modular;
- código tipado;
- documentação;
- validação de dados;
- migrações;
- testes;
- logs;
- variáveis de ambiente;
- separação de responsabilidades;
- possibilidade de trocar provedores externos;
- tratamento consistente de erros.

---

# 69. GitHub

O repositório deverá demonstrar qualidade profissional.

README contendo:

- apresentação;
- problema;
- solução;
- screenshots;
- arquitetura;
- stack;
- funcionalidades;
- execução local;
- variáveis de ambiente;
- API utilizada;
- funcionamento do recommendation engine;
- roadmap.

---

# 70. Documentação Técnica

O projeto deverá possuir documentos separados para:

1. Product Requirements Document — PRD.
2. Software Requirements Specification — SRS.
3. Arquitetura do Sistema.
4. Modelo de Dados.
5. API Specification.
6. AI Architecture.
7. Recommendation Engine Specification.
8. UX/UI Specification.
9. Security Specification.
10. Testing Strategy.
11. Deployment Guide.
12. Development Roadmap.
13. README.
14. CONTRIBUTING.
15. ADRs para decisões arquiteturais importantes.

---

# 71. Diagramas Recomendados

Criar:

- diagrama de arquitetura;
- diagrama entidade-relacionamento;
- fluxo de autenticação;
- fluxo Music Discovery;
- fluxo Book Discovery;
- fluxo Read With Music;
- pipeline de recomendação;
- fluxo de atualização das preferências.

---

# 72. Objetivo Técnico de Portfólio

O projeto deverá demonstrar domínio ou aprendizado prático em:

Python

FastAPI

REST APIs

PostgreSQL

SQLAlchemy

Alembic

Authentication

JWT

React

API Integration

LLMs

Prompt Engineering

Structured Outputs

Embeddings

Vector Search

pgvector

Recommendation Systems

Software Architecture

Automated Testing

Git

Deploy

---

# 73. Ponto Principal para Entrevistas

O projeto deverá permitir explicar claramente:

"Eu não simplesmente pedi para um LLM recomendar conteúdos. Desenvolvi um pipeline de recomendação em que a IA interpreta a intenção do usuário, o backend busca candidatos reais, embeddings calculam similaridade semântica e um algoritmo próprio combina contexto, similaridade e preferências do usuário para gerar um ranking personalizado."

Essa deverá ser uma das principais mensagens técnicas do projeto.

---

# 74. Limitações Iniciais

O MVP não precisa:

- treinar modelo próprio;
- possuir recomendação colaborativa;
- possuir milhões de músicas armazenadas;
- reproduzir músicas;
- armazenar arquivos de áudio;
- criar playlists diretamente no Spotify;
- possuir aplicativo mobile;
- implementar funcionalidades sociais;
- utilizar microservices.

Deve ser preferida uma arquitetura monolítica modular inicialmente.

---

# 75. Evolução Futura

Possíveis evoluções:

Music + Books

↓

Movies

↓

Games

↓

Podcasts

↓

Unified Discovery Platform

No futuro, o sistema poderia recomendar diferentes tipos de mídia a partir de uma única intenção.

Exemplo:

> "Quero alguma coisa com atmosfera cyberpunk e melancólica."

Resultado:

músicas;

livros;

filmes;

games.

---

# 76. Prioridade Geral

A prioridade deverá seguir esta ordem:

1. Qualidade das recomendações.
2. Funcionamento correto.
3. Arquitetura.
4. Experiência do usuário.
5. Personalização.
6. Quantidade de funcionalidades.

É preferível possuir menos funcionalidades extremamente bem executadas do que muitas funcionalidades incompletas.

---

# 77. Definição de Sucesso do MVP

O MVP será considerado completo quando um usuário puder:

1. criar uma conta;
2. informar algumas preferências;
3. solicitar uma recomendação musical em linguagem natural;
4. receber músicas reais e relevantes;
5. solicitar um próximo livro;
6. receber livros reais e relevantes;
7. informar um livro;
8. receber músicas adequadas à leitura;
9. dar feedback;
10. receber recomendações posteriores influenciadas por esse feedback;
11. consultar recomendações anteriores;
12. acessar links externos dos conteúdos recomendados.

O sistema deverá possuir backend documentado, frontend funcional, banco persistente, testes fundamentais e deploy público.

---

# 78. Diretriz Final

Todas as decisões futuras do projeto deverão preservar a seguinte ideia:

A Inteligência Artificial interpreta.

As fontes externas fornecem conteúdos reais.

O Recommendation Engine decide.

O perfil do usuário personaliza.

O LLM explica quando necessário.

A plataforma não deverá se tornar apenas uma interface para um chatbot.

