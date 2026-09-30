import { useState, type FormEvent } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { ArrowRight, ArrowUpRight, AudioLines, BookOpen, Headphones, Search } from 'lucide-react'
import { motion, useReducedMotion } from 'motion/react'
import { AnimatedChoices } from '../components/ui/animated-tabs'
import { BookCarousel } from '../components/ui/three-d-carousel'

type Mode = 'music' | 'books' | 'read-with-music'
const MotionLink = motion.create(Link)
const arrival = { duration: 0.55, ease: [0.16, 1, 0.3, 1] as const }
const modes: { id: Mode; label: string; placeholder: string }[] = [
  { id: 'music', label: 'Música', placeholder: 'Descreva a música que você procura' },
  { id: 'books', label: 'Livros', placeholder: 'Descreva o livro que você procura' },
  { id: 'read-with-music', label: 'Trilha para leitura', placeholder: 'Que livro você está lendo?' },
]
const suggestions: Record<Mode, string[]> = {
  music: ['Instrumentais para focar', 'Uma atmosfera de ficção científica'],
  books: ['Fantasia sem romance', 'Uma história acolhedora'],
  'read-with-music': ['Duna', 'O Hobbit'],
}

export default function Home() {
  const [mode, setMode] = useState<Mode>('music')
  const [query, setQuery] = useState('')
  const navigate = useNavigate()
  const reduced = useReducedMotion()

  function submit(event: FormEvent) {
    event.preventDefault()
    if (query.trim().length < 3) return
    navigate('/' + mode, { state: { query: query.trim() } })
  }

  return (
    <>
      <section className="home-hero container">
        <div className="hero-copy">
          <motion.h1 initial={reduced ? false : { opacity: 0.75, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={arrival}>Encontre o que combina com o <em>seu momento.</em></motion.h1>
          <motion.p initial={reduced ? false : { opacity: 0.75, y: 12 }} animate={{ opacity: 1, y: 0 }} transition={{ ...arrival, delay: 0.06 }}>Músicas, livros e trilhas de leitura. Comece pelo que você quer sentir.</motion.p>
          <motion.form className="hero-search" onSubmit={submit} initial={reduced ? false : { opacity: 0.8, y: 10 }} animate={{ opacity: 1, y: 0 }} transition={{ ...arrival, delay: 0.12 }}>
            <label className="sr-only" htmlFor="home-query">Descreva o que você procura</label>
            <div className="hero-input-wrap">
              <Search size={22} aria-hidden="true" />
              <input id="home-query" value={query} onChange={event => setQuery(event.target.value)} placeholder={modes.find(item => item.id === mode)?.placeholder} maxLength={1000} minLength={3} required />
              <button className="hero-submit" type="submit" aria-label="Explorar pedido"><ArrowRight size={22} /></button>
            </div>
            <AnimatedChoices items={modes.map(item => ({ ...item, icon: item.id === 'music' ? <Headphones size={17} /> : item.id === 'books' ? <BookOpen size={17} /> : <AudioLines size={17} /> }))} value={mode} onChange={setMode} label="O que você procura?" />
          </motion.form>
          <div className="hero-suggestions"><span>Experimente</span>{suggestions[mode].map(text => <button key={text} type="button" onClick={() => navigate('/' + mode, { state: { query: text } })}>{text}<ArrowUpRight size={14} /></button>)}</div>
        </div>
        <BookCarousel />
      </section>
      <section className="paths container" aria-labelledby="paths-heading">
        <h2 id="paths-heading">Uma busca. Novos caminhos.</h2>
        <motion.div className="path-list" initial={reduced ? false : 'rest'} whileInView="visible" viewport={{ once: true, amount: 0.2 }} transition={{ staggerChildren: 0.07 }}>
          {[
            { to: '/music', icon: <Headphones size={24} />, title: 'Descubra músicas', description: 'Uma atmosfera, uma lembrança, uma faixa de referência.' },
            { to: '/books', icon: <BookOpen size={24} />, title: 'Encontre seu próximo livro', description: 'Fale sobre o tipo de história que você quer viver.' },
            { to: '/read-with-music', icon: <AudioLines size={24} />, title: 'Leia com música', description: 'Crie uma trilha para acompanhar o livro em suas mãos.' },
          ].map(item => <MotionLink key={item.to} to={item.to} className="path-item" variants={{ rest: { opacity: 0.65, y: 14 }, visible: { opacity: 1, y: 0 } }} transition={reduced ? { duration: 0 } : arrival}>{item.icon}<span><strong>{item.title}</strong><small>{item.description}</small></span><ArrowUpRight size={23} /></MotionLink>)}
        </motion.div>
      </section>
      <section className="reading-invitation container">
        <motion.div className="invitation-cover" initial={reduced ? false : { rotate: 7, y: 16 }} whileInView={{ rotate: 0, y: 0 }} viewport={{ once: true, amount: 0.4 }} transition={arrival}><img src="/images/covers/hobbit.jpg" alt="Capa de O Hobbit, edição em inglês" width="165" height="250" loading="lazy" /></motion.div>
        <div><h2>Uma história.<br />Outra atmosfera.</h2><p>Do silêncio da concentração à intensidade de uma aventura. Escolha como a música acompanha sua leitura.</p><Link to="/read-with-music" state={{ query: 'O Hobbit' }} className="button button-primary">Criar uma trilha de leitura <ArrowUpRight size={18} /></Link></div>
        <div className="invitation-modes" aria-label="Modos de leitura"><span><Headphones size={18} /> Foco</span><span><AudioLines size={18} /> Imersiva</span><span><BookOpen size={18} /> Cinematográfica</span></div>
      </section>
    </>
  )
}
