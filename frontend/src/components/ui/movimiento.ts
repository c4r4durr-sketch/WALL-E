import type { Transition } from 'motion/react'

// Movimiento compartido (docs/DISENO.md): 200 ms con la curva
// cubic-bezier(.2,.8,.2,1); listas escalonadas de 30 ms por elemento,
// hasta el elemento 12. Con prefers-reduced-motion no hay entradas: lo
// resuelven MotionConfig (en main.tsx) y los componentes con
// useReducedMotion.

export const CURVA = [0.2, 0.8, 0.2, 1] as const

export const TRANSICION: Transition = { duration: 0.2, ease: CURVA }

export function retrasoEscalonado(indice: number): number {
  return Math.min(indice, 12) * 0.03
}
