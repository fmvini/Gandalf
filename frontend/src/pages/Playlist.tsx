import { useEffect, useRef, useState } from 'react'
import { Link, Navigate, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, ArrowUpRight, Trash2 } from 'lucide-react'
import { musicDestination } from '../lib/api'
import { duration } from '../lib/format'
import { useSession } from '../lib/useSession'
import { playlistDuration, playlistError, playlists, type PlaylistDetail } from '../lib/playlists'

export default function Playlist() {
  const { user, expired } = useSession()
  const { id = '' } = useParams()
  if (!user) return <Navigate to="/login" replace state={{ notice: expired ? 'Sua sessão terminou. Entre novamente para acessar suas playlists.' : undefined }} />
  return <PlaylistContent key={user.id + id} id={id} />
}

function PlaylistContent({ id }: { id: string }) {
  const navigate = useNavigate()
  const [data, setData] = useState<PlaylistDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [confirming, setConfirming] = useState(false)
  const [removing, setRemoving] = useState(false)
  const removeController = useRef<AbortController | null>(null)
  const errorPanel = useRef<HTMLDivElement | null>(null)
  const confirmButton = useRef<HTMLButtonElement | null>(null)
  const deleteButton = useRef<HTMLButtonElement | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError('')
    playlists.detail(id, controller.signal).then(result => { if (!controller.signal.aborted) setData(result) })
      .catch(cause => { if (!controller.signal.aborted) setError(playlistError(cause)) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [id, attempt])
  useEffect(() => () => removeController.current?.abort(), [])
  useEffect(() => { if (error) errorPanel.current?.focus() }, [error])
  useEffect(() => { if (confirming) confirmButton.current?.focus() }, [confirming])

  async function remove() {
    if (removing) return
    const controller = new AbortController()
    removeController.current = controller
    setRemoving(true)
    setError('')
    try {
      await playlists.remove(id, controller.signal)
      if (!controller.signal.aborted) navigate('/account', { replace: true, state: { notice: 'Playlist excluída da sua conta.' } })
    } catch (cause) { if (!controller.signal.aborted) setError(playlistError(cause)) }
    finally { if (!controller.signal.aborted) setRemoving(false) }
  }

  return <section className="playlist-page container" aria-busy={loading || removing}>
    <Link className="account-explore" to="/account"><ArrowLeft size={17} aria-hidden="true" /> Voltar às playlists</Link>
    {loading ? <p role="status">Buscando playlist…</p> : null}
    {error ? <div className="account-error" role="alert" tabIndex={-1} ref={errorPanel}><p>{error}</p>{!data ? <button className="text-button" type="button" onClick={() => setAttempt(value => value + 1)}>Tentar novamente</button> : null}</div> : null}
    {data ? <><div className="library-heading"><div><h1>{data.name}</h1><p>{playlistDuration(data)}</p>{data.description ? <p>{data.description}</p> : null}</div><button ref={deleteButton} className="button button-secondary" type="button" disabled={removing || confirming} onClick={() => setConfirming(true)}><Trash2 size={17} aria-hidden="true" /> Excluir playlist</button></div>
      {confirming ? <div className="delete-confirmation"><p>Excluir <strong>{data.name}</strong> da sua conta? Esta ação não pode ser desfeita.</p><div className="account-controls"><button ref={confirmButton} className="button button-secondary" type="button" disabled={removing} onClick={() => void remove()}>{removing ? 'Excluindo…' : 'Confirmar exclusão'}</button><button className="text-button" type="button" disabled={removing} onClick={() => { setConfirming(false); window.setTimeout(() => deleteButton.current?.focus(), 0) }}>Manter playlist</button></div></div> : null}
      <ol className="playlist-list">{data.tracks.map(track => { const destination = musicDestination(track.item); return <li key={track.position}><span className="track-number">{String(track.position).padStart(2, '0')}</span><div><strong>{track.item.title}</strong><span>{track.item.artist}</span></div><span className="track-duration">{duration(track.item.duration_ms) || '—'}</span><a href={destination.href} target="_blank" rel="noopener noreferrer" aria-label={destination.label + ': ' + track.item.title}><ArrowUpRight size={19} /></a></li> })}</ol>
      {data.duration_estimated ? <p className="field-help">O total inclui estimativas de 5 minutos para faixas sem duração informada. As músicas abrem em fontes ou buscas externas.</p> : <p className="field-help">Duração informada pelas fontes das faixas. As músicas abrem em fontes ou buscas externas.</p>}
    </> : null}
  </section>
}
