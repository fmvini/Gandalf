import { useEffect, useState } from 'react'
import { Link, NavLink, Route, Routes, useLocation } from 'react-router-dom'
import { ArrowUpRight, Menu, Moon, Sun, UserRound, X } from 'lucide-react'
import Home from './pages/Home'
import Discovery from './pages/Discovery'
import ReadWithMusic from './pages/ReadWithMusic'
import Authentication from './pages/Authentication'
import Account from './pages/Account'
import Playlist from './pages/Playlist'
import { useSession } from './lib/useSession'

const links = [
  { to: '/music', label: 'Música' },
  { to: '/books', label: 'Livros' },
  { to: '/read-with-music', label: 'Ler com música' },
]

type Theme = 'light' | 'dark'

function getInitialTheme(): Theme {
  const saved = localStorage.getItem('gandalf-theme')
  return saved === 'light' ? 'light' : 'dark'
}

export default function App() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme)
  const [menuOpen, setMenuOpen] = useState(false)
  const location = useLocation()
  const { user } = useSession()

  useEffect(() => {
    document.documentElement.dataset.theme = theme
    localStorage.setItem('gandalf-theme', theme)
  }, [theme])

  useEffect(() => {
    setMenuOpen(false)
    window.scrollTo(0, 0)
  }, [location.pathname])

  return (
    <>
      <a className="skip-link" href="#main">Pular para o conteúdo</a>
      <header className="site-header">
        <div className="header-inner container">
          <Link className="wordmark" to="/" aria-label="Gandalf, início">gandalf<span>.</span></Link>
          <nav className={menuOpen ? 'primary-nav is-open' : 'primary-nav'} aria-label="Navegação principal">
            {links.map(link => <NavLink key={link.to} to={link.to} className={({ isActive }) => isActive ? 'nav-link active' : 'nav-link'}>{link.label}</NavLink>)}
          </nav>
          <div className="header-actions">
            <Link className="account-link" to={user ? '/account' : '/login'} aria-label={user ? 'Minha conta' : 'Entrar na conta'}><UserRound size={18} aria-hidden="true" /><span>{user ? 'Minha conta' : 'Entrar'}</span></Link>
            <button className="icon-button theme-button" type="button" onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')} aria-label={theme === 'light' ? 'Ativar tema escuro' : 'Ativar tema claro'} title={theme === 'light' ? 'Tema escuro' : 'Tema claro'}>
              {theme === 'light' ? <Moon size={19} /> : <Sun size={19} />}
            </button>
            <Link className="header-cta" to="/music">Explorar <ArrowUpRight size={17} /></Link>
            <button className="icon-button menu-button" type="button" onClick={() => setMenuOpen(!menuOpen)} aria-label={menuOpen ? 'Fechar menu' : 'Abrir menu'} aria-expanded={menuOpen}>
              {menuOpen ? <X size={22} /> : <Menu size={22} />}
            </button>
          </div>
        </div>
      </header>
      <main id="main">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/music" element={<Discovery key="music" kind="music" />} />
          <Route path="/books" element={<Discovery key="books" kind="books" />} />
          <Route path="/read-with-music" element={<ReadWithMusic />} />
          <Route path="/login" element={<Authentication key="login" mode="login" />} />
          <Route path="/register" element={<Authentication key="register" mode="register" />} />
          <Route path="/account" element={<Account />} />
          <Route path="/account/playlists/:id" element={<Playlist />} />
          <Route path="*" element={<section className="not-found container"><h1>Esse caminho não existe.</h1><p>Volte ao início para encontrar música, livros ou uma trilha para ler.</p><Link className="button button-primary" to="/">Voltar ao início <ArrowUpRight size={18} /></Link></section>} />
        </Routes>
      </main>
      <footer className="site-footer">
        <div className="container footer-inner"><span className="footer-brand">gandalf<span>.</span></span><p>Para descobrir o que ouvir, ler e sentir depois.</p><span>Feito para começar pela curiosidade.</span></div>
      </footer>
    </>
  )
}
