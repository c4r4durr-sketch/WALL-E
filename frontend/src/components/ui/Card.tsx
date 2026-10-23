import type { HTMLAttributes, ReactNode } from 'react'
import { cx } from './cx'

// Tarjeta: superficie con sombra en capas (sin borde como separador).
// `interactiva`: al pasar el mouse sube 3 px y pasa a la sombra --shh.

interface Props extends HTMLAttributes<HTMLDivElement> {
  interactiva?: boolean
  // 'grande' (26 px, tarjetas de página) o 'interna' (20 px, dentro de otra).
  radio?: 'grande' | 'interna'
  sinPadding?: boolean
}

export function Card({ interactiva = false, radio = 'grande', sinPadding = false, className, ...props }: Props) {
  return (
    <div
      className={cx(
        'bg-surf shadow-sh',
        radio === 'grande' ? 'rounded-[26px]' : 'rounded-card',
        !sinPadding && 'p-6',
        interactiva && 'transicion hover:-translate-y-[3px] hover:shadow-shh',
        className,
      )}
      {...props}
    />
  )
}

// Título de sección dentro de una tarjeta, con descripción y acciones.
export function CardHeader({
  titulo,
  descripcion,
  acciones,
  className,
}: {
  titulo: ReactNode
  descripcion?: ReactNode
  acciones?: ReactNode
  className?: string
}) {
  return (
    <div className={cx('flex items-start justify-between gap-4', className)}>
      <div className="min-w-0">
        <h2 className="text-[17px] font-semibold tracking-[-0.01em] text-ink">{titulo}</h2>
        {descripcion && <p className="mt-0.5 text-[13px] text-muted">{descripcion}</p>}
      </div>
      {acciones && <div className="flex shrink-0 items-center gap-2">{acciones}</div>}
    </div>
  )
}
