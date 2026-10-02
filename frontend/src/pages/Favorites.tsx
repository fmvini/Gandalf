import { useEffect, useRef, useState } from 'react'
import { Link, Navigate } from 'react-router-dom'
import { ArrowLeft, ArrowUpRight, BookOpen, Headphones, RefreshCw, Trash2 } from 'lucide-react'
import { useSession } from '../lib/useSession'
import { musicDestination, type BookItem, type MusicItem } from '../lib/api'
import { favoriteError, favorites, type Favorite, type FavoritePage, type FavoriteType } from '../lib/favorites'
import { localBookCover } from '../lib/showcase'

export default function Favorites() {
  const { user, expired } = useSession()
  if (!user) return <Navigate to="/login" replace state={{ notice: expired ? 'Sua sessão terminou. Entre novamente para acessar seus favoritos.' : undefined, returnTo: { pathname: '/account/favorites' } }} />
  return <Collection key={user.id} />
}

function Collection() {
  const [type, setType] = useState<FavoriteType | ''>('')
  const [offset, setOffset] = useState(0)
  const [attempt, setAttempt] = useState(0)
  const [data, setData] = useState<FavoritePage | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [removing, setRemoving] = useState<string | null>(null)
  const [notice, setNotice] = useState('')
  const mutation = useRef<AbortController | null>(null)
  const errorPanel = useRef<HTMLDivElement | null>(null)
  const heading = useRef<HTMLHeadingElement | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true); setError(''); setData(null)
    favorites.list(type, offset, controller.signal).then(page => {
      if (controller.signal.aborted) return
      if (!page.items.length && offset > 0) setOffset(Math.max(0, offset - 10))
      else setData(page)
    }).catch(cause => { if (!controller.signal.aborted) setError(favoriteError(cause)) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [type, offset, attempt])
  useEffect(() => () => mutation.current?.abort(), [])
  useEffect(() => { if (error) errorPanel.current?.focus() }, [error])

  async function remove(item: Favorite) {
    if (mutation.current) return
    const controller = new AbortController()
    mutation.current = controller
    setRemoving(item.id); setError(''); setNotice('')
    try {
      await favorites.remove(item.id, controller.signal)
      if (controller.signal.aborted) return
      setNotice(item.item.title + ' foi removido dos favoritos.')
      heading.current?.focus()
      setAttempt(value => value + 1)
    } catch (cause) { if (!controller.signal.aborted) setError(favoriteError(cause)) }
    finally { mutation.current = null; if (!controller.signal.aborted) setRemoving(null) }
  }

  return <section className="favorites-page container" aria-labelledby="favorites-title" aria-busy={loading || !!removing}>
    <Link className="account-explore" to="/account"><ArrowLeft size={17} aria-hidden="true" /> Voltar à conta</Link>
    <div className="library-heading"><div><h1 id="favorites-title" tabIndex={-1} ref={heading}>Seus favoritos.</h1><p>Músicas e livros que você guardou para encontrar de novo.</p></div><button className="text-button" type="button" disabled={loading || !!removing} onClick={() => setAttempt(value => value + 1)}><RefreshCw size={16} aria-hidden="true" /> Atualizar favoritos</button></div>
    <div className="favorite-filters" role="group" aria-label="Tipos de favoritos">{([{ value: '', label: 'Todos' }, { value: 'MUSIC', label: 'Músicas' }, { value: 'BOOK', label: 'Livros' }] as const).map(option => <button className="button button-secondary" type="button" key={option.value} aria-pressed={type === option.value} disabled={!!removing} onClick={() => { setType(option.value); setOffset(0); setNotice('') }}>{option.label}</button>)}</div>
    {notice ? <p role="status" className="field-help">{notice}</p> : null}
    {loading ? <p role="status" className="field-help">Buscando seus favoritos…</p> : null}
    {error ? <div className="account-error" role="alert" tabIndex={-1} ref={errorPanel}><p>{error}</p>{!data ? <button type="button" className="text-button" onClick={() => setAttempt(value => value + 1)}>Tentar novamente</button> : null}</div> : null}
    {data && !data.total ? <div className="library-empty"><h2>{type ? 'Nenhum favorito deste tipo por enquanto.' : 'Guarde o que você quer reencontrar.'}</h2><p>Use Salvar favorito nas sugestões de músicas, livros ou nas faixas de uma trilha.</p><div className="favorite-empty-links"><Link className="account-explore" to="/music">Descobrir músicas</Link><Link className="account-explore" to="/books">Encontrar livros</Link></div></div> : null}
    {data?.items.length ? <><ul className="result-list favorite-list">{data.items.map(item => <SavedItem key={item.id} favorite={item} removing={removing} onRemove={() => void remove(item)} />)}</ul><nav className="playlist-pagination" aria-label="Páginas de favoritos"><button className="button button-secondary" type="button" disabled={!offset || !!removing} onClick={() => setOffset(value => Math.max(0, value - 10))}>Anteriores</button><span>{offset + 1}–{offset + data.items.length} de {data.total}</span><button className="button button-secondary" type="button" disabled={offset + data.items.length >= data.total || !!removing} onClick={() => setOffset(value => value + 10)}>Próximas</button></nav></> : null}
  </section>
}

function SavedItem({ favorite, removing, onRemove }: { favorite: Favorite; removing: string | null; onRemove: () => void }) {
  const [imageFailed, setImageFailed] = useState(false)
  const music = favorite.type === 'MUSIC'
  const track = favorite.item as MusicItem
  const book = favorite.item as BookItem
  const image = music ? track.image_url : book.cover_url || (book.provider === 'local' ? localBookCover(book.title) : undefined)
  const destination = music ? musicDestination(track) : book.external_url ? { href: book.external_url, label: 'Ver livro' } : null
  return <li className="result-row"><div className={'result-image ' + (music ? 'music' : 'books')}>{image && !imageFailed ? <img src={image} alt="" loading="lazy" onError={() => setImageFailed(true)} /> : music ? <Headphones size={30} aria-hidden="true" /> : <BookOpen size={30} aria-hidden="true" />}</div><div className="result-main"><h2>{favorite.item.title}</h2><p>{music ? track.artist : book.authors.join(', ')}</p><div className="favorite-row-actions">{destination ? <a className="result-link" href={destination.href} target="_blank" rel="noopener noreferrer" aria-label={destination.label + ': ' + favorite.item.title}>{destination.label}<ArrowUpRight size={17} aria-hidden="true" /></a> : null}<button className="text-button favorite-button" type="button" disabled={!!removing} onClick={onRemove} aria-label={'Remover dos favoritos: ' + favorite.item.title}><Trash2 size={16} aria-hidden="true" />{removing === favorite.id ? 'Removendo…' : 'Remover favorito'}</button></div></div></li>
}
