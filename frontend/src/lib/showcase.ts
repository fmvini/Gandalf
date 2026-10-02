import type { BookItem } from './api'

export const showcaseBooks = [
  { title: 'Duna', author: 'Frank Herbert', cover: '/images/covers/dune.jpg', mood: 'Ficção científica · Épico', description: 'Um planeta distante. Uma leitura para mergulhar.' },
  { title: 'O Hobbit', author: 'J. R. R. Tolkien', cover: '/images/covers/hobbit.jpg', mood: 'Fantasia · Aventura', description: 'O próximo caminho pode começar numa página.' },
  { title: 'O Jardim Secreto', author: 'Frances Hodgson Burnett', cover: '/images/covers/secret-garden.jpg', mood: 'Acolhedor · Esperançoso', description: 'Uma pausa tranquila entre novas descobertas.' },
] as const

export function localBookCover(title: string): string | undefined {
  return showcaseBooks.find(book => book.title === title)?.cover
}

export function bookCoverSource(book: Pick<BookItem, 'title' | 'provider' | 'cover_url'>): string | undefined {
  // The bundled edition belongs to our local catalog, not every namesake
  // from an external provider. Keep real provider metadata as the first choice.
  return book.cover_url || (book.provider === 'local' ? localBookCover(book.title) : undefined)
}
