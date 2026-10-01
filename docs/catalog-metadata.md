# Proveniência das etiquetas do catálogo local

Conferência: 2026-10-01. Catálogo: `api/app/providers/local_catalog.py`, 18 livros e 25 músicas. Esta etapa acrescenta etiquetas a obras existentes; títulos, autoria e IDs são preservados. As fontes abaixo foram reabertas para conferir os metadados, sem copiar partituras, áudio ou textos das obras.

## Critério e limites

Descrições, atmosferas (`calmo`, `acolhedor`, `introspectivo` etc.), energia e presença de voz continuam sendo classificações editoriais. As novas etiquetas `piano` e `detetive` têm evidência específica nas fontes abaixo; sua aplicação ao vocabulário do Gandalf é uma decisão editorial.

`piano` significa que há uma obra/edição identificada com piano. Não promete piano solo, instrumentação de todas as versões, nem valida a gravação aberta pelo link de busca do YouTube. O catálogo local representa obras e não gravações identificadas. Uma edição para piano não autoriza generalizar a instrumentação para todo o repertório do artista.

`detetive` distingue narrativa de investigação por detetives do tema amplo `mistério`. O Cão dos Baskervilles conserva também `mistério`; a nova categoria não é aplicada automaticamente aos outros livros de mistério.

## Evidência por obra

| Obra / autoria no catálogo | Etiqueta | Fonte primária e evidência conferida |
| --- | --- | --- |
| Gymnopédie No. 1 — Erik Satie | `piano` | [Alfred Music, edição 00-2501](https://www.alfred.com/products/satie-3-gymnopedies-3-gnossiennes-00-2501): volume das três Gymnopédies e três Gnossiennes de Satie, identificado como livro para piano. A aplicação à primeira Gymnopédie decorre da inclusão no conjunto de três obras. |
| Clair de lune — Claude Debussy | `piano` | [Henle, HN 391](https://www.henle.de/Clair-de-lune/HN-391): edição Urtext de Debussy com instrumentação para piano solo. |
| Ambre — Nils Frahm | `piano` | [Faber Music, D50458](https://www.fabermusic.com/shop/ambre-d50458): identifica Frahm, a coleção Sheets Eins e o instrumento/formato piano solo. |
| Avril 14th — Aphex Twin | `piano` | [Faber Music, D44637](https://www.fabermusic.com/shop/avril-14th-d44637): edição da obra interpretada por Aphex Twin, arranjada para piano solo. Evidência de edição; não se afirma instrumentação universal. |
| River Flows in You — Yiruma | `piano` | [Hal Leonard, catálogo educacional 2012](https://www.halleonard.com/bin/PromoEducationalKeyboardFall40offpno2012.pdf#page=5), quinta página do PDF (índice 4): entrada 00296896 identifica a obra de Yiruma como solo de piano e apresenta arranjo intermediário de Wayne Hawkins. |
| Comptine d'un autre été, l'après-midi — Yann Tiersen | `piano` | [Hal Leonard, Contemporary Piano Masters, 2ª edição](https://www.halleonard.com/product-family/PC28241/contemporary-piano-masters-2nd-edition): coleção para piano solo, com Tiersen entre os compositores e a obra na lista de músicas. Sustenta essa edição para piano. |
| Spiegel im Spiegel — Arvo Pärt | `piano` | [Universal Edition, catálogo de Pärt](https://www.universaledition.com/media/f4/97/a0/1751447474/Paert_Jubilaeumskatalog_Webversion.pdf#page=16), página impressa 16 / 16ª página do PDF (índice 15): versões de 1978 para violino e piano, viola e piano e violoncelo e piano; também lista arranjos posteriores e versão para órgão. **Não é piano solo e existem versões sem piano.** |
| O Cão dos Baskervilles — Arthur Conan Doyle | `detetive` | [Penguin Classics, ISBN 9780241455296](https://www.penguin.co.uk/books/34513/the-hound-of-the-baskervilles-by-doyle-arthur-conan/9780241455296): a sinopse apresenta Holmes e Watson investigando a morte de Sir Charles Baskerville. A categoria do Gandalf é inferida desse conteúdo, sem generalizar a toda obra do autor. |

Os PDFs foram conferidos pela extração textual do navegador nas páginas indicadas; o serviço de captura de páginas retornou erro de cache. Não houve inspeção visual dos PDFs nesta sessão. Os links de editoras são evidência bibliográfica, não licença de distribuição das obras.

## Cobertura e continuidade

- Sete das 25 músicas recebem `piano`. Saman permanece sem a etiqueta: a sessão anterior não obteve evidência específica suficiente e esta etapa não amplia sua classificação.
- Um dos 18 livros recebe `detetive`. Ausência da etiqueta não prova ausência de piano ou investigação; as exclusões trabalham apenas com os metadados conhecidos.
- Piano e detetive são temas reconhecidos, não filtros rígidos de inclusão. Pedidos com vários temas podem trazer itens que atendem apenas a parte deles. Na descoberta local de livros, detetive participa do desempate por gênero explícito.
- Novas etiquetas precisam de evidência por obra e comparação contra o baseline aceito, preservando os julgamentos do corpus. Para ampliar Saman ou outros instrumentos/subgêneros, continuar por pesquisa específica da obra/edição.
