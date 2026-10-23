import type { ReactNode } from 'react'
import { cx } from './cx'

// Estado en píldora: fondo y texto del mismo tono (--ok / --warn /
// --danger), o neutro. El texto siempre dice el estado; el color solo lo
// refuerza.

export type TonoBadge = 'ok' | 'warn' | 'danger' | 'neutral' | 'acc'

const TONO: Record<TonoBadge, string> = {
  ok: 'bg-ok-b text-ok',
  warn: 'bg-warn-b text-warn',
  danger: 'bg-danger-b text-danger',
  neutral: 'bg-surf2 text-muted',
  acc: 'bg-soft text-softink',
}

export function Badge({ tono = 'neutral', icono, children, className }: {
  tono?: TonoBadge
  icono?: ReactNode
  children: ReactNode
  className?: string
}) {
  return (
    <span
      className={cx(
        'inline-flex items-center gap-1 whitespace-nowrap rounded-full px-2.5 py-0.5 text-xs font-semibold',
        TONO[tono],
        className,
      )}
    >
      {icono}
      {children}
    </span>
  )
}
