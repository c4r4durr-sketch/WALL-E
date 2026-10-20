import { History, X } from 'lucide-react'
import { fechaHora, monto } from '../../../shared/formato'
import { useHistorialCostos } from '../hooks/useHistorialCostos'
import type { Herramienta } from '../api/catalogoApi'

// HU7: cambios del costo unitario de una herramienta, del más reciente al
// más antiguo, con quién y cuándo los hizo. Solo lectura (todos los roles).

interface Props {
  herramienta: Herramienta
  onCerrar: () => void
}

export function HistorialCostos({ herramienta, onCerrar }: Props) {
  const { data: cambios, isLoading, isError, refetch } = useHistorialCostos(herramienta.id)

  return (
    <section className="space-y-3 rounded-lg border border-slate-300 bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="inline-flex items-center gap-2 text-lg font-semibold text-slate-800">
          <History size={18} aria-hidden />
          Historial de costos · {herramienta.codigo} {herramienta.nombre}
        </h2>
        <button
          type="button"
          onClick={onCerrar}
          title="Cerrar"
          aria-label="Cerrar historial"
          className="rounded-md p-1.5 text-slate-600 hover:bg-slate-100"
        >
          <X size={18} aria-hidden />
        </button>
      </div>

      {isLoading && <p className="text-sm text-slate-500">Cargando...</p>}
      {isError && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          No se pudo cargar el historial.{' '}
          <button type="button" onClick={() => refetch()} className="font-medium underline">Reintentar</button>
        </p>
      )}
      {cambios?.length === 0 && (
        <p className="text-sm text-slate-500">Todavía no se cargó un costo para esta herramienta.</p>
      )}
      {cambios && cambios.length > 0 && (
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-100 text-slate-600">
            <tr>
              <th className="px-3 py-2">Fecha</th>
              <th className="px-3 py-2 text-right">Costo anterior</th>
              <th className="px-3 py-2 text-right">Costo nuevo</th>
              <th className="px-3 py-2">Usuario</th>
            </tr>
          </thead>
          <tbody>
            {cambios.map((c) => (
              <tr key={c.id} className="border-t border-slate-100">
                <td className="px-3 py-2">{fechaHora(c.fecha)}</td>
                <td className="px-3 py-2 text-right tabular-nums">
                  {c.costo_anterior === null ? <span className="text-slate-400">Primer costo</span> : monto(c.costo_anterior)}
                </td>
                <td className="px-3 py-2 text-right font-medium tabular-nums">{monto(c.costo_nuevo)}</td>
                <td className="px-3 py-2">{c.usuario}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  )
}
