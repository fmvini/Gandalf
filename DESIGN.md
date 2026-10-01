---
name: Gandalf
description: Descoberta imersiva de música e livros, com capas e movimento discreto.
colors:
  primary: "#ad8bd2"
  primary-hover: "#b99cda"
  ink-plum: "#171321"
  surface-plum: "#211b2e"
  raised-plum: "#2b233b"
  text-ivory: "#f4eef5"
  text-muted: "#c5b7ca"
  border-violet: "#544662"
  soft-violet: "#382b4b"
  light-ground: "#f6f1f7"
  light-text: "#2d2337"
typography:
  display:
    fontFamily: "Manrope Variable, sans-serif"
    fontSize: "clamp(2.7rem, 4.3vw, 4.1rem)"
    fontWeight: 600
    lineHeight: 1.12
    letterSpacing: "-0.04em"
  body:
    fontFamily: "Manrope Variable, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  control: "8px"
  sm: "10px"
  md: "12px"
  lg: "18px"
  showcase: "16px"
  pill: "999px"
spacing:
  xs: "8px"
  sm: "16px"
  md: "24px"
  lg: "40px"
  xl: "64px"
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.ink-plum}"
    rounded: "{rounded.pill}"
    padding: "11px 20px"
  search-field:
    backgroundColor: "{colors.surface-plum}"
    textColor: "{colors.text-ivory}"
    rounded: "{rounded.md}"
    padding: "7px 7px 7px 18px"
---

# Design System: Gandalf

## Overview

**Creative North Star: "Descoberta imersiva"**

O Gandalf trata o pedido em linguagem natural como o início de um percurso por sensações. Capas reais e movimento discreto aproximam o catálogo do visitante; os fluxos de busca mantêm formulários e resultados objetivos. O tema principal é escuro, roxo e cozy. O tema claro conserva a mesma hierarquia. Esta composição foi aprovada pelo usuário em 30/09/2026.

**Key Characteristics:**

- Tipografia legível, marca editorial e controles fáceis de identificar.
- Fundo ameixa, superfícies tonais e acento violeta.
- Capas reais em perspectiva com navegação explícita.
- Espaço suficiente para pedidos, filtros e metadados reais.

## Colors

O roxo guia as ações, enquanto fundos ameixa e texto marfim sustentam o uso prolongado.

### Primary

- **Ametista acolhedora** (#ad8bd2): botões principais, ações e seleção.
- **Ametista clara** (#b99cda): hover e ênfase sobre o fundo escuro.

### Neutral

- **Ameixa de fundo** (#171321): tema padrão.
- **Ameixa de superfície** (#211b2e): formulários e áreas de conteúdo.
- **Marfim noturno** (#f4eef5): texto principal.
- **Lavanda suave** (#c5b7ca): texto secundário.
- **Lilás de papel** (#f6f1f7): fundo do tema claro.

**The Catalog Rule.** Capas abrem a descoberta; listas e formulários usam superfícies simples para deixar o conteúdo real em primeiro plano. O atlas ilustrado permanece como apoio nas páginas internas.

## Typography

**Display / Body Font:** Manrope Variable (fallback sans-serif).
**Brand Font:** Newsreader (fallback Georgia).

Manrope aproxima títulos, instruções e controles. Newsreader preserva o caráter editorial da marca e da numeração das faixas. Ambas são servidas localmente por Fontsource.

### Hierarchy

- **Display** (600, até 4.1rem, line-height 1.12): título da Home.
- **Headline** (600, até 4rem): páginas de descoberta.
- **Title** (600–650, 1 a 1.5rem): caminhos, resultados e livro em destaque.
- **Body** (400, 1rem, line-height 1.55): instruções e descrições.
- **Label** (600–700): controles; metadados menores mantêm contraste e espaçamento.

## Layout

Contêiner máximo de 1260px com margem fluida. Na Home, busca e carrossel dividem o primeiro quadro; abaixo de 850px, a composição vira uma coluna, mantendo a busca antes das capas. Os três caminhos se tornam linhas empilhadas. O cabeçalho usa navegação móvel abaixo de 760px. Resultados usam linhas para leitura rápida; modos de leitura usam uma grade que se reduz no celular. Ajustes em 520px e 360px preservam controles sem rolagem horizontal.

## Elevation & Depth

Camadas tonais fazem a maior parte da separação. Capas recebem sombra difusa com deslocamento e perspectiva; a busca usa borda fina, reforçada no foco. Evitar ampliar esse tratamento de profundidade para todos os resultados.

## Shapes

Campos e painéis usam cantos de 10 a 18px. A busca principal tem raio de 12px, seus controles internos 8px e a vitrine 16px. Botões gerais conservam forma de cápsula; os da Home usam cantos menores. As linhas de resultados não recebem uma caixa individual.

## Components

### Buttons

- **Primary:** ametista, texto ameixa, altura mínima de 48px; hover mais claro e foco visível.
- **Secondary:** superfície violeta suave com borda discreta.

### Inputs / Fields

- Superfície ameixa, texto marfim e borda violeta. O foco muda a borda para ametista; o cursor segue a mesma cor.

### Navigation

- Uma linha no desktop. No celular, menu acessível por botão. A rota ativa recebe uma linha sutil.

### Atlas

- Arte raster sem texto embutido; rótulos legíveis em HTML se adaptam ao tamanho da tela.

### Catálogo e escolhas

- Carrossel sem avanço automático: botões, setas do teclado e arraste mudam o livro ativo; link leva à busca de trilha com o título preenchido.
- Grupo de escolhas Música/Livros/Ler com música usa botões pressionáveis e destaque que acompanha a seleção; não representa painéis de abas.
- Origem e adaptações dos componentes estão em `frontend/THIRD_PARTY_NOTICES.md`.

### Preferências, explicações e carregamento

- Preferências musicais usam Accordion e escolhas Radix de seleção única, com opção Tanto faz, indicação visual de seleção e limpeza. Resultados conservam os filtros submetidos; alterações posteriores pedem uma nova busca.
- Explicações nos três fluxos usam Accordion com busca ao abrir, cache por resultado e retry explícito. Skeletons são decorativos e acompanham as mensagens reais de carregamento/cancelamento; sua pulsação e a expansão do Accordion são removidas com movimento reduzido.

### Movimento

- Abertura da Home com deslocamentos curtos e conteúdo já visível; sequência de até 550ms com saída suave.
- Capas e destaque de seleção usam molas amortecidas. Caminhos entram uma vez ao aparecer na tela, com intervalo de 70ms.
- Hover eleva ações em 2px apenas onde há mouse e movimento permitido.
- `prefers-reduced-motion` elimina entradas e deslocamentos animados, mantendo navegação e informação; sem loops decorativos.

## Do's and Don'ts

### Do:

- **Do** iniciar a descoberta com um pedido livre e um destino explícito.
- **Do** manter o tema escuro como padrão e oferecer o claro.
- **Do** usar imagens de catálogo apenas quando vierem de provedores reais.

### Don't:

- **Don't** apresentar resultados demonstrativos como recomendações reais.
- **Don't** depender de animação ou arraste para acessar conteúdo.
- **Don't** usar brilho neon, gradiente roxo genérico ou cartões iguais para os três caminhos.
