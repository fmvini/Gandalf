import { ApiError, type BookItem, type MusicItem } from './api'
import { authSession } from './auth'

export type FavoriteType = 'MUSIC' | 'BOOK'
export type Favorite = {
  id: string; type: FavoriteType; item_id: string; created_at: string
  item: MusicItem | BookItem
}
export type FavoritePage = { items: Favorite[]; total: number; limit: number; offset: number }
export type AuthReturnTo = { pathname: string; state?: unknown }

const path = '/users/me/favorites'
export const favorites = {
  status(type: FavoriteType, itemIds: string[], signal: AbortSignal) {
    return authSession.request<{ favorites: Record<string, string> }>(path + '/status', {
      method: 'POST', body: JSON.stringify({ type, item_ids: [...new Set(itemIds)] }), signal,
    })
  },
  save(recommendationId: string, itemId: string, signal: AbortSignal) {
    return authSession.request<Favorite>(path, {
      method: 'POST', body: JSON.stringify({ recommendation_id: recommendationId, item_id: itemId }), signal,
    })
  },
  list(type: FavoriteType | '', offset: number, signal: AbortSignal) {
    return authSession.request<FavoritePage>(`${path}?limit=10&offset=${offset}${type ? '&type=' + type : ''}`, { signal })
  },
  remove(id: string, signal: AbortSignal) {
    return authSession.request<void>(path + '/' + encodeURIComponent(id), { method: 'DELETE', signal })
  },
}

export function favoriteError(cause: unknown) {
  if (cause instanceof ApiError) {
    if (cause.status === 404) return 'Esta seleção expirou ou o item não está mais disponível nela. Faça uma nova busca para salvar.'
    if (cause.status === 401) return 'Sua sessão terminou. Entre novamente para acessar seus favoritos.'
    if (cause.status === 503) return 'Os favoritos estão indisponíveis agora. Aguarde um instante e tente novamente.'
  }
  return cause instanceof Error ? cause.message : 'Não foi possível atualizar seus favoritos. Tente novamente.'
}
