import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Bookmark } from 'lucide-react'
import { ApiError, type BookItem, type MusicItem, type Recommendation } from '../lib/api'
import { useSession } from '../lib/useSession'
import { playlistError, playlists } from '../lib/playlists'

export type ReadingSnapshot = {
  book: BookItem; result: Recommendation<MusicItem>
  settings?: { mode: 'FOCUS' | 'IMMERSIVE' | 'CINEMATIC' | 'CALM' | 'CUSTOM'; context: string; length: number; vocals: string }
}

export function SavePlaylist({ reading }: { reading: ReadingSnapshot }) {
  const { user } = useSession()
  return <SaveForm key={(user?.id || 'anonymous') + reading.result.recommendation_id} reading={reading} signedIn={!!user} />
}

function SaveForm({ reading, signedIn }: { reading: ReadingSnapshot; signedIn: boolean }) {
  const [name, setName] = useState(reading.book.title.slice(0, 120))
  const [pending, setPending] = useState(false)
  const [saved, setSaved] = useState<string | null>(null)
  const [error, setError] = useState('')
  const [expired, setExpired] = useState(false)
  const controller = useRef<AbortController | null>(null)
  const errorPanel = useRef<HTMLParagraphElement | null>(null)
  useEffect(() => () => controller.current?.abort(), [])
  useEffect(() => { if (error) errorPanel.current?.focus() }, [error])

  async function save(event: FormEvent) {
    event.preventDefault()
    if (pending || !name.trim() || !reading.result.recommendation_id) return
    const next = new AbortController()
    controller.current = next
    setPending(true)
    setError('')
    try {
      const playlist = await playlists.create(name, reading.result.recommendation_id, next.signal)
      if (!next.signal.aborted) setSaved(playlist.id)
    } catch (cause) {
      if (!next.signal.aborted) {
        setError(playlistError(cause, true))
        setExpired(cause instanceof ApiError && cause.status === 404)
      }
    } finally { if (!next.signal.aborted) setPending(false) }
  }

  if (!reading.result.recommendation_id || !reading.result.items.length) return null
  return <div className="save-playlist">
    {saved ? <p role="status">Playlist salva na sua conta. <Link className="account-explore" to={'/account/playlists/' + saved}>Ver playlist</Link></p>
      : !signedIn ? <p>Guarde esta trilha para voltar a ela depois. <Link className="account-explore" to="/login" state={{ notice: 'Entre para salvar sua trilha. Ela estará aqui quando você voltar.', returnTo: { pathname: '/read-with-music', state: { reading } } }}>Entrar para salvar</Link></p>
        : <form onSubmit={save} aria-busy={pending}>
          <div className="form-group"><label htmlFor="playlist-name">Nome da playlist</label><input id="playlist-name" value={name} onChange={event => setName(event.target.value)} maxLength={120} required disabled={pending || expired} /></div>
          <button className="button button-secondary" type="submit" disabled={pending || expired || !name.trim()}><Bookmark size={17} aria-hidden="true" />{pending ? 'Salvando…' : error ? 'Tentar salvar novamente' : 'Salvar na minha conta'}</button>
          {error ? <p className="account-error" role="alert" tabIndex={-1} ref={errorPanel}>{error}</p> : null}
          <p className="field-help">Salva todas as faixas, na ordem desta trilha. {expired ? 'Use Criar minha trilha para gerar uma nova seleção.' : 'Você poderá consultar ou excluir a playlist na sua conta.'}</p>
        </form>}
  </div>
}
