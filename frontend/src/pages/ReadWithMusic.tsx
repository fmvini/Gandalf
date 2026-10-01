import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useLocation } from 'react-router-dom'
import { ArrowRight, ArrowUpRight, AudioLines, BookOpen, CircleAlert, RotateCcw, Search } from 'lucide-react'
import { api, musicDestination, post, type BookItem, type MusicItem, type Recommendation } from '../lib/api'
import { duration } from '../lib/format'
import { Explanation } from '../components/Explanation'
import { ResultSkeleton } from '../components/ui/skeleton'
import { SavePlaylist, type ReadingSnapshot } from '../components/SavePlaylist'

type Mode = 'FOCUS' | 'IMMERSIVE' | 'CINEMATIC' | 'CALM' | 'CUSTOM'
const modes: { id: Mode; label: string; description: string }[] = [
  { id: 'FOCUS', label: 'Foco', description: 'Instrumental e discreta' },
  { id: 'IMMERSIVE', label: 'Imersiva', description: 'Dentro do universo do livro' },
  { id: 'CINEMATIC', label: 'Cinematográfica', description: 'Como uma trilha de filme' },
  { id: 'CALM', label: 'Calma', description: 'Leve e tranquila' },
  { id: 'CUSTOM', label: 'Do seu jeito', description: 'Você descreve a atmosfera' },
]

