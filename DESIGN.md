---
name: Gandalf
description: Descoberta de música e livros em um atlas noturno acolhedor.
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
    fontFamily: "Newsreader, Georgia, serif"
    fontSize: "clamp(3.7rem, 5.7vw, 6rem)"
    fontWeight: 500
    lineHeight: 0.97
    letterSpacing: "-0.03em"
  body:
    fontFamily: "DM Sans, sans-serif"
    fontSize: "1rem"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  sm: "10px"
  md: "12px"
  lg: "18px"
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
    rounded: "{rounded.pill}"
    padding: "7px 7px 7px 22px"
---

# Design System: Gandalf

## Overview

**Creative North Star: "Atlas de afinidades"**

O Gandalf trata o pedido em linguagem natural como o início de um percurso por sensações. O mapa ilustrado é uma peça editorial que expressa essa ideia na Home; os fluxos de busca mantêm formulários e resultados objetivos. O tema principal é escuro, roxo e cozy, como um atlas aberto em uma sala de leitura à noite. O tema claro conserva a mesma hierarquia.

**Key Characteristics:**

- Tipografia editorial e controles fáceis de identificar.
- Fundo ameixa, superfícies tonais e acento violeta.
- Mapa autoral com rótulos em HTML para preservar leitura e adaptação.
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

**The Atlas Rule.** A ilustração abre a experiência; listas e formulários usam superfícies simples para deixar o conteúdo real em primeiro plano.

## Typography

**Display Font:** Newsreader (fallback Georgia).
**Body Font:** DM Sans (fallback sans-serif).

Newsreader dá caráter de publicação cultural a títulos e chamadas. DM Sans mantém as instruções e os controles diretos.

### Hierarchy

- **Display** (500, até 6rem, line-height 0.97): tese da Home.
- **Headline** (500, até 5.2rem): páginas de descoberta.
- **Title** (500, 1.35 a 1.75rem): resultados e caminhos.
- **Body** (400, 1rem, line-height 1.55): instruções e descrições.
- **Label** (700, 0.83 a 0.96rem): controles e metadados.

## Layout

Contêiner máximo de 1260px com margem fluida. Na Home, texto e atlas dividem o primeiro quadro; abaixo de 760px, a composição vira uma coluna e mantém a busca acima do mapa. Resultados usam linhas para leitura rápida, e a escolha de modos usa uma grade que se reduz a duas colunas no celular.

## Elevation & Depth

Camadas tonais fazem a maior parte da separação. A busca principal recebe uma sombra difusa com deslocamento; painéis usam borda fina quando o agrupamento precisa ficar explícito.

## Shapes

Campos e painéis usam cantos de 10 a 18px. Busca principal, chips e botões principais usam forma de cápsula. As linhas de resultados não recebem uma caixa individual.

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

## Do's and Don'ts

### Do:

- **Do** iniciar a descoberta com um pedido livre e um destino explícito.
- **Do** manter o tema escuro como padrão e oferecer o claro.
- **Do** usar imagens de catálogo apenas quando vierem de provedores reais.

### Don't:

- **Don't** apresentar resultados demonstrativos como recomendações reais.
- **Don't** transformar o mapa em um controle confuso ou obrigatório.
- **Don't** usar brilho neon, gradiente roxo genérico ou cartões iguais para os três caminhos.
