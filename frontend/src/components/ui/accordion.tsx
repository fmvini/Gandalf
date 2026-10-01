// Adapted from shadcn's Accordion, retrieved through the authenticated 21st MCP.
// MIT: see frontend/THIRD_PARTY_NOTICES.md.
import type { ReactNode } from 'react'
import * as AccordionPrimitive from '@radix-ui/react-accordion'
import { ChevronDown } from 'lucide-react'

export function Accordion({ title, children, className = '', onOpenChange }: {
  title: ReactNode
  children: ReactNode
  className?: string
  onOpenChange?: (open: boolean) => void
}) {
  return <AccordionPrimitive.Root type="single" collapsible className={'accordion ' + className} onValueChange={value => onOpenChange?.(value === 'content')}>
    <AccordionPrimitive.Item value="content">
      <AccordionPrimitive.Header className="accordion-heading">
        <AccordionPrimitive.Trigger className="accordion-trigger">
          <span>{title}</span><ChevronDown size={16} aria-hidden="true" />
        </AccordionPrimitive.Trigger>
      </AccordionPrimitive.Header>
      <AccordionPrimitive.Content className="accordion-content">
        <div className="accordion-body">{children}</div>
      </AccordionPrimitive.Content>
    </AccordionPrimitive.Item>
  </AccordionPrimitive.Root>
}
