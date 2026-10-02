import { useState, type ComponentProps } from 'react'
import { BookOpen } from 'lucide-react'
import type { BookItem } from '../lib/api'
import { bookCoverSource } from '../lib/showcase'

type Props = Omit<ComponentProps<'img'>, 'src' | 'onLoad' | 'onError'> & {
  book: Pick<BookItem, 'title' | 'provider' | 'cover_url'>
  fallbackSize?: number
}

export function BookCover({ book, alt = '', fallbackSize = 30, ...props }: Props) {
  const source = bookCoverSource(book)
  const [failedSource, setFailedSource] = useState<string | null>(null)
  if (!source || failedSource === source) return <span className="book-cover-fallback" aria-hidden="true"><BookOpen size={fallbackSize} /></span>
  return <img {...props} key={source} src={source} alt={alt}
    onError={() => setFailedSource(source)}
    onLoad={event => {
      // Legacy Open Library URLs can return a successful blank 1px image.
      // Mark only this source as failed so a new URL can load normally.
      if (event.currentTarget.naturalWidth <= 1 || event.currentTarget.naturalHeight <= 1) setFailedSource(source)
    }}
  />
}
