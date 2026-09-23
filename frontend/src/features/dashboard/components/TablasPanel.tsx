import { Link } from 'react-router-dom'
import type { AlertaReorden, HerramientaEstancada } from '../api/indicadoresApi'

// Detalle de las alertas del panel. Tablas (no gráficos): lo que importa es
// qué herramienta, cuánto hay y qué hacer, y eso se lee mejor en filas.

function Seccion({ titulo, descripcion, children }: { titulo: string; descripcion: string; children: React.ReactNode }) {
  return (
    <section className="rounded-lg border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-100 px-4 py-3">
        <h2 className="font-semibold text-slate-800">{titulo}</h2>
        <p className="text-xs text-slate-500">{descripcion}</p>
      </div>
      <div className="overflow-x-auto">{children}</div>
    </section>
  )
}

function Vacio({ texto }: { texto: string }) {
  return <p className="px-4 py-6 text-center text-sm text-slate-500">{texto}</p>
}

function pedidoEnCajas(a: AlertaReorden): string {
  if (a.pedido_sugerido === null) return '—'
  const unidades = Math.round(a.pedido_sugerido)
  if (a.unidades_por_caja <= 1) return `${unidades} u.`
  const cajas = Math.round(unidades / a.unidades_por_caja)
  return `${cajas} ${cajas === 1 ? 'caja' : 'cajas'} (${unidades} u.)`
}

export function TablaAlertasReorden({ alertas, sinDatos }: { alertas: AlertaReorden[]; sinDatos: number }) {
  return (
    <Seccion
      titulo="Alertas de reorden"
      descripcion="Stock total (todas las sucursales) en o por debajo del punto de reorden. Pedido sugerido = EOQ redondeado a cajas cerradas."
    >
      {alertas.length === 0 ? (
        <Vacio texto="Ninguna herramienta llegó a su punto de reorden." />
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-2">Herramienta</th>
              <th className="px-4 py-2 text-right">Stock total</th>
              <th className="px-4 py-2 text-right">Punto de reorden</th>
              <th className="px-4 py-2 text-right">Pedido sugerido</th>
            </tr>
          </thead>
          <tbody>
            {alertas.map((a) => (
              <tr key={a.herramienta_id} className="border-t border-slate-100">
                <td className="px-4 py-2">
                  <span className="font-medium text-slate-800">{a.codigo}</span>{' '}
                  <span className="text-slate-600">{a.nombre}</span>
                </td>
                <td className="px-4 py-2 text-right tabular-nums">{a.stock_total}</td>
                <td className="px-4 py-2 text-right tabular-nums">{a.punto_reorden}</td>
                <td className="px-4 py-2 text-right tabular-nums">
                  {a.pedido_sugerido === null ? (
                    <span className="text-xs text-slate-500">Faltan costos en el catálogo</span>
                  ) : (
                    pedidoEnCajas(a)
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {sinDatos > 0 && (
        <p className="border-t border-slate-100 px-4 py-2 text-xs text-slate-500">
          {sinDatos} {sinDatos === 1 ? 'herramienta no tiene' : 'herramientas no tienen'} demanda anual o tiempo de
          entrega, así que no se puede calcular su punto de reorden.{' '}
          <Link to="/catalogo" className="text-blue-600 hover:underline">Completar en el catálogo →</Link>
        </p>
      )}
    </Seccion>
  )
}

export function TablaEstancadas({ estancadas, dias }: { estancadas: HerramientaEstancada[]; dias: number }) {
  return (
    <Seccion
      titulo={`Sin ventas hace más de ${dias} días`}
      descripcion="Herramientas con stock en una sucursal que no registran salidas (los ajustes no cuentan como venta)."
    >
      {estancadas.length === 0 ? (
        <Vacio texto="No hay herramientas estancadas." />
      ) : (
        <table className="w-full text-left text-sm">
          <thead className="bg-slate-50 text-slate-600">
            <tr>
              <th className="px-4 py-2">Herramienta</th>
              <th className="px-4 py-2">Sucursal</th>
              <th className="px-4 py-2 text-right">Stock</th>
              <th className="px-4 py-2 text-right">Días sin venta</th>
            </tr>
          </thead>
          <tbody>
            {estancadas.map((e) => (
              <tr key={`${e.herramienta_id}-${e.sucursal_id}`} className="border-t border-slate-100">
                <td className="px-4 py-2">
                  <span className="font-medium text-slate-800">{e.codigo}</span>{' '}
                  <span className="text-slate-600">{e.nombre}</span>
                </td>
                <td className="px-4 py-2">{e.sucursal_nombre}</td>
                <td className="px-4 py-2 text-right tabular-nums">{e.stock}</td>
                <td className="px-4 py-2 text-right tabular-nums">
                  {e.dias_sin_venta}
                  {e.nunca_vendida && <span className="block text-xs text-slate-500">nunca vendida</span>}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </Seccion>
  )
}
