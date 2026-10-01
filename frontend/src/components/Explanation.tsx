import { useEffect, useRef, useState } from 'react'
import { api } from '../lib/api'
import { Accordion } from './ui/accordion'

export function Explanation({ recommendationId, itemId }: { recommendationId: string | null; itemId: string }) {
  const [status, setStatus] = useState<'idle' | 'loading' | 'ready' | 'error'>('idle')
  const [explanation, setExplanation] = useState('')
  const controller = useRef<AbortController | null>(null)

  useEffect(() => () => controller.current?.abort(), [])

  async function load() {
    if (!recommendationId || controller.current || status === 'ready') return
    const next = new AbortController()
    controller.current = next
    setStatus('loading')
    try {
      const result = await api<{ text: string }>('/recommendations/' + encodeURIComponent(recommendationId) + '/items/' + encodeURIComponent(itemId) + '/explanation', { signal: next.signal })
      if (!next.signal.aborted) { setExplanation(result.text); setStatus('ready') }
    } catch {
      if (!next.signal.aborted) setStatus('error')
    } finally {
      if (controller.current === next) controller.current = null
    }
  }

  const fallback = recommendationId
    ? 'A explicação detalhada não está disponível agora.'
    : 'Esta sugestão foi selecionada para o pedido acima. A explicação detalhada não está disponível nesta busca.'
  return <Accordion className="why" title="Por que esta sugestão?" onOpenChange={open => { if (open && status === 'idle') void load() }}>
    <div aria-live="polite" aria-busy={status === 'loading'}>
      <p>{status === 'loading' ? 'Buscando explicação…' : status === 'ready' ? explanation : fallback}</p>
      {status === 'error' ? <button type="button" className="text-button explanation-retry" onClick={() => void load()}>Tentar explicação novamente</button> : null}
    </div>
  </Accordion>
}
