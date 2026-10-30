import type { ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'
import { Card } from './Card'
import { cx } from './cx'

// Indicador: etiqueta (12/600 --muted), número grande (28/700 con cifras
// tabulares) y una nota. Si es una alerta activa lo dice con ícono y
// texto ("Requiere atención"), no solo con color.

interface Props {
  etiqueta: string
  valor: ReactNode
  unidad?: string
  nota?: ReactNode
  alerta?: boolean
  className?: string
}

export function StatCard({ etiqueta, valor, unidad, nota, alerta = false, className }: Props) {
  return (
    <Card interactiva className={cx('flex flex-col', className)}>
      <p className="text-xs font-semibold text-muted">{etiqueta}</p>
      <p className="mt-2 text-[28px] font-bold leading-none tracking-[-0.03em] text-ink tabular-nums">
        {typeof valor === 'number' ? valor.toLocaleString('es') : valor}
        {unidad && <span className="ml-1.5 text-sm font-medium tracking-normal text-muted">{unidad}</span>}
      </p>
      {alerta ? (
        <p className="mt-3 inline-flex items-center gap-1.5 text-xs font-semibold text-warn">
          <AlertTriangle size={14} aria-hidden />
          Requiere atención
        </p>
      ) : (
        nota && <p className="mt-3 text-xs text-muted">{nota}</p>
      )}
    </Card>
  )
}
