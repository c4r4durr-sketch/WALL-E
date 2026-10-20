import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Info } from 'lucide-react'
import { getSession } from '../../auth/session'
import { Rol } from '../../../shared/types/roles'
import { mensajeDeError } from '../../../shared/api/errores'
import { fechaLarga, hora, hoyEnLaPaz } from '../../../shared/formato'
import { StatTile } from '../../dashboard/components/StatTile'
import { ETIQUETA, cajas } from '../../movimientos/formato'
import { useSucursales } from '../../usuarios/hooks/useSucursales'
import { useCierreDiario } from '../hooks/useCierreDiario'
import type { CierreDiario, LineaCierre } from '../api/reportesApi'
import type { TipoMovimiento } from '../../movimientos/api/movimientosApi'

// Cierre y resumen diario (HU14): todos los movimientos del día de una
// sucursal, en hora de La Paz, para cuadrar la caja. El Administrador
// elige la sucursal; el Supervisor ve solo la suya (el backend responde
// 403 a cualquier otra, y al Empleado).

function unidades(cierre: CierreDiario, tipo: TipoMovimiento): number {
  return cierre.totales.find((t) => t.tipo_movimiento === tipo)?.unidades ?? 0
}

function cantidadRegistrada(l: LineaCierre): string {
  return l.tipo_unidad === 'CAJA' ? cajas(l.cantidad) : `${l.cantidad} u.`
}

