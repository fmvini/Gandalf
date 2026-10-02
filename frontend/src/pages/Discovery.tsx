import { useEffect, useRef, useState, type FormEvent } from 'react'
import { useLocation } from 'react-router-dom'
import { ArrowRight, ArrowUpRight, BookOpen, CircleAlert, Headphones, RotateCcw, Search, SlidersHorizontal } from 'lucide-react'
import { musicDestination, post, type BookItem, type MusicItem, type RankedItem, type Recommendation } from '../lib/api'
import { duration, intentWords } from '../lib/format'
import { BookCover } from '../components/BookCover'
import { Accordion } from '../components/ui/accordion'
import { ToggleGroup } from '../components/ui/toggle-group'
import { ResultSkeleton } from '../components/ui/skeleton'
import { Explanation } from '../components/Explanation'
import { FavoriteControls, FavoriteButton } from '../components/FavoriteControls'
import { continuationBody, freshSuggestions, MAX_SEEN_ITEMS } from '../lib/discovery'
import { RerollControls } from '../components/RerollControls'
import { AnimatedContent } from '../components/ui/animated-content'

type Kind = 'music' | 'books'
type Data = Recommendation<MusicItem> | Recommendation<BookItem>
export type DiscoverySnapshot = {
  kind: Kind; query: string; submittedQuery: string; data: Data
  vocals: string; energy: string; submittedFilters: { vocals: string; energy: string }
  seenItemIds?: string[]; seenBookIds?: string[]; nextOffset: number
  rerollState?: 'idle' | 'error' | 'exhausted'; rerollMessage?: string
}
const vocalOptions = [{ value: 'any', label: 'Tanto faz' }, { value: 'none', label: 'Instrumental' }, { value: 'required', label: 'Com voz' }]
const energyOptions = [{ value: 'any', label: 'Tanto faz' }, { value: 'low', label: 'Baixa' }, { value: 'medium', label: 'Média' }, { value: 'high', label: 'Alta' }]

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

function MusicResult({ ranked, recommendationId }: { ranked: RankedItem<MusicItem>; recommendationId: string | null }) {
  const item = ranked.item
  const destination = musicDestination(item)
  return <li className="result-row"><ResultImage url={item.image_url} title={item.title} type="music" /><div className="result-main"><div className="result-heading"><h3>{item.title}</h3><span>{duration(item.duration_ms)}</span></div><p>{item.artist}{item.album ? ' · ' + item.album : ''}</p>{item.tags?.length ? <div className="result-tags">{item.tags.slice(0, 3).map(tag => <span key={tag}>{tag}</span>)}</div> : null}<Explanation recommendationId={recommendationId} itemId={item.id} /><FavoriteButton itemId={item.id} title={item.title} /></div><a className="result-link" href={destination.href} target="_blank" rel="noopener noreferrer" aria-label={destination.label + ': ' + item.title}>{destination.label} <ArrowUpRight size={17} /></a></li>
}

function BookResult({ ranked, recommendationId }: { ranked: RankedItem<BookItem>; recommendationId: string | null }) {
  const item = ranked.item
  return <li className="result-row"><div className="result-image books"><BookCover book={item} alt={'Capa de ' + item.title} loading="lazy" /></div><div className="result-main"><div className="result-heading"><h3>{item.title}</h3>{item.publication_year ? <span>{item.publication_year}</span> : null}</div><p>{item.authors?.join(', ') || 'Autoria não informada'}</p>{item.description ? <p className="result-description">{item.description}</p> : null}<Explanation recommendationId={recommendationId} itemId={item.id} /><FavoriteButton itemId={item.id} title={item.title} /></div>{item.external_url ? <a className="result-link" href={item.external_url} target="_blank" rel="noopener noreferrer" aria-label={'Abrir ' + item.title + ' na fonte'}>Ver livro <ArrowUpRight size={17} /></a> : null}</li>
}

