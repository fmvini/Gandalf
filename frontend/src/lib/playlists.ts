import { ApiError, type MusicItem } from './api'
import { authSession } from './auth'

export type PlaylistSummary = {
  id: string; name: string; description: string | null
  source: 'MANUAL' | 'READ_WITH_MUSIC'; source_recommendation_id: string | null
  total_duration_ms: number; duration_estimated: boolean; tracks_count: number
  created_at: string; updated_at: string
}
export type PlaylistDetail = PlaylistSummary & { tracks: { position: number; item: MusicItem }[] }
export type PlaylistPage = { items: PlaylistSummary[]; total: number; limit: number; offset: number }

export const playlists = {
  create(name: string, source: string, signal: AbortSignal) {
    return authSession.request<PlaylistDetail>('/playlists', {
      method: 'POST', body: JSON.stringify({ name: name.trim(), source_recommendation_id: source }), signal,
    })
  },
  list(offset: number, signal: AbortSignal) {
    return authSession.request<PlaylistPage>(`/playlists?limit=10&offset=${offset}`, { signal })
  },
  detail(id: string, signal: AbortSignal) {
    return authSession.request<PlaylistDetail>('/playlists/' + encodeURIComponent(id), { signal })
  },
  remove(id: string, signal: AbortSignal) {
    return authSession.request<void>('/playlists/' + encodeURIComponent(id), { method: 'DELETE', signal })
  },
}

export function playlistError(cause: unknown, saving = false) {
  if (cause instanceof ApiError) {
    if (cause.status === 401) return 'Sua sessão terminou. Entre novamente para acessar suas playlists.'
    if (cause.status === 404) return saving
      ? 'Esta trilha saiu do cache. Crie a trilha novamente e tente salvar.'
      : 'Esta playlist não está disponível nesta conta. Volte à lista para atualizar suas playlists.'
    if (cause.status === 503) return 'As playlists estão indisponíveis agora. Aguarde um instante e tente novamente.'
  }
  return cause instanceof Error ? cause.message : 'Não foi possível concluir. Tente novamente.'
}

export function playlistDuration(playlist: PlaylistSummary) {
  return `${playlist.tracks_count} ${playlist.tracks_count === 1 ? 'faixa' : 'faixas'} · ${Math.round(playlist.total_duration_ms / 60000)} min${playlist.duration_estimated ? ' (estimados)' : ''}`
}
