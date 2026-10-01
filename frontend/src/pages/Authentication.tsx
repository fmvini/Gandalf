import { useEffect, useRef, useState, type FormEvent } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, Eye, EyeOff } from 'lucide-react'
import { authSession } from '../lib/auth'
import { useSession } from '../lib/useSession'

export default function Authentication({ mode }: { mode: 'login' | 'register' }) {
  const registration = mode === 'register'
  const navigate = useNavigate()
  const location = useLocation()
  const session = useSession()
  const initial = location.state as { email?: string; notice?: string } | null
  const [email, setEmail] = useState(initial?.email || '')
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [confirmation, setConfirmation] = useState('')
  const [visible, setVisible] = useState(false)
  const [pending, setPending] = useState(false)
  const [error, setError] = useState('')
  const controller = useRef<AbortController | null>(null)
  const errorPanel = useRef<HTMLDivElement | null>(null)

  useEffect(() => () => controller.current?.abort(), [])
  useEffect(() => { if (error) errorPanel.current?.focus() }, [error])

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (pending) return
    if (registration && password !== confirmation) {
      setError('As senhas precisam ser iguais. Confira a confirmação.')
      return
    }
    const next = new AbortController()
    controller.current = next
    setPending(true)
    setError('')
    try {
      if (registration) {
        await authSession.register(email, username, password, next.signal)
        if (!next.signal.aborted) navigate('/login', { replace: true, state: { email: email.trim(), notice: 'Conta criada. Entre com seu e-mail e senha.' } })
      } else {
        await authSession.signIn(email, password, next.signal)
        if (!next.signal.aborted) navigate('/account', { replace: true })
      }
    } catch (cause) {
      if (!next.signal.aborted) setError(cause instanceof Error ? cause.message : 'Não foi possível concluir. Tente novamente.')
    } finally {
      if (!next.signal.aborted) setPending(false)
    }
  }

  if (session.user) return <Navigate to="/account" replace />
  const notice = initial?.notice || (session.expired ? 'Sua sessão terminou. Entre novamente para acessar sua conta.' : '')
  return <section className="account-page container" aria-labelledby="auth-title">
    <div className="account-intro"><h1 id="auth-title">{registration ? 'Crie sua conta.' : 'Entre no Gandalf.'}</h1><p>{registration ? 'Escolha um nome de usuário e cadastre seu acesso.' : 'Use seu e-mail e senha para acessar sua conta.'}</p><Link className="account-explore" to="/music">Continuar explorando sem conta <ArrowRight size={17} aria-hidden="true" /></Link></div>
    <div className="account-panel">
      {notice && !registration ? <p className="account-notice" role="status">{notice}</p> : null}
      <form className="account-form" onSubmit={submit} aria-busy={pending}>
        {error ? <div className="account-error" role="alert" tabIndex={-1} ref={errorPanel}>{error}</div> : null}
        <div className="form-group"><label htmlFor="auth-email">E-mail</label><input id="auth-email" type="email" autoComplete="email" autoCapitalize="none" spellCheck={false} value={email} onChange={event => setEmail(event.target.value)} maxLength={320} required disabled={pending} /></div>
        {registration ? <div className="form-group"><label htmlFor="auth-username">Nome de usuário</label><input id="auth-username" autoComplete="username" autoCapitalize="none" spellCheck={false} value={username} onChange={event => setUsername(event.target.value)} minLength={3} maxLength={32} pattern="(?:[A-Za-z0-9_.]|-)+" required disabled={pending} aria-describedby="username-help" /><p id="username-help" className="field-help">De 3 a 32 caracteres: letras, números, ponto, hífen ou sublinhado.</p></div> : null}
        <div className="form-group"><label htmlFor="auth-password">Senha</label><div className="password-field"><input id="auth-password" type={visible ? 'text' : 'password'} autoComplete={registration ? 'new-password' : 'current-password'} value={password} onChange={event => setPassword(event.target.value)} minLength={registration ? 10 : 1} maxLength={128} required disabled={pending} aria-describedby={registration ? 'password-help' : undefined} /><button type="button" className="icon-button" aria-label={visible ? 'Ocultar senha' : 'Mostrar senha'} aria-pressed={visible} onClick={() => setVisible(!visible)}>{visible ? <EyeOff size={19} aria-hidden="true" /> : <Eye size={19} aria-hidden="true" />}</button></div>{registration ? <p id="password-help" className="field-help">Use de 10 a 128 caracteres. Prefira uma frase longa que você consiga lembrar.</p> : null}</div>
        {registration ? <div className="form-group"><label htmlFor="auth-confirmation">Confirme a senha</label><input id="auth-confirmation" type={visible ? 'text' : 'password'} autoComplete="new-password" value={confirmation} onChange={event => setConfirmation(event.target.value)} minLength={10} maxLength={128} required disabled={pending} /></div> : null}
        <button className="button button-primary" type="submit" disabled={pending}>{pending ? (registration ? 'Criando conta…' : 'Entrando…') : (registration ? 'Criar conta' : 'Entrar')} <ArrowRight size={18} aria-hidden="true" /></button>
      </form>
      <p className="account-alternate">{registration ? 'Já tem uma conta?' : 'Primeira vez por aqui?'} <Link to={registration ? '/login' : '/register'}>{registration ? 'Entrar' : 'Criar conta'}</Link></p>
      <p className="account-session-note">Sua sessão dura enquanto esta página estiver aberta. Ao recarregar ou fechar, entre novamente.</p>
    </div>
  </section>
}
