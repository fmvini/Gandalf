export type MusicItem = {
  id: string; title: string; artist: string; album?: string; image_url?: string | null
  tags?: string[]; duration_ms?: number; links?: Record<string, string | null>
}

export type BookItem = {
  id: string; title: string; authors: string[]; description?: string
  cover_url?: string | null; external_url?: string | null; provider?: string; external_id?: string
  publication_year?: number; genres?: string[]
}

export type RankedItem<T> = {
  position: number; item: T; user_feedback?: string | null
  scores?: { semantic?: number; context?: number; preference?: number; reference?: number }
}
export type Recommendation<T> = {
  recommendation_id: string | null
  parsed_query?: Record<string, unknown>
  items: RankedItem<T>[]
  meta?: { hint?: string; degraded?: boolean; has_more?: boolean; next_offset?: number | null }
  playlist?: { total_duration_ms: number; tracks_count: number; duration_estimated?: boolean; target_duration_ms?: number; target_met?: boolean; shortfall_ms?: number }
}

const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(message: string, public readonly status: number, public readonly code?: string) {
    super(message)
    this.name = 'ApiError'
  }
}

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  const headers = new Headers(init?.headers)
  if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers,
    })
  } catch {
    throw new Error('Não foi possível conectar à API. Verifique se o servidor está ligado e tente novamente.')
  }
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    const message = data?.error?.message || data?.detail
    if (response.status === 429) throw new ApiError('Muitas tentativas em pouco tempo. Aguarde um instante e tente novamente.', 429, data?.error?.code)
    throw new ApiError(typeof message === 'string' ? message : 'A solicitação não pôde ser concluída. Tente novamente.', response.status, data?.error?.code)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

export function post<T>(path: string, body: object, signal?: AbortSignal) {
  return api<T>(path, { method: 'POST', body: JSON.stringify(body), signal })
}

export function musicDestination(item: MusicItem) {
  if (item.links?.spotify) return { href: item.links.spotify, label: 'Ouvir no Spotify' }
  if (item.links?.youtube) return { href: item.links.youtube, label: 'Ouvir no YouTube' }
  if (item.links?.provider) return { href: item.links.provider, label: 'Ver fonte' }
  if (item.links?.search) return { href: item.links.search, label: 'Buscar no YouTube' }
  return {
    href: 'https://www.youtube.com/results?search_query=' + encodeURIComponent(item.title + ' ' + item.artist),
    label: 'Buscar no YouTube',
  }
}
