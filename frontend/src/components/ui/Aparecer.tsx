import type { ReactNode } from 'react'
import { motion, useReducedMotion } from 'motion/react'
import { TRANSICION, retrasoEscalonado } from './movimiento'

// Entrada escalonada de un elemento de lista (30 ms por índice, hasta 12).
// Con prefers-reduced-motion aparece directamente, sin animación.

interface Props {
  indice: number
  children: ReactNode
  className?: string
}

export function Aparecer({ indice, children, className }: Props) {
  const reducido = useReducedMotion()
  return (
    <motion.div
      className={className}
      initial={reducido ? false : { opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ ...TRANSICION, delay: retrasoEscalonado(indice) }}
    >
      {children}
    </motion.div>
  )
}
