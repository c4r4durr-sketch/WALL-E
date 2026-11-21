import type { ReactNode } from 'react'
import { useReducedMotion } from 'motion/react'
import type { TooltipContentProps, TooltipValueType } from 'recharts'

// Piezas comunes de los gráficos de /reportes. Los colores son variables
// CSS (index.css: --graf-1 naranja, --graf-2 y --graf-3 grises, más --ink,
// --muted y --line), así cada gráfico sigue al tema claro/oscuro y sale en
// grises al imprimir sin código extra.

export const COLOR = {
  principal: 'var(--graf-1)',
  secundario: 'var(--graf-2)',
  tenue: 'var(--graf-3)',
  tinta: 'var(--ink)',
  texto: 'var(--muted)',
  grilla: 'var(--line)',
  fondo: 'var(--surf)',
} as const

// Ejes sin líneas ni marcas, con texto 12 px --muted.
export const EJE = {
  axisLine: false,
  tickLine: false,
  tick: { fill: COLOR.texto, fontSize: 12 },
} as const

export const GRILLA = { stroke: COLOR.grilla, strokeDasharray: '3 3' } as const

// Entrada corta (400 ms, sin rebote) y ninguna con prefers-reduced-motion.
export function useAnimacion() {
  const reducido = useReducedMotion()
  return { isAnimationActive: !reducido, animationDuration: 400, animationEasing: 'ease-out' } as const
}

// Para el `content` del <Tooltip> de Recharts: recibe la fila de datos
// bajo el cursor (la misma que se pasó en `data`).
export function tooltipDe<T>(render: (fila: T) => ReactNode) {
  return function Contenido({ active, payload }: TooltipContentProps<TooltipValueType, string | number>) {
    const fila = payload?.[0]?.payload as T | undefined
    return active && fila ? render(fila) : null
  }
}
