import { RotateCcw } from 'lucide-react'
import { Alert, AlertDescription } from './ui/alert'
import type { DiscoveryKind } from '../lib/discovery'

type Props = {
  kind: DiscoveryKind
  loading: boolean
  ended: boolean
  error: boolean
  message: string
  onContinue: () => void
  onCancel: () => void
}

export function RerollControls({ kind, loading, ended, error, message, onContinue, onCancel }: Props) {
  const options = kind === 'music' ? 'outras músicas' : 'outros livros'
  return <Alert className="reroll-controls" variant={error ? 'destructive' : 'default'} role="group" aria-label="Renovar sugestões">
    <button type="button" className="button button-secondary" onClick={onContinue} disabled={loading || ended}>
      <RotateCcw size={17} aria-hidden="true" />{loading ? `Buscando ${options}…` : `Ver ${options}`}
    </button>
    <AlertDescription className="reroll-message">
      <p role={error ? 'alert' : 'status'} aria-atomic="true">{loading
        ? `Buscando novas sugestões para o mesmo pedido. ${kind === 'music' ? 'Suas músicas atuais continuam' : 'Seus livros atuais continuam'} aqui enquanto você espera.`
        : message}</p>
      {loading ? <button className="text-button" type="button" onClick={onCancel}>Cancelar busca de {options}</button> : null}
    </AlertDescription>
  </Alert>
}
