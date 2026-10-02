import type { MusicItem } from './api'

export function musicMetadataLabel(item: MusicItem): string {
  const source = item.provider === 'musicbrainz' ? 'MusicBrainz'
    : item.provider === 'local' ? 'Catálogo local'
      : item.provider ? 'Fonte: ' + item.provider : ''
  const classification = item.classification_source === 'ai_estimate' ? 'Estimativa por IA'
    : item.classification_source === 'provider_tags' ? 'Tags da fonte' : ''
  const vocals = item.has_vocals === false ? 'Instrumental'
    : item.has_vocals === true ? 'Com voz' : 'Vocais não informados'
  const energy = item.energy === 'low' ? 'Energia baixa'
    : item.energy === 'medium' ? 'Energia média'
      : item.energy === 'high' ? 'Energia alta' : 'Energia não informada'
  return [source, classification, vocals, energy].filter(Boolean).join(' · ')
}

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
