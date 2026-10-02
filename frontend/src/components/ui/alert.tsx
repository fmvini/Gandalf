// Adapted from shadcn Alert, listed on 21st.dev. Public source, not MCP retrieval.
// MIT: source and license in frontend/THIRD_PARTY_NOTICES.md.
import type { ComponentProps } from 'react'

export function Alert({ className = '', variant = 'default', role = 'alert', ...props }: ComponentProps<'div'> & { variant?: 'default' | 'destructive' }) {
  return <div {...props} data-slot="alert" role={role} className={`inline-alert ${variant === 'destructive' ? 'inline-alert-error' : ''} ${className}`} />
}

export function AlertDescription({ className = '', ...props }: ComponentProps<'div'>) {
  return <div {...props} data-slot="alert-description" className={'inline-alert-description ' + className} />
}