export default function ReadWithMusic() {
  const location = useLocation()
  const reading = (location.state as { reading?: ReadingSnapshot } | null)?.reading
  const initialQuery = (location.state as { query?: string } | null)?.query || ''
  const [bookQuery, setBookQuery] = useState(reading?.book.title || initialQuery)
  const [books, setBooks] = useState<BookItem[]>([])
  const [selectedBook, setSelectedBook] = useState<BookItem | null>(reading?.book || null)
  const [bookStatus, setBookStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle')
  const [mode, setMode] = useState<Mode>(reading?.settings?.mode || 'FOCUS')
  const [context, setContext] = useState(reading?.settings?.context || '')
  const [length, setLength] = useState(reading?.settings?.length || 60)
  const [vocals, setVocals] = useState(reading?.settings?.vocals || 'INSTRUMENTAL')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>(reading ? 'success' : 'idle')
  const [result, setResult] = useState<Recommendation<MusicItem> | null>(reading?.result || null)
  const [error, setError] = useState('')
  const searchController = useRef<AbortController | null>(null)
  const playlistController = useRef<AbortController | null>(null)

  useEffect(() => {
    if (selectedBook || bookQuery.trim().length < 2) {
      setBooks([])
      setBookStatus('idle')
      return
    }
    const controller = new AbortController()
    searchController.current = controller
    const timer = window.setTimeout(async () => {
      setBookStatus('loading')
      try {
        const data = await api<{ items: BookItem[] }>('/books/search?q=' + encodeURIComponent(bookQuery.trim()) + '&limit=6', { signal: controller.signal })
        if (!controller.signal.aborted) { setBooks(data.items || []); setBookStatus('ready') }
      } catch {
        if (!controller.signal.aborted) setBookStatus('error')
      }
    }, 320)
    return () => { window.clearTimeout(timer); controller.abort() }
  }, [bookQuery, selectedBook])

  useEffect(() => () => { searchController.current?.abort(); playlistController.current?.abort() }, [])

  function chooseBook(book: BookItem | null) {
    playlistController.current?.abort()
    setSelectedBook(book)
    setBookQuery(book?.title || '')
    setBooks([])
    setResult(null)
    setStatus('idle')
    setError('')
  }

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (!selectedBook || (mode === 'CUSTOM' && !context.trim())) return
    playlistController.current?.abort()
    const controller = new AbortController()
    playlistController.current = controller
    setStatus('loading')
    setError('')
    setResult(null)
    try {
      const data = await post<Recommendation<MusicItem>>('/recommendations/read-with-music', {
        book_id: selectedBook.id,
        mode,
        context: context.trim(),
        vocals: mode === 'FOCUS' ? 'INSTRUMENTAL' : vocals,
        target_duration_min: length,
      }, controller.signal)
      if (!controller.signal.aborted) { setResult(data); setStatus('success') }
    } catch (cause) {
      if (!controller.signal.aborted) { setError(cause instanceof Error ? cause.message : 'Não foi possível gerar a trilha.'); setStatus('error') }
    }
  }

  return <div className="reading-page">
    <section className="discovery-intro container"><div><span className="page-icon"><AudioLines size={25} /></span><h1>Uma trilha para entrar na história.</h1><p>Escolha o livro, conte como vai ler e deixe a música acompanhar as páginas.</p></div><div className="intro-art" aria-hidden="true"><img src="/images/affinity-atlas.png" alt="" /></div></section>
    <section className="reading-layout container">
      <form className="reading-form" onSubmit={submit}>
        <div className="form-group"><label htmlFor="book-search">Qual livro você está lendo?</label>{selectedBook ? <div className="selected-book"><span className="mini-cover">{selectedBook.cover_url ? <img src={selectedBook.cover_url} alt="" /> : <BookOpen size={22} />}</span><span><strong>{selectedBook.title}</strong><small>{selectedBook.authors?.join(', ')}</small></span><button type="button" onClick={() => chooseBook(null)}>Trocar</button></div> : <><div className="field-with-icon"><Search size={19} /><input id="book-search" value={bookQuery} onChange={event => setBookQuery(event.target.value)} placeholder="Busque pelo título do livro" autoComplete="off" aria-describedby="book-search-help" /></div><p id="book-search-help" className="field-help">Selecione um livro do catálogo para criar a trilha.</p>{bookStatus === 'loading' ? <p className="picker-status">Buscando livros…</p> : null}{bookStatus === 'error' ? <p className="picker-status">Não foi possível buscar livros. Verifique a conexão com a API.</p> : null}{bookStatus === 'ready' && !books.length ? <p className="picker-status">Nenhum livro encontrado. Tente outro título.</p> : null}{books.length ? <ul className="book-options" aria-label="Livros encontrados">{books.map(book => <li key={book.id}><button type="button" onClick={() => chooseBook(book)}><span className="mini-cover">{book.cover_url ? <img src={book.cover_url} alt="" /> : <BookOpen size={21} />}</span><span><strong>{book.title}</strong><small>{book.authors?.join(', ')}</small></span></button></li>)}</ul> : null}</>}</div>
        <fieldset className="form-group"><legend>Como quer ouvir?</legend><div className="mode-grid">{modes.map(item => <button key={item.id} type="button" className={mode === item.id ? 'reading-mode selected' : 'reading-mode'} onClick={() => setMode(item.id)} aria-pressed={mode === item.id}><strong>{item.label}</strong><span>{item.description}</span></button>)}</div></fieldset>
        <div className="reading-options"><div className="form-group"><label htmlFor="reading-context">Seu contexto <span>(opcional)</span></label><input id="reading-context" value={context} onChange={event => setContext(event.target.value)} placeholder="Ex.: antes de dormir, com chuva lá fora" maxLength={500} required={mode === 'CUSTOM'} />{mode === 'CUSTOM' ? <p className="field-help">Descreva a atmosfera para o modo Do seu jeito.</p> : null}</div><div className="form-group"><label htmlFor="reading-duration">Duração</label><select id="reading-duration" value={length} onChange={event => setLength(Number(event.target.value))}>{[30, 60, 90, 120].map(value => <option key={value} value={value}>{value} minutos</option>)}</select></div><div className="form-group"><label htmlFor="reading-vocals">Vocais</label><select id="reading-vocals" value={vocals} onChange={event => setVocals(event.target.value)} disabled={mode === 'FOCUS'}><option value="INSTRUMENTAL">Instrumental</option><option value="MINIMAL">Poucos vocais</option><option value="ANY">Tanto faz</option></select></div></div>
        <button className="button button-primary generate-button" type="submit" disabled={!selectedBook || status === 'loading'}>{status === 'loading' ? 'Criando trilha…' : 'Criar minha trilha'} <ArrowRight size={18} /></button>
      </form>
      <aside className="reading-aside"><div className="aside-illustration"><img src="/images/affinity-atlas.png" alt="" /></div><h2>Uma história, outra atmosfera.</h2><p>O modo de escuta muda a forma como a música acompanha o livro. Comece pelo que a leitura pede agora.</p></aside>
    </section>
    <section className="results-section container" aria-live="polite" aria-busy={status === 'loading'}>
      {status === 'success' && result?.meta?.hint ? <p className="field-help">{result.meta.hint}</p> : null}
      {status === 'success' && result && selectedBook ? <SavePlaylist reading={{ book: selectedBook, result, settings: { mode, context, length, vocals } }} /> : null}
      {status === 'success' && result?.playlist?.target_duration_ms ? <p className="duration-summary">{result.playlist.duration_estimated ? 'Duração estimada' : 'Duração das faixas'}: {Math.round(result.playlist.total_duration_ms / 60000)} min · Pedido: {result.playlist.target_duration_ms / 60000} min.{result.playlist.target_met === false ? ' Ainda faltam ' + Math.ceil((result.playlist.shortfall_ms ?? 0) / 60000) + ' min; não encontramos faixas compatíveis suficientes.' : ' Duração solicitada atendida.'}</p> : null}
      {status === 'loading' ? <><div className="status-panel"><div className="loading-track" aria-hidden="true"><span /></div><h2>Encontrando o clima do livro…</h2><p>Depois, organizamos faixas reais para sua leitura.</p><button type="button" className="text-button" onClick={() => { playlistController.current?.abort(); setStatus('idle') }}>Cancelar</button></div><ResultSkeleton kind="playlist" /></> : null}
      {status === 'error' ? <div className="status-panel error-panel"><CircleAlert size={30} /><h2>A trilha não ficou pronta.</h2><p>{error}</p><button className="button button-secondary" type="button" onClick={() => setStatus('idle')}><RotateCcw size={17} /> Revisar pedido</button></div> : null}
      {status === 'success' && result ? <><div className="results-title"><div><span className="results-kicker">Sua trilha de leitura</span><h2>{selectedBook?.title}</h2></div><span>{result.playlist?.tracks_count ?? result.items.length} {(result.playlist?.tracks_count ?? result.items.length) === 1 ? 'faixa' : 'faixas'} · {result.playlist ? Math.round(result.playlist.total_duration_ms / 60000) : length} min</span></div>{result.items.length ? <ol className="playlist-list">{result.items.map((ranked, index) => { const track = ranked.item; const destination = musicDestination(track); return <li key={(result.recommendation_id || "") + track.id}><span className="track-number">{String(index + 1).padStart(2, '0')}</span><div className="playlist-track-main"><strong>{track.title}</strong><span>{track.artist}</span><Explanation recommendationId={result.recommendation_id} itemId={track.id} /></div><span className="track-duration">{duration(track.duration_ms)}</span><a href={destination.href} target="_blank" rel="noopener noreferrer" aria-label={destination.label + ': ' + track.title}><ArrowUpRight size={19} /></a></li> })}</ol> : <div className="status-panel"><h2>Nenhuma faixa encontrada.</h2><p>Tente outro modo ou amplie o contexto da sua leitura.</p></div>}</> : null}
    </section>
  </div>
}
