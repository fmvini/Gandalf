import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Bookmark, BookmarkCheck } from 'lucide-react'
import { useSession } from '../lib/useSession'
import { favoriteError, favorites, type AuthReturnTo, type FavoriteType } from '../lib/favorites'

type Controls = {
  signedIn: boolean; loading: boolean; saved: Record<string, string>
  busy: Record<string, boolean>; errors: Record<string, string>; notices: Record<string, string>
  returnTo: AuthReturnTo; toggle: (id: string) => void
}
const FavoriteContext = createContext<Controls | null>(null)
type Props = { type: FavoriteType; itemIds: string[]; recommendationId: string | null; returnTo: AuthReturnTo; children: ReactNode }

export function FavoriteControls({ children, ...props }: Props) {
  const { user } = useSession()
  if (!props.recommendationId || !props.itemIds.length) return <>{children}</>
  return <ControlsContent key={(user?.id || 'anonymous') + props.recommendationId + props.itemIds.join(',')} {...props} signedIn={!!user}>{children}</ControlsContent>
}

function ControlsContent({ type, itemIds, recommendationId, returnTo, children, signedIn }: Props & { signedIn: boolean }) {
  const [saved, setSaved] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(signedIn)
  const [statusError, setStatusError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const [busy, setBusy] = useState<Record<string, boolean>>({})
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [notices, setNotices] = useState<Record<string, string>>({})
  const mutations = useRef(new Map<string, AbortController>())
  const ids = itemIds.join(',')
  useEffect(() => {
    if (!signedIn) return
    const controller = new AbortController()
    setLoading(true)
    setStatusError('')
    favorites.status(type, ids.split(','), controller.signal)
      .then(data => { if (!controller.signal.aborted) setSaved(data.favorites) })
      .catch(cause => { if (!controller.signal.aborted) setStatusError(favoriteError(cause)) })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
  }, [signedIn, type, ids, attempt])
  useEffect(() => {
    const pending = mutations.current
    return () => { pending.forEach(controller => controller.abort()); pending.clear() }
  }, [])

  async function toggle(id: string) {
    if (!recommendationId || loading || statusError || mutations.current.has(id)) return
    const controller = new AbortController()
    mutations.current.set(id, controller)
    setBusy(current => ({ ...current, [id]: true }))
    setErrors(current => ({ ...current, [id]: '' }))
    setNotices(current => ({ ...current, [id]: '' }))
    try {
      const existing = saved[id]
      const result = existing ? await favorites.remove(existing, controller.signal) : await favorites.save(recommendationId, id, controller.signal)
      if (controller.signal.aborted) return
      setSaved(current => {
        const next = { ...current }
        if (existing) delete next[id]
        else if (result) next[id] = result.id
        return next
      })
      setNotices(current => ({ ...current, [id]: existing ? 'Removido dos favoritos.' : 'Salvo nos seus favoritos.' }))
    } catch (cause) { if (!controller.signal.aborted) setErrors(current => ({ ...current, [id]: favoriteError(cause) })) }
    finally {
      mutations.current.delete(id)
      if (!controller.signal.aborted) setBusy(current => ({ ...current, [id]: false }))
    }
  }

  return <FavoriteContext.Provider value={{ signedIn, loading: loading || !!statusError, saved, busy, errors, notices, returnTo, toggle }}>
    {signedIn ? <div className="favorites-status" aria-live="polite">{loading ? <p className="field-help">Consultando seus favoritos…</p> : null}{statusError ? <div className="account-error" role="alert"><p>{statusError}</p><button className="text-button" type="button" onClick={() => setAttempt(value => value + 1)}>Consultar favoritos novamente</button></div> : null}</div> : null}
    {children}
  </FavoriteContext.Provider>
}

export function FavoriteButton({ itemId, title }: { itemId: string; title: string }) {
  const controls = useContext(FavoriteContext)
  const [inviting, setInviting] = useState(false)
  if (!controls) return null
  const saved = !!controls.saved[itemId]
  return <div className="favorite-control">
    <button className="text-button favorite-button" type="button" aria-label={(saved ? 'Remover dos favoritos: ' : 'Salvar nos favoritos: ') + title} aria-pressed={saved} disabled={controls.loading || controls.busy[itemId]} onClick={() => controls.signedIn ? controls.toggle(itemId) : setInviting(true)}>{saved ? <BookmarkCheck size={16} aria-hidden="true" /> : <Bookmark size={16} aria-hidden="true" />}{controls.busy[itemId] ? 'Atualizando…' : saved ? 'Salvo' : 'Salvar favorito'}</button>
    {inviting && !controls.signedIn ? <p className="favorite-message">Entre para guardar este item na sua conta. <Link to="/login" state={{ notice: 'Entre para salvar seu favorito. Sua seleção estará aqui quando você voltar.', returnTo: controls.returnTo }}>Entrar para salvar</Link></p> : null}
    {controls.errors[itemId] ? <p className="favorite-message favorite-error" role="alert">{controls.errors[itemId]}</p> : null}
    {controls.notices[itemId] ? <p className="favorite-message" role="status">{controls.notices[itemId]}</p> : null}
  </div>
}
