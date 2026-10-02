# Recursos de terceiros

## Componentes disponíveis no 21st.dev

As adaptações usam as fontes dos autores. Accordion e Toggle Group foram recuperados pelo MCP autenticado do 21st.dev em 01/10/2026; Skeleton usa a fonte pública do shadcn. A consulta é uma ferramenta de desenvolvimento, sem chave ou chamadas ao 21st no produto.

- `src/components/ui/animated-tabs.tsx`: baseado em [Animated Tabs de Chetan Verma](https://ui.chetanverma.com/components/animated-tabs), [disponível no 21st.dev](https://docs.21st.dev/@chetanverma16/components/animated-tabs). [Fonte original](https://github.com/chetanverma16/chetanverma-ui/blob/main/contents/components/animated-tabs/index.mdx), [licença](https://github.com/chetanverma16/chetanverma-ui/blob/main/LICENSE). Adaptado para grupo de escolhas controlado, ícones, temas e movimento reduzido, sem semântica de painéis de abas.
- `src/components/ui/three-d-carousel.tsx`: baseado em [3D Carousel do Cult UI](https://www.cult-ui.com/docs/components/three-d-carousel), [coleção no 21st.dev](https://docs.21st.dev/blog/cult-ui-components). [Fonte original](https://github.com/nolly-studio/cult-ui/blob/main/apps/www/registry/default/ui/three-d-carousel.tsx), [licença](https://github.com/nolly-studio/cult-ui/blob/main/LICENSE.md). Adaptado para três capas em perspectiva, navegação por botões/teclado/arraste, anúncio do livro ativo e preferência por movimento reduzido; sem cilindro, modal ou avanço automático.

- `src/components/ui/accordion.tsx`: [Accordion de shadcn no 21st.dev](https://21st.dev/@shadcn/components/accordion), demo 1530. Adaptado para painel único recolhível, preferências e explicações carregadas sob demanda; primitivas Radix, tokens locais e movimento reduzido.
- `src/components/ui/toggle-group.tsx`: [Toggle Group de shadcn no 21st.dev](https://21st.dev/@shadcn/components/toggle-group), demo 252. Adaptado para seleção única obrigatória de vocais/energia, opção indiferente, indicador de seleção e navegação por teclado Radix.
- `src/components/ui/skeleton.tsx`: [Skeleton de shadcn no 21st.dev](https://21st.dev/@shadcn/components/skeleton), [fonte pública](https://github.com/shadcn-ui/ui/blob/main/apps/v4/registry/new-york-v4/ui/skeleton.tsx). Adaptado para placeholders decorativos de músicas, livros e trilhas, preservando mensagens/cancelamento e movimento reduzido.
- `src/components/ui/alert.tsx`: [Alert de shadcn listado no 21st.dev](https://21st.dev/community/components/shadcn/alert/default), [fonte oficial](https://github.com/shadcn-ui/ui/blob/main/apps/v4/registry/new-york-v4/ui/alert.tsx), consultada em 02/10/2026. Adaptado do contêiner e descrição (`Alert`, `AlertDescription`) para estados inline de renovação: tokens locais, textos completos, erro assertivo e progresso/resultado educados. CSS nativo substitui Tailwind/CVA, sem dependências novas. **Fonte pública:** o MCP autenticado estava indisponível (`WinError 10061`); não houve recuperação autenticada nem confirmação de cota nesta sessão.

Os componentes shadcn são cobertos pela [licença MIT](https://github.com/shadcn-ui/ui/blob/main/LICENSE.md). Os componentes adaptados acima são distribuídos sob a licença MIT:

```text
MIT License

Copyright (c) 2024 chetanverma
Copyright (c) 2023 Jordan-Gilliam
Copyright (c) 2023 shadcn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

## React Bits

`src/components/ui/animated-content.tsx` adapta o comportamento de [AnimatedContent, por David Haz](https://reactbits.dev/animations/animated-content), a partir da [fonte TypeScript oficial](https://github.com/DavidHDev/react-bits/blob/main/src/ts-default/Animations/AnimatedContent/AnimatedContent.tsx), consultada em 02/10/2026. Da fonte, mantém deslocamento vertical curto, retorno ao repouso e saída suave; substitui GSAP/ScrollTrigger por `motion/react` já instalado. A transição marca a chegada de uma seleção nova, sem ocultar conteúdo, esperar scroll ou reaparecer após editar filtros. `prefers-reduced-motion` apresenta o conteúdo estático; não há desaparecimento, escala, blur ou repetição automática.

Distribuído como parte do Gandalf sob [MIT + Commons Clause License Condition v1.0](https://github.com/DavidHDev/react-bits/blob/main/LICENSE.md), **não MIT simples**. Copyright (c) 2026 David Haz. O texto integral acompanha o produto em `public/licenses/react-bits.txt`. A licença permite uso como parte de aplicação/site/produto e restringe revenda, sublicenciamento e redistribuição dos componentes em si, inclusive versões portadas. Este componente integra o produto; não é distribuído como biblioteca independente.

## Capas

Obtidas em 30/09/2026 da Open Library Covers API e servidas localmente. São capas de edições em inglês; títulos da interface seguem o catálogo em português. Os direitos das capas permanecem com seus respectivos titulares; não estão cobertos pela licença MIT dos componentes.

| Arquivo | Livro / ISBN | Origem |
| --- | --- | --- |
| `public/images/covers/dune.jpg` | Duna — 9780441172719 | [Open Library](https://covers.openlibrary.org/b/isbn/9780441172719-L.jpg?default=false) |
| `public/images/covers/hobbit.jpg` | O Hobbit — 9780261103344 | [Open Library](https://covers.openlibrary.org/b/isbn/9780261103344-L.jpg?default=false) |
| `public/images/covers/secret-garden.jpg` | O Jardim Secreto — 9780141321066 | [Open Library](https://covers.openlibrary.org/b/isbn/9780141321066-L.jpg?default=false) |

## Fontes

Manrope Variable (`@fontsource-variable/manrope`) e Newsreader (`@fontsource/newsreader`) são distribuídas sob SIL Open Font License 1.1. Licenças e avisos autorais acompanham o build em `public/licenses/manrope.txt` e `public/licenses/newsreader.txt`. As fontes são hospedadas no próprio build; não há chamada ao Google Fonts na página.
