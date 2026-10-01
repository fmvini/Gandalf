import { useEffect, useRef, useState } from 'react'
import { Link, Navigate, useNavigate } from 'react-router-dom'
import { ArrowRight, LogOut, RefreshCw } from 'lucide-react'
import { authSession } from '../lib/auth'
import { useSession } from '../lib/useSession'

export default function Account() {
  const { user, expired } = useSession()
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [leaving, setLeaving] = useState(false)
  const [error, setError] = useState('')
  const [attempt, setAttempt] = useState(0)
  const errorPanel = useRef<HTMLDivElement | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    if (!user) return
    setLoading(true)
    setError('')
    authSession.loadProfile(controller.signal)
      .catch(cause => { if (!controller.signal.aborted) setError(cause instanceof Error ? cause.message : 'Não foi possível atualizar sua conta.') })
      .finally(() => { if (!controller.signal.aborted) setLoading(false) })
    return () => controller.abort()
    // The store publishes profile updates; only a new account or retry reloads it.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user?.id, attempt])
  useEffect(() => { if (error) errorPanel.current?.focus() }, [error])

  async function leave() {
    if (leaving) return
    setLeaving(true)
    setError('')
    try {
      await authSession.signOut()
      navigate('/login', { replace: true, state: { notice: 'Você saiu da sua conta.' } })
    } catch {
      setError('Não foi possível encerrar a sessão. Verifique sua conexão e tente sair novamente.')
    } finally { setLeaving(false) }
  }

  if (!user) return <Navigate to="/login" replace state={{ notice: expired ? 'Sua sessão terminou. Entre novamente para acessar sua conta.' : undefined }} />
  return <section className="account-page container" aria-labelledby="account-title">
    <div className="account-intro"><h1 id="account-title">Sua conta.</h1><p>Você está conectado como <strong>{user.username}</strong>.</p><Link className="account-explore" to="/music">Explorar sugestões <ArrowRight size={17} aria-hidden="true" /></Link></div>
    <div className="account-panel">
      {error ? <div className="account-error" role="alert" tabIndex={-1} ref={errorPanel}>{error}</div> : null}
      <div aria-busy={loading}><h2>Dados da conta</h2><dl className="account-details"><div><dt>Nome de usuário</dt><dd>{user.username}</dd></div><div><dt>E-mail</dt><dd>{user.email}</dd></div><div><dt>Conta criada em</dt><dd>{new Intl.DateTimeFormat('pt-BR', { dateStyle: 'long' }).format(new Date(user.created_at))}</dd></div></dl></div>
      <div className="account-controls"><button type="button" className="text-button" disabled={loading || leaving} onClick={() => setAttempt(current => current + 1)}><RefreshCw size={16} aria-hidden="true" /> {loading ? 'Atualizando conta…' : 'Atualizar dados'}</button><button type="button" className="button button-secondary" disabled={leaving} onClick={() => void leave()}><LogOut size={17} aria-hidden="true" /> {leaving ? 'Saindo…' : 'Sair da conta'}</button></div>
      <p className="account-session-note">Ao recarregar ou fechar esta página, você precisará entrar novamente. Seus dados de cadastro permanecem na conta.</p>
    </div>
  </section>
}
