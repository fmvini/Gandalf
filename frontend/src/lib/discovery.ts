import type { BookItem, MusicItem, RankedItem } from './api'

export type DiscoveryKind = 'music' | 'books'
export type DiscoveryFilters = { vocals: string; energy: string }
export const MAX_SEEN_ITEMS = 200

// The exclusion list is cumulative. Request fewer items near its boundary;
// never drop old IDs to make room, which would reintroduce previous results.
export function continuationBody(kind: DiscoveryKind, query: string, filters: DiscoveryFilters, seen: Set<string>, offset: number) {
  const remaining = MAX_SEEN_ITEMS - seen.size
  if (remaining <= 0) return null
  return {
    query, limit: Math.min(10, remaining), offset,
    ...(kind === 'music' ? {
      filters: { ...(filters.vocals ? { vocals: filters.vocals } : {}), ...(filters.energy ? { energy: filters.energy } : {}) },
      excluded_music_ids: [...seen],
    } : { excluded_book_ids: [...seen] }),
  }
}

export function freshSuggestions<T extends MusicItem | BookItem>(items: RankedItem<T>[], seen: Set<string>, limit = 10) {
  const unique = new Set(seen)
  return items.filter(row => {
    if (unique.has(row.item.id) || unique.size - seen.size >= limit) return false
    unique.add(row.item.id)
    return true
  })
}
