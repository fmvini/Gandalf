import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useLocation } from 'react-router-dom'
import { ArrowRight, ArrowUpRight, BookOpen, CircleAlert, Headphones, RotateCcw, Search, SlidersHorizontal } from 'lucide-react'
import { api, musicDestination, post, type BookItem, type MusicItem, type RankedItem, type Recommendation } from '../lib/api'
import { duration, intentWords } from '../lib/format'
import { localBookCover } from '../lib/showcase'

type Kind = 'music' | 'books'
type Data = Recommendation<MusicItem> | Recommendation<BookItem>

const config = {
  music: {
    title: 'Encontre a música certa para agora.',
    description: 'Conte como você quer se sentir, o que está fazendo ou cite uma música que já ama.',
    placeholder: 'Ex.: músicas atmosféricas e calmas para estudar, parecidas com No Surprises',
    examples: ['Algo calmo para uma noite chuvosa', 'Faixas instrumentais para manter o foco'],
    endpoint: '/recommendations/music',
  },
  books: {
    title: 'Sua próxima história começa aqui.',
    description: 'Descreva o mundo, o ritmo e os personagens que você tem vontade de encontrar.',
    placeholder: 'Ex.: fantasia com um mundo profundo, exploração e pouco romance',
    examples: ['Fantasia com construção de mundo profunda', 'Uma história intimista e esperançosa'],
    endpoint: '/recommendations/books',
  },
} as const

function parseError(error: unknown) {
  return error instanceof Error ? error.message : 'Algo deu errado. Tente novamente.'
}

function ResultImage({ url, title, type }: { url?: string | null; title: string; type: Kind }) {
  const [failed, setFailed] = useState(false)
  return <div className={'result-image ' + type}>{url && !failed ? <img src={url} alt={type === 'music' ? 'Arte de ' + title : 'Capa de ' + title} loading="lazy" onError={() => setFailed(true)} /> : <span aria-hidden="true">{type === 'music' ? <Headphones size={31} /> : <BookOpen size={31} />}</span>}</div>
}

function Why({ recommendationId, itemId }: { recommendationId: string | null; itemId: string }) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle')
  const [explanation, setExplanation] = useState('')
  async function load() {
    if (!recommendationId || status !== 'idle') return
    setStatus('loading')
    try {
      const result = await api<{ text: string }>('/recommendations/' + encodeURIComponent(recommendationId) + '/items/' + encodeURIComponent(itemId) + '/explanation')
      setExplanation(result.text)
      setStatus('ready')
    } catch {
      setStatus('error')
    }
  }
  const fallback = recommendationId
    ? 'A explicação detalhada não está disponível agora.'
    : 'Esta sugestão foi selecionada para o pedido acima. A explicação detalhada não está disponível nesta busca.'
  return <details className="why" onToggle={event => { if (event.currentTarget.open) void load() }}><summary>Por que esta sugestão?</summary><p>{status === 'loading' ? 'Buscando explicação…' : status === 'ready' ? explanation : fallback}</p></details>
}

function MusicResult({ ranked, recommendationId }: { ranked: RankedItem<MusicItem>; recommendationId: string | null }) {
  const item = ranked.item
  const destination = musicDestination(item)
  return <li className="result-row"><ResultImage url={item.image_url} title={item.title} type="music" /><div className="result-main"><div className="result-heading"><h3>{item.title}</h3><span>{duration(item.duration_ms)}</span></div><p>{item.artist}{item.album ? ' · ' + item.album : ''}</p>{item.tags?.length ? <div className="result-tags">{item.tags.slice(0, 3).map(tag => <span key={tag}>{tag}</span>)}</div> : null}<Why recommendationId={recommendationId} itemId={item.id} /></div><a className="result-link" href={destination.href} target="_blank" rel="noopener noreferrer" aria-label={destination.label + ': ' + item.title}>{destination.label} <ArrowUpRight size={17} /></a></li>
}

function BookResult({ ranked, recommendationId }: { ranked: RankedItem<BookItem>; recommendationId: string | null }) {
  const item = ranked.item
  return <li className="result-row"><ResultImage url={item.cover_url || (item.provider === 'local' ? localBookCover(item.title) : undefined)} title={item.title} type="books" /><div className="result-main"><div className="result-heading"><h3>{item.title}</h3>{item.publication_year ? <span>{item.publication_year}</span> : null}</div><p>{item.authors?.join(', ') || 'Autoria não informada'}</p>{item.description ? <p className="result-description">{item.description}</p> : null}<Why recommendationId={recommendationId} itemId={item.id} /></div>{item.external_url ? <a className="result-link" href={item.external_url} target="_blank" rel="noopener noreferrer" aria-label={'Abrir ' + item.title + ' na fonte'}>Ver livro <ArrowUpRight size={17} /></a> : null}</li>
}

