import type { Herramienta } from '../../catalogo/api/catalogoApi'
import type { Sucursal } from '../../usuarios/api/usuariosApi'
import type { Movimiento, TipoMovimiento } from '../api/movimientosApi'
import { useHistorialMovimientos, useStock } from '../hooks/useMovimientos'
import { cajas, desgloseCajas } from '../formato'

// Historial de movimientos de una herramienta (todas las sucursales, del
// más reciente al más antiguo) y su stock actual por sucursal (HU11).

const fechaHora = new Intl.DateTimeFormat('es', { dateStyle: 'short', timeStyle: 'short' })

// Los ajustes llevan etiqueta propia (ámbar, igual que su formulario) para
// distinguir una corrección de una operación normal del mostrador.
const ETIQUETA: Record<TipoMovimiento, { texto: string; clase: string }> = {
  ENTRADA: { texto: 'Entrada', clase: 'bg-green-50 text-green-700' },
  SALIDA: { texto: 'Salida', clase: 'bg-slate-100 text-slate-700' },
  AJUSTE_POSITIVO: { texto: 'Ajuste +', clase: 'bg-amber-100 text-amber-800' },
  AJUSTE_NEGATIVO: { texto: 'Ajuste −', clase: 'bg-amber-100 text-amber-800' },
  TRANSFERENCIA_SALIDA: { texto: 'Transferencia enviada', clase: 'bg-blue-50 text-blue-700' },
  TRANSFERENCIA_ENTRADA: { texto: 'Transferencia recibida', clase: 'bg-blue-50 text-blue-700' },
}

// Tipos que suman al stock (espejo de EFECTO_EN_STOCK del backend).
const SUMA = new Set<TipoMovimiento>(['ENTRADA', 'AJUSTE_POSITIVO', 'TRANSFERENCIA_ENTRADA'])

function cantidadRegistrada(m: Movimiento): string {
  return m.tipo_unidad === 'CAJA' ? cajas(m.cantidad) : `${m.cantidad} u.`
}

interface Props {
  herramienta: Herramienta
  sucursales: Sucursal[]
}

export function HistorialMovimientos({ herramienta, sucursales }: Props) {
  const { data: movimientos, isLoading, isError } = useHistorialMovimientos(herramienta.id)
  const { data: stock } = useStock(herramienta.id)
  const nombreSucursal = (id: number) => sucursales.find((s) => s.id === id)?.nombre ?? `#${id}`

  return (
    <section className="space-y-4">
      <h2 className="text-lg font-semibold text-slate-800">
        Historial de {herramienta.codigo} · {herramienta.nombre}
      </h2>

      {stock && (
        <div className="grid gap-3 sm:grid-cols-2">
          {stock.map((s) => (
            <div key={s.sucursal_id} className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
              <p className="text-sm text-slate-500">{s.sucursal_nombre}</p>
              <p className="text-2xl font-semibold text-slate-800">{s.unidades} <span className="text-sm font-normal text-slate-500">unidades</span></p>
              {herramienta.unidades_por_caja > 1 && (
                <p className="text-xs text-slate-500">{desgloseCajas(s.cajas_completas, s.unidades_sueltas)}</p>
              )}
            </div>
          ))}
        </div>
      )}

      <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-100 text-slate-600">
            <tr>
              <th className="px-3 py-2">Fecha</th>
              <th className="px-3 py-2">Sucursal</th>
              <th className="px-3 py-2">Tipo</th>
              <th className="px-3 py-2 text-right">Registrado</th>
              <th className="px-3 py-2 text-right">Unidades</th>
              <th className="px-3 py-2">Usuario</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={6} className="px-3 py-4 text-center text-slate-500">Cargando...</td></tr>
            )}
            {isError && (
              <tr><td colSpan={6} className="px-3 py-4 text-center text-red-600">No se pudo cargar el historial.</td></tr>
            )}
            {movimientos?.length === 0 && (
              <tr><td colSpan={6} className="px-3 py-4 text-center text-slate-500">Esta herramienta todavía no tiene movimientos.</td></tr>
            )}
            {movimientos?.map((m) => (
              <tr key={m.id} className="border-t border-slate-100">
                <td className="whitespace-nowrap px-3 py-2">{fechaHora.format(new Date(m.creado_en))}</td>
                <td className="px-3 py-2">{nombreSucursal(m.sucursal)}</td>
                <td className="px-3 py-2">
                  <span className={`whitespace-nowrap rounded px-2 py-0.5 text-xs font-medium ${ETIQUETA[m.tipo_movimiento].clase}`}>
                    {ETIQUETA[m.tipo_movimiento].texto}
                  </span>
                  {m.motivo && <p className="mt-1 max-w-xs text-xs italic text-slate-500">{m.motivo}</p>}
                </td>
                <td className="px-3 py-2 text-right">{cantidadRegistrada(m)}</td>
                <td className={`px-3 py-2 text-right font-medium ${SUMA.has(m.tipo_movimiento) ? 'text-green-700' : 'text-red-700'}`}>
                  {SUMA.has(m.tipo_movimiento) ? '+' : '−'}{m.cantidad_unidades}
                </td>
                <td className="px-3 py-2">{m.usuario_username}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  )
}