export function CierreDiarioPage() {
  const session = getSession()
  const esAdmin = session?.rol === Rol.ADMINISTRADOR
  const hoy = hoyEnLaPaz()
  const [fecha, setFecha] = useState(hoy)
  const [sucursal, setSucursal] = useState<string>(session?.sucursal_id ? String(session.sucursal_id) : '')
  const { data: sucursales } = useSucursales()

  const fechaValida = /^\d{4}-\d{2}-\d{2}$/.test(fecha) && fecha <= hoy
  const listo = fechaValida && (!esAdmin || sucursal !== '')
  const { data: cierre, isLoading, isError, error, refetch } = useCierreDiario(
    { sucursal: esAdmin ? Number(sucursal) : undefined, fecha },
    listo,
  )

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <Link to="/" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:underline">
            <ArrowLeft size={14} aria-hidden />
            Volver
          </Link>
          <h1 className="mt-2 text-xl font-semibold text-slate-800">Cierre diario</h1>
          <p className="mt-1 text-sm text-slate-500">Movimientos del día por sucursal, en hora de La Paz.</p>
        </div>

        <div className="flex flex-wrap items-end gap-4 rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <div>
            <label htmlFor="fecha" className="mb-1 block text-sm font-medium text-slate-700">Fecha</label>
            <input
              id="fecha"
              type="date"
              value={fecha}
              max={hoy}
              onChange={(e) => setFecha(e.target.value)}
              className="rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
            {!fechaValida && <p className="mt-1 text-xs text-red-600">Elige una fecha que no sea posterior a hoy.</p>}
          </div>
          <div>
            <label htmlFor="sucursal" className="mb-1 block text-sm font-medium text-slate-700">Sucursal</label>
            {esAdmin ? (
              <select
                id="sucursal"
                value={sucursal}
                onChange={(e) => setSucursal(e.target.value)}
                className="min-w-48 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
              >
                <option value="" disabled>Selecciona una sucursal</option>
                {sucursales?.map((s) => (
                  <option key={s.id} value={s.id}>{s.nombre}</option>
                ))}
              </select>
            ) : (
              <p id="sucursal" className="px-1 py-2 text-sm font-medium text-slate-800">{session?.sucursal_nombre}</p>
            )}
          </div>
        </div>

        {esAdmin && sucursal === '' && (
          <p className="text-sm text-slate-500">Elige una sucursal para ver su cierre.</p>
        )}
        {isLoading && listo && <p className="text-sm text-slate-500">Cargando cierre...</p>}
        {isError && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {mensajeDeError(error, 'No se pudo cargar el cierre diario.')}{' '}
            <button type="button" onClick={() => refetch()} className="font-medium underline">Reintentar</button>
          </p>
        )}

        {cierre && listo && (
          <>
            <h2 className="text-lg font-semibold text-slate-800">
              {cierre.sucursal_nombre} · <span className="font-normal">{fechaLarga(cierre.fecha)}</span>
            </h2>

            <div className="grid grid-cols-4 gap-3">
              <StatTile
                etiqueta="Salidas (unidades)"
                valor={cierre.total_salidas_unidades}
                nota={`${cierre.cantidad_salidas} ${cierre.cantidad_salidas === 1 ? 'venta registrada' : 'ventas registradas'}`}
              />
              <StatTile etiqueta="Entradas (unidades)" valor={unidades(cierre, 'ENTRADA')} />
              <StatTile
                etiqueta="Transferencias (unidades)"
                valor={unidades(cierre, 'TRANSFERENCIA_SALIDA') + unidades(cierre, 'TRANSFERENCIA_ENTRADA')}
                nota={`${unidades(cierre, 'TRANSFERENCIA_SALIDA')} enviadas · ${unidades(cierre, 'TRANSFERENCIA_ENTRADA')} recibidas`}
              />
              <StatTile
                etiqueta="Ajustes (unidades)"
                valor={unidades(cierre, 'AJUSTE_POSITIVO') + unidades(cierre, 'AJUSTE_NEGATIVO')}
                nota={`+${unidades(cierre, 'AJUSTE_POSITIVO')} · −${unidades(cierre, 'AJUSTE_NEGATIVO')}`}
              />
            </div>

            {/* CA3: un día sin salidas muestra un aviso, no una tabla vacía. */}
            {cierre.cantidad_salidas === 0 && (
              <p className="flex items-center gap-2 rounded-md border border-slate-200 bg-white px-3 py-2 text-sm text-slate-700">
                <Info size={16} aria-hidden className="text-slate-500" />
                No hubo salidas (ventas) este día en {cierre.sucursal_nombre}.
                {cierre.lineas.length === 0 && ' Tampoco hubo otros movimientos.'}
              </p>
            )}

            {cierre.lineas.length > 0 && (
              <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-100 text-slate-600">
                    <tr>
                      <th className="px-3 py-2">Hora</th>
                      <th className="px-3 py-2">Tipo</th>
                      <th className="px-3 py-2">Herramienta</th>
                      <th className="px-3 py-2 text-right">Cantidad</th>
                      <th className="px-3 py-2 text-right">Unidades</th>
                      <th className="px-3 py-2">Usuario</th>
                      <th className="px-3 py-2">Motivo</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cierre.lineas.map((l) => (
                      <tr key={l.movimiento_id} className="border-t border-slate-100">
                        <td className="px-3 py-2 tabular-nums">{hora(l.fecha_hora)}</td>
                        <td className="px-3 py-2">
                          <span className={`whitespace-nowrap rounded px-2 py-0.5 text-xs font-medium ${ETIQUETA[l.tipo_movimiento].clase}`}>
                            {ETIQUETA[l.tipo_movimiento].texto}
                          </span>
                        </td>
                        <td className="px-3 py-2">
                          <span className="font-medium">{l.codigo}</span> {l.nombre}
                        </td>
                        <td className="px-3 py-2 text-right">{cantidadRegistrada(l)}</td>
                        <td className="px-3 py-2 text-right tabular-nums">{l.cantidad_unidades}</td>
                        <td className="px-3 py-2">{l.usuario}</td>
                        <td className="px-3 py-2 text-slate-600">{l.motivo || <span className="text-slate-400">—</span>}</td>
                      </tr>
                    ))}
                  </tbody>
                  <tfoot className="border-t border-slate-200 bg-slate-50 font-medium">
                    <tr>
                      <td colSpan={4} className="px-3 py-2 text-right">Total de salidas del día</td>
                      <td className="px-3 py-2 text-right tabular-nums">{cierre.total_salidas_unidades}</td>
                      <td colSpan={2} />
                    </tr>
                  </tfoot>
                </table>
              </div>
            )}
          </>
        )}
      </div>
    </div>
  )
}