export default function Discovery({ kind }: { kind: Kind }) {
  const content = config[kind]
  const location = useLocation()
  const routeSnapshot = (location.state as { discovery?: DiscoverySnapshot } | null)?.discovery
  const restored = routeSnapshot?.kind === kind ? routeSnapshot : undefined
  const initialQuery = (location.state as { query?: string } | null)?.query || ''
  const [query, setQuery] = useState(restored?.query ?? initialQuery)
  const [submittedQuery, setSubmittedQuery] = useState(restored?.submittedQuery || '')
  const [data, setData] = useState<Data | null>(restored?.data || null)
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>(restored ? 'success' : 'idle')
  const [error, setError] = useState('')
  const [stage, setStage] = useState(0)
  const [vocals, setVocals] = useState(restored?.vocals || '')
  const [energy, setEnergy] = useState(restored?.energy || '')
  const [submittedFilters, setSubmittedFilters] = useState(restored?.submittedFilters || { vocals: '', energy: '' })
  const controller = useRef<AbortController | null>(null)
  const seenItems = useRef(new Set<string>(restored?.seenItemIds || restored?.seenBookIds || restored?.data.items.map(row => row.item.id) || []))
  const nextOffset = useRef(restored?.nextOffset || 0)
  const [rerollStatus, setRerollStatus] = useState<'idle' | 'loading' | 'error' | 'exhausted'>(restored?.rerollState || 'idle')
  const [rerollError, setRerollError] = useState(restored?.rerollMessage || '')

  async function runSearch(text: string) {
    controller.current?.abort()
    const nextController = new AbortController()
    controller.current = nextController
    seenItems.current.clear()
    nextOffset.current = 0
    setRerollStatus('idle')
    setRerollError('')
    setData(null)
    setSubmittedQuery(text.trim())
    setSubmittedFilters({ vocals, energy })
    setError('')
    setStage(0)
    setStatus('loading')
    try {
      const filters = kind === 'music' ? {
        ...(vocals ? { vocals } : {}), ...(energy ? { energy } : {}),
      } : {}
      const result = await post<Data>(content.endpoint, { query: text.trim(), filters, limit: 10 }, nextController.signal)
      if (!nextController.signal.aborted) {
        const items = freshSuggestions<MusicItem | BookItem>(result.items, seenItems.current)
        items.forEach(row => seenItems.current.add(row.item.id))
        nextOffset.current = result.meta?.next_offset ?? 0
        setData({ ...result, items } as Data)
        setStatus('success')
      }
    } catch (cause) {
      if (!nextController.signal.aborted) { setError(parseError(cause)); setStatus('error') }
    } finally {
      if (controller.current === nextController) controller.current = null
    }
  }

  async function rerollSuggestions() {
    if (!data || status !== 'success' || controller.current || rerollStatus === 'exhausted' || data.meta?.has_more === false) return
    const body = continuationBody(kind, submittedQuery, submittedFilters, seenItems.current, nextOffset.current)
    if (!body) return
    const nextController = new AbortController()
    controller.current = nextController
    setRerollError('')
    setRerollStatus('loading')
    try {
      const result = await post<Data>(content.endpoint, body, nextController.signal)
      if (nextController.signal.aborted) return
      // Keep the current list when the catalog is exhausted or unavailable.
      const freshItems = freshSuggestions<MusicItem | BookItem>(result.items, seenItems.current, body.limit)
      nextOffset.current = result.meta?.next_offset ?? body.offset
      if (!freshItems.length) {
        // Degradation is a transient source failure, even if the service cannot
        // know a next page. Keep the prior selection and allow an explicit retry.
        const canRetry = result.meta?.degraded || result.meta?.has_more
        setRerollStatus(canRetry ? 'error' : 'exhausted')
        setRerollError(canRetry
          ? `Não encontramos ${kind === 'music' ? 'novas músicas' : 'novos livros'} nesta tentativa. Tente novamente para continuar a busca.`
          : `Você já viu as sugestões disponíveis para este pedido. Amplie ou ajuste a descrição para buscar mais ${kind === 'music' ? 'músicas' : 'livros'}.`)
        return
      }
      freshItems.forEach(row => seenItems.current.add(row.item.id))
      setData({ ...result, items: freshItems } as Data)
      setRerollStatus('idle')
    } catch (cause) {
      if (!nextController.signal.aborted) {
        setRerollError(parseError(cause))
        setRerollStatus('error')
      }
    } finally {
      if (controller.current === nextController) controller.current = null
    }
  }

  useEffect(() => {
    if (!restored && initialQuery.trim().length >= 3) void runSearch(initialQuery)
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
  const filterCount = Number(Boolean(vocals)) + Number(Boolean(energy))
  const filtersChanged = status === 'success' && (submittedFilters.vocals !== vocals || submittedFilters.energy !== energy)
  const continuationEnded = rerollStatus === 'exhausted' || data?.meta?.has_more === false || seenItems.current.size >= MAX_SEEN_ITEMS
  const continuationMessage = rerollError || (seenItems.current.size >= MAX_SEEN_ITEMS
    ? 'Você chegou ao limite de sugestões desta busca. Ajuste seu pedido para começar uma nova seleção.'
    : continuationEnded ? `Você já viu as sugestões disponíveis. Ajuste seu pedido para explorar ${kind === 'music' ? 'outras músicas' : 'outros livros'}.`
      : `Quer outras opções? Veja ${kind === 'music' ? 'novas músicas' : 'novos livros'} para o mesmo pedido, sem repetir ${kind === 'music' ? 'as já mostradas' : 'os já mostrados'}.`)
  const snapshot: DiscoverySnapshot | undefined = data ? { kind, query, submittedQuery, data, vocals, energy, submittedFilters, seenItemIds: [...seenItems.current], nextOffset: nextOffset.current, rerollState: rerollStatus === 'loading' ? 'idle' : rerollStatus, rerollMessage: rerollStatus === 'loading' ? '' : rerollError } : undefined
  return <div className="discovery-page">
    <section className="discovery-intro container"><div><span className="page-icon">{kind === 'music' ? <Headphones size={25} /> : <BookOpen size={25} />}</span><h1>{content.title}</h1><p>{content.description}</p></div><div className="intro-art" aria-hidden="true"><img src="/images/affinity-atlas.png" alt="" /></div></section>
    <section className="search-section container" aria-label={kind === 'music' ? 'Buscar músicas' : 'Buscar livros'}>
      <form onSubmit={submit}>
        <label htmlFor="discovery-query">Seu pedido</label>
        <textarea id="discovery-query" value={query} onChange={event => setQuery(event.target.value)} placeholder={content.placeholder} minLength={3} maxLength={1000} required rows={3} />
        <div className="search-footer"><span>{query.length}/1000 caracteres</span><button className="button button-primary" type="submit" disabled={status === 'loading' || query.trim().length < 3}>{status === 'loading' ? 'Buscando…' : 'Encontrar sugestões'} <ArrowRight size={18} /></button></div>
        {kind === 'music' ? <Accordion className="filters" title={<><SlidersHorizontal size={17} aria-hidden="true" /> Ajustar preferências{filterCount ? <span className="filter-count">{filterCount} {filterCount === 1 ? 'ajuste' : 'ajustes'}</span> : null}</>}>
          <div className="filter-grid"><ToggleGroup label="Vocais" value={vocals || 'any'} items={vocalOptions} onChange={value => setVocals(value === 'any' ? '' : value)} /><ToggleGroup label="Energia" value={energy || 'any'} items={energyOptions} onChange={value => setEnergy(value === 'any' ? '' : value)} /></div>
          <div className="filter-actions"><p>{filtersChanged ? 'Preferências alteradas. Busque novamente para aplicá-las.' : 'Estes ajustes serão aplicados à sua próxima busca.'}</p>{filterCount ? <button type="button" className="text-button" onClick={() => { setVocals(''); setEnergy('') }}>Limpar preferências</button> : null}</div>
        </Accordion> : null}
      </form>
      {status === 'idle' ? <div className="search-empty"><Search size={21} /><p>Não sabe por onde começar?</p><div>{content.examples.map(example => <button key={example} type="button" onClick={() => setQuery(example)}>{example} <ArrowUpRight size={15} /></button>)}</div></div> : null}
    </section>
    <section className="results-section container" aria-live="polite" aria-busy={status === 'loading' || rerollStatus === 'loading'}>
      {status === 'success' && data && data.items.length > 0 ? <RerollControls kind={kind} loading={rerollStatus === 'loading'} ended={continuationEnded} error={rerollStatus === 'error'} message={continuationMessage} onContinue={() => void rerollSuggestions()} onCancel={() => { controller.current?.abort(); controller.current = null; setRerollStatus('idle'); setRerollError('Busca cancelada. Sua seleção continua aqui.') }} /> : null}
      {status === 'success' && data?.items.length && data.meta?.hint ? <p className="field-help">{data.meta.hint}</p> : null}
      {status === 'loading' ? <><div className="status-panel"><div className="loading-track" aria-hidden="true"><span /></div><h2>{['Entendendo seu pedido…', 'Buscando opções reais…', 'Organizando sugestões…'][stage]}</h2><p>Essa busca pode levar alguns segundos.</p><button className="text-button" type="button" onClick={() => { controller.current?.abort(); setStatus('idle') }}>Cancelar busca</button></div><ResultSkeleton kind={kind} /></> : null}
      {status === 'error' ? <div className="status-panel error-panel"><CircleAlert size={30} /><h2>Não foi possível buscar agora.</h2><p>{error}</p><button className="button button-secondary" type="button" onClick={() => void runSearch(query)}><RotateCcw size={17} /> Tentar novamente</button></div> : null}
      {status === 'success' && data ? <><div className="results-title"><div><span className="results-kicker">Seu pedido</span><h2>{submittedQuery}</h2></div><span>{data.items.length} {data.items.length === 1 ? 'sugestão' : 'sugestões'}</span></div>{kind === 'music' && (submittedFilters.vocals || submittedFilters.energy) ? <div className="submitted-preferences" aria-label="Preferências usadas nesta busca"><strong>Preferências usadas</strong>{submittedFilters.vocals ? <span>{vocalOptions.find(item => item.value === submittedFilters.vocals)?.label}</span> : null}{submittedFilters.energy ? <span>Energia {energyOptions.find(item => item.value === submittedFilters.energy)?.label.toLowerCase()}</span> : null}</div> : null}{words.length ? <div className="understanding"><strong>Como entendemos</strong><div>{words.map((word, index) => <span key={word + index}>{word}</span>)}</div></div> : null}{data.items.length ? <FavoriteControls type={kind === 'music' ? 'MUSIC' : 'BOOK'} recommendationId={data.recommendation_id} itemIds={data.items.map(row => row.item.id)} returnTo={{ pathname: kind === 'music' ? '/music' : '/books', state: { discovery: snapshot } }}><AnimatedContent key={(data.recommendation_id || submittedQuery) + data.items.map(row => row.item.id).join(",")}><ol className="result-list">{kind === 'music' ? (data as Recommendation<MusicItem>).items.map(item => <MusicResult key={(data.recommendation_id || submittedQuery) + item.item.id} ranked={item} recommendationId={data.recommendation_id} />) : (data as Recommendation<BookItem>).items.map(item => <BookResult key={(data.recommendation_id || submittedQuery) + item.item.id} ranked={item} recommendationId={data.recommendation_id} />)}</ol></AnimatedContent></FavoriteControls> : <div className="status-panel"><h2>Nenhuma boa opção por enquanto.</h2><p>{data.meta?.hint || 'Tente descrever de outro jeito ou ampliar seu pedido.'}</p></div>}</> : null}
    </section>
  </div>
}
