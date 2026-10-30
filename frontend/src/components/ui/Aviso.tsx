import type { ReactNode } from 'react'
import { AlertTriangle, CheckCircle2, Info, XCircle } from 'lucide-react'
import { cx } from './cx'

// Mensaje dentro de la página: error (role="alert", se anuncia apenas
// aparece), éxito, advertencia o información. Siempre con ícono + texto.

type Tono = 'error' | 'exito' | 'advertencia' | 'info'

const ESTILO: Record<Tono, { clase: string; Icono: typeof Info }> = {
  error: { clase: 'bg-danger-b text-danger', Icono: XCircle },
  exito: { clase: 'bg-ok-b text-ok', Icono: CheckCircle2 },
  advertencia: { clase: 'bg-warn-b text-warn', Icono: AlertTriangle },
  info: { clase: 'bg-surf2 text-ink', Icono: Info },
}

export function Aviso({ tono, children, accion, className }: {
  tono: Tono
  children: ReactNode
  accion?: ReactNode
  className?: string
}) {
  const { clase, Icono } = ESTILO[tono]
  return (
    <div
      role={tono === 'error' ? 'alert' : 'status'}
      className={cx('flex items-start gap-2.5 rounded-campo px-4 py-3 text-sm font-medium', clase, className)}
    >
      <Icono size={18} aria-hidden className="mt-px shrink-0" />
      <div className="min-w-0 flex-1">{children}</div>
      {accion && <div className="shrink-0">{accion}</div>}
    </div>
  )
}
