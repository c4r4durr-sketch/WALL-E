import { PieChart as IconoDona } from 'lucide-react'
import { Cell, Label, Pie, PieChart, ResponsiveContainer, Tooltip } from 'recharts'
import { miles } from '../../../../shared/formato'
import type { EstadoTransferencia } from '../../api/estadisticasApi'
import { CajaTooltip, TarjetaGrafico } from './comun'
import { COLOR, tooltipDe, useAnimacion } from './estilo'

// Dona: transferencias solicitadas en el periodo según su estado actual.
// Completadas en naranja; pendientes y rechazadas en grises. Al lado, la
// lista con la cantidad y el porcentaje de cada estado.

const ESTADOS: Record<EstadoTransferencia, { texto: string; color: string }> = {
  COMPLETADA: { texto: 'Completadas', color: COLOR.principal },
  PENDIENTE: { texto: 'Pendientes', color: COLOR.secundario },
  RECHAZADA: { texto: 'Rechazadas', color: COLOR.tenue },
}

interface Props {
  porEstado: { estado: EstadoTransferencia; cantidad: number }[] | undefined
  total: number
  cargando: boolean
  error: unknown
  onReintentar: () => void
}

interface Fila {
  estado: EstadoTransferencia
  cantidad: number
  porcentaje: number
}

const Contenido = tooltipDe<Fila>((f) => (
  <CajaTooltip
    titulo={ESTADOS[f.estado].texto}
    filas={[{ color: ESTADOS[f.estado].color, texto: 'Transferencias', valor: `${miles(f.cantidad)} (${f.porcentaje} %)` }]}
  />
))

export function GraficoTransferencias({ porEstado, total, cargando, error, onReintentar }: Props) {
  const animacion = useAnimacion()
  const filas: Fila[] = (porEstado ?? []).map((e) => ({
    ...e,
    porcentaje: total ? Math.round((e.cantidad * 1000) / total) / 10 : 0,
  }))
  return (
    <TarjetaGrafico
      titulo="Transferencias por estado"
      descripcion="Solicitudes entre sucursales del periodo, según cómo terminaron."
      cargando={cargando}
      error={error}
      onReintentar={onReintentar}
      vacio={total === 0}
      iconoVacio={IconoDona}
      ayudaVacio="No se solicitaron transferencias en el periodo elegido."
    >
      <div className="flex h-full items-center gap-6">
        <div className="h-full min-w-0 flex-1">
          <ResponsiveContainer width="100%" height="100%">
            <PieChart>
              <Tooltip content={Contenido} />
              <Pie
                data={filas.filter((f) => f.cantidad > 0)}
                dataKey="cantidad"
                nameKey="estado"
                innerRadius="62%"
                outerRadius="92%"
                paddingAngle={2}
                stroke={COLOR.fondo}
                strokeWidth={2}
                {...animacion}
              >
                {filas.filter((f) => f.cantidad > 0).map((f) => <Cell key={f.estado} fill={ESTADOS[f.estado].color} />)}
                <Label
                  position="center"
                  content={({ viewBox }) => {
                    const { cx = 0, cy = 0 } = (viewBox ?? {}) as { cx?: number; cy?: number }
                    return (
                      <text x={cx} y={cy} textAnchor="middle" dominantBaseline="central">
                        <tspan x={cx} dy="-0.4em" fill={COLOR.tinta} fontSize="26" fontWeight="700">{miles(total)}</tspan>
                        <tspan x={cx} dy="1.6em" fill={COLOR.texto} fontSize="12">en total</tspan>
                      </text>
                    )
                  }}
                />
              </Pie>
            </PieChart>
          </ResponsiveContainer>
        </div>
        <ul className="w-44 space-y-3">
          {filas.map((f) => (
            <li key={f.estado}>
              <p className="flex items-center gap-2 text-xs font-semibold text-muted">
                <span className="h-2.5 w-2.5 rounded-[3px]" style={{ background: ESTADOS[f.estado].color }} aria-hidden />
                {ESTADOS[f.estado].texto}
              </p>
              <p className="mt-0.5 text-lg font-bold tracking-[-0.03em] text-ink tabular-nums">
                {miles(f.cantidad)} <span className="text-xs font-medium tracking-normal text-muted">{f.porcentaje} %</span>
              </p>
            </li>
          ))}
        </ul>
      </div>
    </TarjetaGrafico>
  )
}
