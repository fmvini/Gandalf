# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Product Purpose

Descobrir músicas e livros a partir de uma descrição e criar uma seleção musical para acompanhar um livro.

## Stack

React, Vite, TypeScript e FastAPI. Implementação e limites em `docs/IMPLEMENTATION_STATUS.md`.

## Users

- Pessoas que procuram músicas por sensação, contexto ou referência.
- Pessoas que querem escolher a próxima leitura.
- Pessoas que procuram uma trilha para o livro que estão lendo.

## Positioning

A arquitetura alvo separa interpretação por IA, itens reais de provedores e classificação pelo motor próprio. O modo local usa regras e catálogo offline; o modo online é experimental e tem divergências documentadas. O pedido interpretado e as razões de cada sugestão devem ser visíveis.

## Operating Context

Uso público sem conta para a primeira descoberta, em desktop e mobile. Histórico, itens salvos e preferências por conta são evolução prevista, ainda não implementada.

## Capabilities and Constraints

- Preservar os três fluxos públicos, rotas, formulários, filtros, estados de erro/vazio/carregamento e explicações.
- Interface responsiva com temas claro/escuro; meta WCAG 2.1 AA, sem certificação de conformidade.
- API e catálogo local funcionais; integrações online experimentais exigem configuração própria.
- Sem reprodução de áudio integrada. Links externos abrem fontes/buscas.
- Não apresentar seleção ilustrativa do catálogo como recomendação personalizada.

## Brand Commitments

- Nome Gandalf confirmado como provisório pelo usuário em 28/09/2026.
- Roxo e atmosfera cozy são compromissos visuais confirmados; escuro como padrão e claro disponível.
- Interface atual em português brasileiro.
- Em 30/09/2026, o usuário escolheu descoberta imersiva, com capas e movimento discreto, e aprovou a composição implementada.
- Componentes disponíveis no 21st.dev adaptados a partir das fontes públicas dos autores; créditos em `frontend/THIRD_PARTY_NOTICES.md`.

## Evidence on Hand

`api/app/providers/local_catalog.py`, `docs/IMPLEMENTATION_STATUS.md`, interface e testes Playwright em `frontend/`. Não há dados de usuários, métricas comerciais ou depoimentos aprovados.

## Accessibility & Inclusion

Preservar navegação por teclado, foco visível, rótulos, responsividade e preferência por movimento reduzido.

## Product Principles

1. O pedido em linguagem natural é o ponto de partida.
2. Recomendações são itens reais e acionáveis.
3. O usuário pode entender como o pedido foi interpretado.
4. É possível experimentar sem criar conta.
