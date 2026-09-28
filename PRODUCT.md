# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

React, Vite e TypeScript, conforme docs/08-ux-ui-specification.md.

## Users

- Pessoas que procuram músicas por sensação, contexto ou referência.
- Pessoas que querem escolher a próxima leitura.
- Pessoas que procuram uma trilha para o livro que estão lendo.

## Product Purpose

Permitir descobertas de músicas e livros a partir de pedidos em linguagem natural e criar trilhas para leitura.

## Positioning

A IA interpreta o pedido; provedores externos fornecem itens reais; um motor próprio classifica as recomendações. O pedido interpretado e as razões de cada sugestão devem ser visíveis ao usuário.

## Operating Context

Uso público sem conta para a primeira descoberta, em desktop e mobile. Uma conta acrescentará histórico, itens salvos e preferências.

## Capabilities and Constraints

- Fluxos públicos: descobrir músicas, descobrir livros, criar trilha para leitura.
- Interface responsiva com tema claro e escuro; meta WCAG 2.1 AA.
- A API especificada em docs/05-API-Specification.md ainda não está implementada neste repositório. A interface não deve simular resultados como reais.
- Nome Gandalf confirmado pelo usuário como provisório em 28/09/2026.
- Roxo e atmosfera cozy são compromissos visuais confirmados pelo usuário.
- O tema escuro é o padrão; o claro deve estar disponível como alternativa.
- Idioma padrão da interface ainda está em aberto na documentação.

## Evidence on Hand

Escopo, PRD, contratos de API e especificação de UX em docs/. Não há depoimentos, números de uso ou catálogo local de músicas e livros.

## Product Principles

1. O pedido em linguagem natural é o ponto de partida.
2. Recomendações são itens reais e acionáveis.
3. O usuário pode entender como o pedido foi interpretado.
4. É possível experimentar sem criar conta.
