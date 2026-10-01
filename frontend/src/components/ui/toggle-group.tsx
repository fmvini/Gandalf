// Adapted from shadcn's Toggle Group, retrieved through the authenticated 21st MCP.
// MIT: see frontend/THIRD_PARTY_NOTICES.md. Required, single-selection preference.
import * as ToggleGroupPrimitive from '@radix-ui/react-toggle-group'
import { Check } from 'lucide-react'

export function ToggleGroup({ label, value, items, onChange }: {
  label: string
  value: string
  items: { value: string; label: string }[]
  onChange: (value: string) => void
}) {
  return <div className="preference-group">
    <span className="preference-label">{label}</span>
    <ToggleGroupPrimitive.Root type="single" value={value} onValueChange={next => { if (next) onChange(next) }} aria-label={label} className="preference-choices">
      {items.map(item => <ToggleGroupPrimitive.Item key={item.value} value={item.value} className="preference-choice">
        <Check size={14} className="preference-check" aria-hidden="true" />{item.label}
      </ToggleGroupPrimitive.Item>)}
    </ToggleGroupPrimitive.Root>
  </div>
}
