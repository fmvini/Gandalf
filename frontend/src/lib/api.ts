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
  meta?: { hint?: string; degraded?: boolean }
  playlist?: { total_duration_ms: number; tracks_count: number; duration_estimated?: boolean }
}

const baseUrl = (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1').replace(/\/$/, '')

export async function api<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`${baseUrl}${path}`, {
      ...init,
      headers: { 'Content-Type': 'application/json', ...init?.headers },
    })
  } catch {
    throw new Error('Não foi possível conectar à API. Verifique se o servidor está ligado e tente novamente.')
  }
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    const message = data?.error?.message || data?.detail
    if (response.status === 429) throw new Error('Muitas buscas em pouco tempo. Aguarde um instante e tente novamente.')
    throw new Error(typeof message === 'string' ? message : 'A busca não pôde ser concluída. Tente novamente.')
  }
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
