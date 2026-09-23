import { Link } from 'react-router-dom'
import { useEOQ, useROP } from '../hooks/useIndicadores'

// Detalle de una herramienta: cuánto pedir (EOQ, ajustado a cajas) y cuándo
// pedir (punto de reorden vs stock total). Si faltan datos en el catálogo,
// se dice cuáles en vez de mostrar un número inventado.

const NOMBRE_CAMPO: Record<string, string> = {
  demanda_anual: 'demanda anual',
  costo_pedido: 'costo por pedido',
  costo_almacenamiento_unitario: 'costo de almacenamiento (mayor a 0)',
  tiempo_entrega_dias: 'tiempo de entrega',
}

function Faltantes({ campos }: { campos: string[] }) {
  return (
    <p className="mt-2 text-sm text-slate-600">
      Faltan datos en el catálogo: {campos.map((c) => NOMBRE_CAMPO[c] ?? c).join(', ')}.{' '}
      <Link to="/catalogo" className="text-blue-600 hover:underline">Completar →</Link>
    </p>
  )
}

function Dato({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="flex justify-between gap-4 text-sm">
      <dt className="text-slate-500">{etiqueta}</dt>
      <dd className="tabular-nums text-slate-800">{valor}</dd>
    </div>
  )
}

const num = (v: number | null, sufijo = '') => (v === null ? '—' : `${v.toLocaleString('es')}${sufijo}`)

export function DetalleEOQROP({ herramientaId }: { herramientaId: number }) {
  const eoq = useEOQ(herramientaId)
  const rop = useROP(herramientaId)

  if (eoq.isLoading || rop.isLoading) return <p className="text-sm text-slate-500">Calculando...</p>
  if (eoq.isError || rop.isError || !eoq.data || !rop.data) {
    return <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">No se pudieron calcular los indicadores.</p>
  }
  const e = eoq.data
  const r = rop.data
  const cajas = e.eoq_ajustado_cajas !== null && e.unidades_por_caja > 1 ? Math.round(e.eoq_ajustado_cajas / e.unidades_por_caja) : null

  return (
    <section className="space-y-3">
      <h2 className="text-lg font-semibold text-slate-800">{e.codigo} · {e.nombre}</h2>
      <div className="grid gap-3 md:grid-cols-2">
        <div className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm">
          <p className="text-sm text-slate-500">Cuánto pedir (EOQ)</p>
          {e.eoq === null ? (
            <Faltantes campos={e.datos_faltantes} />
          ) : (
            <>
              <p className="mt-1 text-3xl font-semibold tabular-nums text-slate-900">
                {num(e.eoq_ajustado_cajas)} <span className="text-base font-normal text-slate-500">unidades</span>
              </p>
              <p className="text-xs text-slate-500">
                {cajas !== null ? `${cajas} ${cajas === 1 ? 'caja cerrada' : 'cajas cerradas'} · ` : ''}EOQ exacto {num(e.eoq)}
              </p>
            </>
          )}
          <dl className="mt-3 space-y-1 border-t border-slate-100 pt-3">
            <Dato etiqueta="Demanda anual estimada (D)" valor={num(e.demanda_anual)} />
            <Dato etiqueta="Vendido en los últimos 12 meses" valor={num(e.demanda_observada)} />
            <Dato etiqueta="Costo por pedido (S)" valor={num(e.costo_pedido)} />
            <Dato etiqueta="Costo de almacenamiento (H)" valor={num(e.costo_almacenamiento_unitario)} />
          </dl>
        </div>

        <div className={`rounded-lg border bg-white p-4 shadow-sm ${r.requiere_reorden ? 'border-amber-300' : 'border-slate-200'}`}>
          <p className="text-sm text-slate-500">Cuándo pedir (punto de reorden)</p>
          {r.punto_reorden === null ? (
            <Faltantes campos={r.datos_faltantes} />
          ) : (
            <>
              <p className="mt-1 text-3xl font-semibold tabular-nums text-slate-900">
                {num(r.punto_reorden)} <span className="text-base font-normal text-slate-500">unidades</span>
              </p>
              {r.requiere_reorden ? (
                <p className="mt-1 flex items-center gap-1 text-xs font-medium text-amber-800">
                  <svg aria-hidden="true" viewBox="0 0 20 20" className="h-3.5 w-3.5 fill-current">
                    <path d="M10 2 1 18h18L10 2Zm-1 6h2v5H9V8Zm0 6h2v2H9v-2Z" />
                  </svg>
                  Hay que pedir: el stock total ya está en o bajo este punto
                </p>
              ) : (
                <p className="text-xs text-slate-500">Todavía no hace falta pedir</p>
              )}
            </>
          )}
          <dl className="mt-3 space-y-1 border-t border-slate-100 pt-3">
            <Dato etiqueta="Stock total (todas las sucursales)" valor={num(r.stock_total)} />
            <Dato etiqueta="Demanda diaria promedio" valor={num(r.demanda_diaria_promedio)} />
            <Dato etiqueta="Tiempo de entrega" valor={num(r.lead_time_dias, ' días')} />
          </dl>
        </div>
      </div>
    </section>
  )
}