export default function Discovery({ kind }: { kind: Kind }) {
  const content = config[kind]
  const location = useLocation()
  const initialQuery = (location.state as { query?: string } | null)?.query || ''
  const [query, setQuery] = useState(initialQuery)
  const [submittedQuery, setSubmittedQuery] = useState('')
  const [data, setData] = useState<Data | null>(null)
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [error, setError] = useState('')
  const [stage, setStage] = useState(0)
  const [vocals, setVocals] = useState('')
  const [energy, setEnergy] = useState('')
  const controller = useRef<AbortController | null>(null)

  async function runSearch(text: string) {
    controller.current?.abort()
    const nextController = new AbortController()
    controller.current = nextController
    setData(null)
    setSubmittedQuery(text.trim())
    setError('')
    setStage(0)
    setStatus('loading')
    try {
      const filters = kind === 'music' ? {
        ...(vocals ? { vocals } : {}), ...(energy ? { energy } : {}),
      } : {}
      const result = await post<Data>(content.endpoint, { query: text.trim(), filters, limit: 10 }, nextController.signal)
      if (!nextController.signal.aborted) { setData(result); setStatus('success') }
    } catch (cause) {
      if (!nextController.signal.aborted) { setError(parseError(cause)); setStatus('error') }
    }
  }

  useEffect(() => {
    if (initialQuery.trim().length >= 3) void runSearch(initialQuery)
    return () => controller.current?.abort()
    // Initial route state starts the first search once.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  useEffect(() => {
    if (status !== 'loading') return
    const interval = window.setInterval(() => setStage(current => Math.min(current + 1, 2)), 1600)
    return () => window.clearInterval(interval)
  }, [status])

  function submit(event: FormEvent) {
    event.preventDefault()
    if (query.trim().length >= 3) void runSearch(query)
  }

  const words = intentWords(data?.parsed_query)
  return <div className="discovery-page">
    <section className="discovery-intro container"><div><span className="page-icon">{kind === 'music' ? <Headphones size={25} /> : <BookOpen size={25} />}</span><h1>{content.title}</h1><p>{content.description}</p></div><div className="intro-art" aria-hidden="true"><img src="/images/affinity-atlas.png" alt="" /></div></section>
    <section className="search-section container" aria-label={kind === 'music' ? 'Buscar músicas' : 'Buscar livros'}>
      <form onSubmit={submit}>
        <label htmlFor="discovery-query">Seu pedido</label>
        <textarea id="discovery-query" value={query} onChange={event => setQuery(event.target.value)} placeholder={content.placeholder} minLength={3} maxLength={1000} required rows={3} />
        <div className="search-footer"><span>{query.length}/1000 caracteres</span><button className="button button-primary" type="submit" disabled={status === 'loading' || query.trim().length < 3}>{status === 'loading' ? 'Buscando…' : 'Encontrar sugestões'} <ArrowRight size={18} /></button></div>
        {kind === 'music' ? <details className="filters"><summary><SlidersHorizontal size={17} /> Ajustar preferências</summary><div className="filter-grid"><label>Vocais<select value={vocals} onChange={event => setVocals(event.target.value)}><option value="">Tanto faz</option><option value="none">Instrumental</option><option value="required">Com voz</option></select></label><label>Energia<select value={energy} onChange={event => setEnergy(event.target.value)}><option value="">Tanto faz</option><option value="low">Baixa</option><option value="medium">Média</option><option value="high">Alta</option></select></label></div></details> : null}
      </form>
      {status === 'idle' ? <div className="search-empty"><Search size={21} /><p>Não sabe por onde começar?</p><div>{content.examples.map(example => <button key={example} type="button" onClick={() => setQuery(example)}>{example} <ArrowUpRight size={15} /></button>)}</div></div> : null}
    </section>
    <section className="results-section container" aria-live="polite" aria-busy={status === 'loading'}>
      {status === 'success' && data?.items.length && data.meta?.hint ? <p className="field-help">{data.meta.hint}</p> : null}
      {status === 'loading' ? <div className="status-panel"><div className="loading-track" aria-hidden="true"><span /></div><h2>{['Entendendo seu pedido…', 'Buscando opções reais…', 'Organizando sugestões…'][stage]}</h2><p>Essa busca pode levar alguns segundos.</p><button className="text-button" type="button" onClick={() => { controller.current?.abort(); setStatus('idle') }}>Cancelar busca</button></div> : null}
      {status === 'error' ? <div className="status-panel error-panel"><CircleAlert size={30} /><h2>Não foi possível buscar agora.</h2><p>{error}</p><button className="button button-secondary" type="button" onClick={() => void runSearch(query)}><RotateCcw size={17} /> Tentar novamente</button></div> : null}
      {status === 'success' && data ? <><div className="results-title"><div><span className="results-kicker">Seu pedido</span><h2>{submittedQuery}</h2></div><span>{data.items.length} {data.items.length === 1 ? 'sugestão' : 'sugestões'}</span></div>{words.length ? <div className="understanding"><strong>Como entendemos</strong><div>{words.map((word, index) => <span key={word + index}>{word}</span>)}</div></div> : null}{data.items.length ? <ol className="result-list">{kind === 'music' ? (data as Recommendation<MusicItem>).items.map(item => <MusicResult key={item.item.id} ranked={item} recommendationId={data.recommendation_id} />) : (data as Recommendation<BookItem>).items.map(item => <BookResult key={item.item.id} ranked={item} recommendationId={data.recommendation_id} />)}</ol> : <div className="status-panel"><h2>Nenhuma boa opção por enquanto.</h2><p>{data.meta?.hint || 'Tente descrever de outro jeito ou ampliar seu pedido.'}</p></div>}</> : null}
    </section>
  </div>
}
