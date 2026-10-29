import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { AlertTriangle, CheckCircle2 } from 'lucide-react'
import { Aviso, Card, Cargando, Skeleton, cx } from '../../../components/ui'
import { useEOQ, useROP } from '../hooks/useIndicadores'

// Detalle de una herramienta: cuánto pedir (EOQ, ajustado a cajas) y cuándo
// pedir (punto de reorden vs stock total). Si faltan datos en el catálogo,
// se dice cuáles en vez de mostrar un número inventado. HU21: los dos usan
// lo vendido en los últimos 12 meses; la demanda estimada del catálogo solo
// cuando no hubo ventas. La tarjeta dice cuál se usó.

const NOMBRE_CAMPO: Record<string, string> = {
  demanda_anual: 'demanda anual',
  costo_pedido: 'costo por pedido',
  costo_almacenamiento_unitario: 'costo de almacenamiento (mayor a 0)',
  tiempo_entrega_dias: 'tiempo de entrega',
}

function Faltantes({ campos }: { campos: string[] }) {
  return (
    <Aviso tono="advertencia" className="mt-3">
      Faltan datos en el catálogo: {campos.map((c) => NOMBRE_CAMPO[c] ?? c).join(', ')}.{' '}
      <Link to="/catalogo" className="underline">Completar</Link>
    </Aviso>
  )
}

function Dato({ etiqueta, valor }: { etiqueta: string; valor: string }) {
  return (
    <div className="flex h-10 items-center justify-between gap-4 text-sm">
      <dt className="text-muted">{etiqueta}</dt>
      <dd className="font-semibold text-ink tabular-nums">{valor}</dd>
    </div>
  )
}

function Numero({ valor, unidad }: { valor: string; unidad: string }) {
  return (
    <p className="mt-2 text-[32px] font-bold leading-none tracking-[-0.03em] text-ink tabular-nums">
      {valor} <span className="text-sm font-medium tracking-normal text-muted">{unidad}</span>
    </p>
  )
}

function Tarjeta({ titulo, children, alerta = false }: { titulo: string; children: ReactNode; alerta?: boolean }) {
  return (
    <Card className={cx(alerta && 'ring-2 ring-warn')}>
      <p className="text-xs font-semibold text-muted">{titulo}</p>
      {children}
    </Card>
  )
}

const num = (v: number | null, sufijo = '') => (v === null ? '—' : `${v.toLocaleString('es')}${sufijo}`)

function FuenteDemanda({ fuente }: { fuente: 'OBSERVADA' | 'ESTIMADA' }) {
  return (
    <p className="mt-3 text-xs text-muted">
      {fuente === 'OBSERVADA'
        ? 'Calculado con lo vendido en los últimos 12 meses.'
        : 'Sin ventas en los últimos 12 meses: calculado con la demanda estimada del catálogo.'}
    </p>
  )
}

export function DetalleEOQROP({ herramientaId }: { herramientaId: number }) {
  const eoq = useEOQ(herramientaId)
  const rop = useROP(herramientaId)

  if (eoq.isLoading || rop.isLoading) {
    return (
      <Cargando etiqueta="Calculando indicadores">
        <div className="grid grid-cols-2 gap-5">
          {[0, 1].map((i) => (
            <div key={i} className="space-y-4 rounded-[26px] bg-surf p-6 shadow-sh">
              <Skeleton className="h-3 w-1/3" />
              <Skeleton className="h-9 w-1/2" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-full" />
              <Skeleton className="h-3 w-2/3" />
            </div>
          ))}
        </div>
      </Cargando>
    )
  }
  if (eoq.isError || rop.isError || !eoq.data || !rop.data) {
    return <Aviso tono="error">No se pudieron calcular los indicadores.</Aviso>
  }
  const e = eoq.data
  const r = rop.data
  const cajas = e.eoq_ajustado_cajas !== null && e.unidades_por_caja > 1 ? Math.round(e.eoq_ajustado_cajas / e.unidades_por_caja) : null

  return (
    <div className="grid grid-cols-2 gap-5">
      <Tarjeta titulo="Cuánto pedir (EOQ)">
        {e.eoq === null ? (
          <Faltantes campos={e.datos_faltantes} />
        ) : (
          <>
            <Numero valor={num(e.eoq_ajustado_cajas)} unidad="unidades" />
            <p className="mt-2 text-xs text-muted tabular-nums">
              {cajas !== null ? `${cajas} ${cajas === 1 ? 'caja cerrada' : 'cajas cerradas'} · ` : ''}EOQ exacto {num(e.eoq)}
            </p>
          </>
        )}
        <dl className="mt-5 divide-y divide-line border-t border-line">
          <Dato etiqueta="Vendido en los últimos 12 meses" valor={num(e.demanda_observada)} />
          <Dato etiqueta="Demanda anual estimada (catálogo)" valor={num(e.demanda_anual)} />
          <Dato etiqueta="Costo por pedido (S)" valor={num(e.costo_pedido)} />
          <Dato etiqueta="Costo de almacenamiento (H)" valor={num(e.costo_almacenamiento_unitario)} />
        </dl>
        <FuenteDemanda fuente={e.fuente_demanda} />
      </Tarjeta>

      <Tarjeta titulo="Cuándo pedir (punto de reorden)" alerta={r.requiere_reorden}>
        {r.punto_reorden === null ? (
          <Faltantes campos={r.datos_faltantes} />
        ) : (
          <>
            <Numero valor={num(r.punto_reorden)} unidad="unidades" />
            {r.requiere_reorden ? (
              <p className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-warn">
                <AlertTriangle size={14} aria-hidden />
                Hay que pedir: el stock total ya está en o bajo este punto
              </p>
            ) : (
              <p className="mt-2 inline-flex items-center gap-1.5 text-xs font-semibold text-ok">
                <CheckCircle2 size={14} aria-hidden />
                Todavía no hace falta pedir
              </p>
            )}
          </>
        )}
        <dl className="mt-5 divide-y divide-line border-t border-line">
          <Dato etiqueta="Stock total (todas las sucursales)" valor={num(r.stock_total)} />
          <Dato etiqueta="Demanda diaria promedio" valor={num(r.demanda_diaria_promedio)} />
          <Dato etiqueta="Tiempo de entrega" valor={num(r.lead_time_dias, ' días')} />
        </dl>
        <FuenteDemanda fuente={r.fuente_demanda} />
      </Tarjeta>
    </div>
  )
}
