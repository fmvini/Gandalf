export const legalContact = {
  name: 'Vinícius F. Marrocos',
  email: 'viniciusfmarrocos@gmail.com',
}

export const legalUpdatedAt = '2026-10-10'

export const legalLinks = [
  { to: '/politica-de-cookies', label: 'Política de cookies', kind: 'cookies' },
  { to: '/politica-de-privacidade', label: 'Política de privacidade', kind: 'privacy' },
  { to: '/termos-de-uso', label: 'Termos de uso', kind: 'terms' },
] as const

export type LegalKind = typeof legalLinks[number]['kind']
