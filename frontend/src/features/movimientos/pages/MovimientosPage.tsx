import { useState } from 'react'
import { Link } from 'react-router-dom'
import { getSession } from '../../auth/session'
import { useHerramientas } from '../../catalogo/hooks/useHerramientas'
import { useSucursales } from '../../usuarios/hooks/useSucursales'
import { Rol } from '../../../shared/types/roles'
import { MovimientoForm } from '../components/MovimientoForm'
import { HistorialMovimientos } from '../components/HistorialMovimientos'

// Entradas y salidas de inventario (HU9) + historial y stock por
// herramienta (HU11). Todos los roles registran; nadie edita ni borra un
// movimiento (se corrige con uno nuevo).
export function MovimientosPage() {
  const session = getSession()
  const { data: herramientas, isLoading } = useHerramientas()
  const { data: sucursales } = useSucursales()
  const [herramientaId, setHerramientaId] = useState<number | null>(null)

  const herramienta = herramientas?.find((h) => h.id === herramientaId) ?? null
  const sucursalFija = session?.rol === Rol.EMPLEADO ? session.sucursal_id : null

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <Link to="/" className="text-sm text-slate-500 hover:underline">← Volver</Link>
          <h1 className="mt-2 text-xl font-semibold text-slate-800">Movimientos de inventario</h1>
        </div>

        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <label htmlFor="herramienta" className="mb-1 block text-sm font-medium text-slate-700">Herramienta</label>
          <select
            id="herramienta"
            value={herramientaId ?? ''}
            onChange={(event) => setHerramientaId(event.target.value ? Number(event.target.value) : null)}
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
          >
            <option value="">{isLoading ? 'Cargando...' : 'Selecciona una herramienta'}</option>
            {herramientas?.map((h) => (
              <option key={h.id} value={h.id}>{h.codigo} · {h.nombre}</option>
            ))}
          </select>
          {herramientas?.length === 0 && (
            <p className="mt-2 text-sm text-slate-500">
              No hay herramientas en el catálogo. <Link to="/catalogo" className="text-blue-600 hover:underline">Cargar una →</Link>
            </p>
          )}
        </div>

        {herramienta && sucursales && (
          <>
            {/* key: al cambiar de herramienta el formulario arranca limpio */}
            <MovimientoForm key={herramienta.id} herramienta={herramienta} sucursales={sucursales} sucursalFija={sucursalFija} />
            <HistorialMovimientos herramienta={herramienta} sucursales={sucursales} />
          </>
        )}
      </div>
    </div>
  )
}
