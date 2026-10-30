import { History } from 'lucide-react'
import { Aviso, Button, EmptyState, SkeletonFilas } from '../../../components/ui'
import { fechaHora, monto } from '../../../shared/formato'
import { useHistorialCostos } from '../hooks/useHistorialCostos'
import type { Herramienta } from '../api/catalogoApi'

// HU7: cambios del costo unitario de una herramienta, del más reciente al
// más antiguo, con quién y cuándo los hizo. Solo lectura (todos los roles).
// Se muestra en el panel lateral del catálogo.

export function HistorialCostos({ herramienta }: { herramienta: Herramienta }) {
  const { data: cambios, isLoading, isError, refetch } = useHistorialCostos(herramienta.id)

  if (isLoading) {
    return (
      <div className="overflow-hidden rounded-card bg-surf shadow-sh">
        <SkeletonFilas filas={4} columnas={3} />
      </div>
    )
  }
  if (isError) {
    return (
      <Aviso tono="error" accion={<Button tamano="sm" onClick={() => refetch()}>Reintentar</Button>}>
        No se pudo cargar el historial.
      </Aviso>
    )
  }
  if (!cambios || cambios.length === 0) {
    return (
      <div className="rounded-card bg-surf shadow-sh">
        <EmptyState compacto icono={History} titulo="Sin costos cargados" ayuda="Todavía no se cargó un costo para esta herramienta." />
      </div>
    )
  }

  return (
    <ol className="space-y-2.5">
      {cambios.map((c) => (
        <li key={c.id} className="flex items-center justify-between gap-4 rounded-card bg-surf px-5 py-4 shadow-sh">
          <div className="min-w-0">
            <p className="text-sm font-semibold text-ink">{c.usuario}</p>
            <p className="text-xs text-muted tabular-nums">{fechaHora(c.fecha)}</p>
          </div>
          <div className="text-right">
            <p className="text-[17px] font-bold tracking-[-0.03em] text-ink tabular-nums">{monto(c.costo_nuevo)}</p>
            <p className="text-xs text-muted tabular-nums">
              {c.costo_anterior === null ? 'Primer costo' : `antes ${monto(c.costo_anterior)}`}
            </p>
          </div>
        </li>
      ))}
    </ol>
  )
}
