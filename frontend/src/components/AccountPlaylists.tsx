import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, RefreshCw } from 'lucide-react'
import { playlistDuration, playlistError, playlists, type PlaylistPage } from '../lib/playlists'

export function AccountPlaylists({ leaving }: { leaving: boolean }) {
  const [offset, setOffset] = useState(0)
  const [attempt, setAttempt] = useState(0)
  const [data, setData] = useState<PlaylistPage | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  useEffect(() => {
    if (leaving) return
    const controller = new AbortController()
    setLoading(true)
    setData(null)
    setError('')
    playlists.list(offset, controller.signal).then(page => {
      if (controller.signal.aborted) return
      if (!page.items.length && offset > 0) setOffset(Math.max(0, offset - 10))
      else setData(page)
    }).catch(cause => { if (!controller.signal.aborted) setError(playlistError(cause)) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [offset, attempt, leaving])

  return <section className="account-playlists" aria-labelledby="playlists-title" aria-busy={loading}>
    <div className="library-heading"><div><h2 id="playlists-title">Suas playlists</h2><p>Trilhas que você guardou para acompanhar as próximas páginas.</p></div><button className="text-button" type="button" disabled={loading || leaving} onClick={() => setAttempt(value => value + 1)}><RefreshCw size={16} aria-hidden="true" /> Atualizar playlists</button></div>
    <div aria-live="polite">
      {loading ? <p className="field-help">Buscando suas playlists…</p> : null}
      {error ? <div className="account-error" role="alert"><p>{error}</p><button className="text-button" type="button" disabled={leaving} onClick={() => setAttempt(value => value + 1)}>Tentar novamente</button></div> : null}
      {data && !data.total ? <div className="library-empty"><h3>Sua próxima leitura pode ter uma trilha.</h3><p>Crie uma seleção de músicas para um livro e salve aqui.</p><Link className="account-explore" to="/read-with-music">Criar uma trilha <ArrowRight size={17} aria-hidden="true" /></Link></div> : null}
      {data?.items.length ? <><ul className="saved-playlists">{data.items.map(item => <li key={item.id}><Link to={'/account/playlists/' + item.id}><span><strong>{item.name}</strong><small>{playlistDuration(item)}</small></span><ArrowRight size={19} aria-hidden="true" /></Link></li>)}</ul><nav className="playlist-pagination" aria-label="Páginas de playlists"><button className="button button-secondary" type="button" disabled={!offset || leaving} onClick={() => setOffset(value => Math.max(0, value - 10))}>Anteriores</button><span>{offset + 1}–{offset + data.items.length} de {data.total}</span><button className="button button-secondary" type="button" disabled={offset + data.items.length >= data.total || leaving} onClick={() => setOffset(value => value + 10)}>Próximas</button></nav></> : null}
    </div>
  </section>
}
