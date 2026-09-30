'use client'

// Adapted from Chetan Verma's Animated Tabs, published on 21st.dev.
// MIT: see frontend/THIRD_PARTY_NOTICES.md. Controlled choice group, not tab panels.
import { useId, type ReactNode } from 'react'
import { LayoutGroup, motion, useReducedMotion } from 'motion/react'

type Choice<T extends string> = { id: T; label: string; icon: ReactNode }

export function AnimatedChoices<T extends string>({ items, value, onChange, label }: {
  items: Choice<T>[]
  value: T
  onChange: (value: T) => void
  label: string
}) {
  const id = useId()
  const reduced = useReducedMotion()
  return <LayoutGroup id={id}>
    <div className="animated-choices" role="group" aria-label={label}>
      {items.map(item => <button key={item.id} type="button" aria-pressed={value === item.id} onClick={() => onChange(item.id)}>
        {value === item.id && <motion.span className="choice-highlight" layoutId="active-choice" transition={reduced ? { duration: 0 } : { type: 'spring', stiffness: 380, damping: 34 }} />}
        <span className="choice-label">{item.icon}{item.label}</span>
      </button>)}
    </div>
  </LayoutGroup>
}
