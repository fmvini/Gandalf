import { createRoot } from 'react-dom/client'
import { BookCover } from '../../src/components/BookCover'
import type { BookItem } from '../../src/lib/api'

const host = document.createElement('div')
host.id = 'cover-regression-fixture'
host.className = 'mini-cover'
document.body.append(host)
const root = createRoot(host)

// Keep the component mounted: resetting the root would hide source-state bugs.
export function render(book: Pick<BookItem, 'title' | 'provider' | 'cover_url'>) {
  root.render(<BookCover book={book} alt="Regression cover" />)
}

export function dispose() {
  root.unmount()
  host.remove()
}
