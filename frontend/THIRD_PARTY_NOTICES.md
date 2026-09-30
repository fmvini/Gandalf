# Recursos de terceiros

## Componentes disponíveis no 21st.dev

As adaptações usam as fontes públicas dos autores. O marketplace `21st` está instalado; o CLI de busca exigiu autenticação e não foi utilizado para baixar componentes.

- `src/components/ui/animated-tabs.tsx`: baseado em [Animated Tabs de Chetan Verma](https://ui.chetanverma.com/components/animated-tabs), [disponível no 21st.dev](https://docs.21st.dev/@chetanverma16/components/animated-tabs). [Fonte original](https://github.com/chetanverma16/chetanverma-ui/blob/main/contents/components/animated-tabs/index.mdx), [licença](https://github.com/chetanverma16/chetanverma-ui/blob/main/LICENSE). Adaptado para grupo de escolhas controlado, ícones, temas e movimento reduzido, sem semântica de painéis de abas.
- `src/components/ui/three-d-carousel.tsx`: baseado em [3D Carousel do Cult UI](https://www.cult-ui.com/docs/components/three-d-carousel), [coleção no 21st.dev](https://docs.21st.dev/blog/cult-ui-components). [Fonte original](https://github.com/nolly-studio/cult-ui/blob/main/apps/www/registry/default/ui/three-d-carousel.tsx), [licença](https://github.com/nolly-studio/cult-ui/blob/main/LICENSE.md). Adaptado para três capas em perspectiva, navegação por botões/teclado/arraste, anúncio do livro ativo e preferência por movimento reduzido; sem cilindro, modal ou avanço automático.

Os dois componentes são distribuídos sob a licença MIT:

```text
MIT License

Copyright (c) 2024 chetanverma
Copyright (c) 2023 Jordan-Gilliam

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

## Capas

Obtidas em 30/09/2026 da Open Library Covers API e servidas localmente. São capas de edições em inglês; títulos da interface seguem o catálogo em português. Os direitos das capas permanecem com seus respectivos titulares; não estão cobertos pela licença MIT dos componentes.

| Arquivo | Livro / ISBN | Origem |
| --- | --- | --- |
| `public/images/covers/dune.jpg` | Duna — 9780441172719 | [Open Library](https://covers.openlibrary.org/b/isbn/9780441172719-L.jpg?default=false) |
| `public/images/covers/hobbit.jpg` | O Hobbit — 9780261103344 | [Open Library](https://covers.openlibrary.org/b/isbn/9780261103344-L.jpg?default=false) |
| `public/images/covers/secret-garden.jpg` | O Jardim Secreto — 9780141321066 | [Open Library](https://covers.openlibrary.org/b/isbn/9780141321066-L.jpg?default=false) |

## Fontes

Manrope Variable (`@fontsource-variable/manrope`) e Newsreader (`@fontsource/newsreader`) são distribuídas sob SIL Open Font License 1.1. Licenças e avisos autorais acompanham o build em `public/licenses/manrope.txt` e `public/licenses/newsreader.txt`. As fontes são hospedadas no próprio build; não há chamada ao Google Fonts na página.
