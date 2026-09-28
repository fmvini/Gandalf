export function duration(ms?: number) {
  if (!ms) return ''
  const minutes = Math.floor(ms / 60000)
  const seconds = Math.floor((ms % 60000) / 1000)
  return `${minutes}:${String(seconds).padStart(2, '0')}`
}

export function intentWords(value?: Record<string, unknown>): string[] {
  if (!value) return []
  return ['mood', 'atmosphere', 'genres', 'themes', 'context', 'energy', 'pace', 'vocals']
    .flatMap(key => {
      const item = value[key]
      return Array.isArray(item) ? item : typeof item === 'string' ? [item] : []
    })
    .filter((item): item is string => typeof item === 'string' && item.length > 0)
    .slice(0, 7)
}
