import { useState, type FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ArrowRight, ArrowUpRight, AudioLines, BookOpen, Headphones, Search } from 'lucide-react'

type Mode = 'music' | 'books' | 'read-with-music'
const modes: { id: Mode; label: string; placeholder: string }[] = [
  { id: 'music', label: 'Música', placeholder: 'Descreva a música que você procura' },
  { id: 'books', label: 'Livros', placeholder: 'Descreva o livro que você procura' },
  { id: 'read-with-music', label: 'Trilha para leitura', placeholder: 'Que livro você está lendo?' },
]

export default function Home() {
  const [mode, setMode] = useState<Mode>('music')
  const [query, setQuery] = useState('')
  const navigate = useNavigate()

  function submit(event: FormEvent) {
    event.preventDefault()
    if (query.trim().length < 3) return
    navigate('/' + mode, { state: { query: query.trim() } })
  }

  return (
    <>
      <section className="home-hero container">
        <div className="hero-copy">
          <h1>Encontre o que combina com o <em>seu momento.</em></h1>
          <p>Diga o que você está sentindo, o que quer viver ou o que te interessa. O Gandalf transforma seu pedido em caminhos para música e livros.</p>
          <form className="hero-search" onSubmit={submit}>
            <label className="sr-only" htmlFor="home-query">Descreva o que você procura</label>
            <div className="hero-input-wrap">
              <Search size={22} aria-hidden="true" />
              <input id="home-query" value={query} onChange={event => setQuery(event.target.value)} placeholder={modes.find(item => item.id === mode)?.placeholder} maxLength={1000} minLength={3} required />
              <button className="hero-submit" type="submit" aria-label="Explorar pedido"><ArrowRight size={22} /></button>
            </div>
            <div className="mode-tabs" role="group" aria-label="O que você procura?">
              {modes.map(item => <button key={item.id} type="button" className={mode === item.id ? 'mode-tab selected' : 'mode-tab'} onClick={() => setMode(item.id)} aria-pressed={mode === item.id}>{item.id === 'music' ? <Headphones size={17} /> : item.id === 'books' ? <BookOpen size={17} /> : <AudioLines size={17} />}{item.label}</button>)}
            </div>
          </form>
        </div>
        <div className="atlas-visual" aria-label="Mapa ilustrado de sensações como calmo, nostálgico e imersivo">
          <img src="/images/affinity-atlas.png" alt="" />
          <span className="atlas-label atlas-calm">calmo</span>
          <span className="atlas-label atlas-nostalgic">nostálgico</span>
          <span className="atlas-label atlas-immersive">imersivo</span>
          <span className="atlas-label atlas-reflective">reflexivo</span>
          <span className="atlas-label atlas-curious">curioso</span>
          <span className="atlas-label atlas-contemplative">contemplativo</span>
        </div>
      </section>
      <section className="paths container" aria-labelledby="paths-heading">
        <h2 id="paths-heading">Uma busca. Novos caminhos.</h2>
        <div className="path-list">
          <Link to="/music" className="path-item"><Headphones size={24} /><span><strong>Descubra músicas</strong><small>Uma atmosfera, uma lembrança, uma faixa de referência.</small></span><ArrowUpRight size={23} /></Link>
          <Link to="/books" className="path-item"><BookOpen size={24} /><span><strong>Encontre seu próximo livro</strong><small>Fale sobre o tipo de história que você quer viver.</small></span><ArrowUpRight size={23} /></Link>
          <Link to="/read-with-music" className="path-item"><AudioLines size={24} /><span><strong>Leia com música</strong><small>Crie uma trilha para acompanhar o livro em suas mãos.</small></span><ArrowUpRight size={23} /></Link>
        </div>
      </section>
      <section className="closing container"><p>Para a próxima página</p><h2>Talvez seu novo livro favorito. Talvez a música certa para a história.</h2><Link to="/read-with-music">Criar uma trilha de leitura <ArrowUpRight size={18} /></Link></section>
    </>
  )
}
