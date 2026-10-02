'use client'

// AnimatedContent interaction adapted from React Bits / David Haz.
// Replaces GSAP/ScrollTrigger with existing Motion; no hidden default or scroll gate.
// MIT + Commons Clause: see frontend/THIRD_PARTY_NOTICES.md and public/licenses/react-bits.txt.
import type { ReactNode } from 'react'
import { motion, useReducedMotion } from 'motion/react'

export function AnimatedContent({ children }: { children: ReactNode }) {
  const reducedMotion = useReducedMotion()
  return <motion.div
    className="discovery-results-transition"
    initial={reducedMotion !== false ? false : { y: 6 }}
    animate={{ y: 0 }}
    transition={{ duration: reducedMotion !== false ? 0 : 0.22, ease: [0.16, 1, 0.3, 1] }}
  >{children}</motion.div>
}
