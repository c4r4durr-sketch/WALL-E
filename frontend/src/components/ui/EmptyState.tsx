import type { ReactNode } from 'react'
import type { LucideIcon } from 'lucide-react'
import { cx } from './cx'

// Estado vacío (docs/DISENO.md): ícono grande en un círculo --soft,
// título, una línea de ayuda y, si corresponde, una acción.

interface Props {
  icono: LucideIcon
  titulo: string
  ayuda?: ReactNode
  accion?: ReactNode
  compacto?: boolean
  className?: string
}

export function EmptyState({ icono: Icono, titulo, ayuda, accion, compacto = false, className }: Props) {
  return (
    <div className={cx('flex flex-col items-center text-center', compacto ? 'px-6 py-8' : 'px-6 py-14', className)}>
      <div className={cx('flex items-center justify-center rounded-full bg-soft text-softink', compacto ? 'h-14 w-14' : 'h-20 w-20')}>
        <Icono size={compacto ? 26 : 34} aria-hidden />
      </div>
      <h3 className="mt-4 text-[17px] font-semibold tracking-[-0.01em] text-ink">{titulo}</h3>
      {ayuda && <p className="mt-1 max-w-sm text-sm text-muted">{ayuda}</p>}
      {accion && <div className="mt-5">{accion}</div>}
    </div>
  )
}
