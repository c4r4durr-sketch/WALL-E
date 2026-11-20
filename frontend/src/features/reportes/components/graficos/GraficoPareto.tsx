import { BarChart3 } from 'lucide-react'
import { Bar, CartesianGrid, Cell, ComposedChart, Line, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { bs, bsCorto } from '../../../../shared/formato'
import type { Clase, PuntoPareto, TotalClase } from '../../api/estadisticasApi'
import { CajaTooltip, Leyenda, TarjetaGrafico } from './comun'
import { COLOR, EJE, GRILLA, tooltipDe, useAnimacion } from './estilo'

// Pareto ABC: una barra por herramienta con su valor vendido, de mayor a
// menor y teñida por clase (A naranja, B y C grises), y la línea del %
// acumulado contra el eje derecho, con las marcas de 80 % y 95 % que
// separan las clases.

const COLOR_CLASE: Record<Clase, string> = { A: COLOR.principal, B: COLOR.secundario, C: COLOR.tenue }

// Con muchas herramientas los códigos no entran debajo de las barras.
const MAXIMO_CON_CODIGOS = 14

interface Props {
  pareto: PuntoPareto[] | undefined
  clases: TotalClase[] | undefined
  sinCosto: number
  cargando: boolean
  error: unknown
  onReintentar: () => void
}

interface Fila extends PuntoPareto {
  valorNumero: number
}

const Contenido = tooltipDe<Fila>((p) => (
  <CajaTooltip
    titulo={`${p.codigo} · ${p.nombre}`}
    filas={[
      { color: COLOR_CLASE[p.clase], texto: `Clase ${p.clase}`, valor: bs(p.valorNumero) },
      { texto: '% del valor', valor: `${p.porcentaje.toLocaleString('es')} %` },
      { color: COLOR.tinta, texto: '% acumulado', valor: `${p.porcentaje_acumulado.toLocaleString('es')} %` },
    ]}
  />
))

function ResumenClases({ clases, sinCosto }: { clases: TotalClase[]; sinCosto: number }) {
  return (
    <div>
      <ul className="grid grid-cols-3 gap-3">
        {clases.map((c) => (
          <li key={c.clase} className="rounded-card bg-surf2 px-4 py-3">
            <p className="flex items-center gap-2 text-xs font-semibold text-muted">
              <span className="h-2.5 w-2.5 rounded-[3px]" style={{ background: COLOR_CLASE[c.clase] }} aria-hidden />
              Clase {c.clase}
            </p>
            <p className="mt-1 text-lg font-bold tracking-[-0.03em] text-ink tabular-nums">
              {c.porcentaje_valor.toLocaleString('es')} %
            </p>
            <p className="text-xs text-muted tabular-nums">{c.herramientas} herramientas</p>
          </li>
        ))}
      </ul>
      {sinCosto > 0 && (
        <p className="mt-3 text-xs text-muted">{sinCosto} herramientas vendidas sin costo cargado quedan fuera del valor.</p>
      )}
    </div>
  )
}

export function GraficoPareto({ pareto, clases, sinCosto, cargando, error, onReintentar }: Props) {
  const animacion = useAnimacion()
  const filas: Fila[] | undefined = pareto?.map((p) => ({ ...p, valorNumero: Number(p.valor) }))
  const conCodigos = (filas?.length ?? 0) <= MAXIMO_CON_CODIGOS
  return (
    <TarjetaGrafico
      titulo="Clasificación ABC (Pareto)"
      descripcion="Valor vendido por herramienta y % acumulado: A hasta 80 %, B hasta 95 %."
      cargando={cargando}
      error={error}
      onReintentar={onReintentar}
      vacio={!filas?.length}
      iconoVacio={BarChart3}
      ayudaVacio="No hubo ventas con costo cargado en el periodo elegido."
      leyenda={
        <Leyenda items={[
          { color: COLOR.principal, texto: 'A' },
          { color: COLOR.secundario, texto: 'B' },
          { color: COLOR.tenue, texto: 'C' },
          { color: COLOR.tinta, texto: '% acumulado', linea: true },
        ]} />
      }
      pie={clases && clases.length > 0 && <ResumenClases clases={clases} sinCosto={sinCosto} />}
    >
      <ResponsiveContainer width="100%" height="100%">
        <ComposedChart data={filas} margin={{ top: 8, right: 4, bottom: 0, left: 0 }} barCategoryGap={conCodigos ? '20%' : 1}>
          <CartesianGrid {...GRILLA} vertical={false} />
          <XAxis dataKey="codigo" {...EJE} tick={conCodigos ? EJE.tick : false} interval={0} height={conCodigos ? 30 : 8} />
          <YAxis yAxisId="valor" tickFormatter={bsCorto} width={76} {...EJE} />
          <YAxis yAxisId="porcentaje" orientation="right" domain={[0, 100]} ticks={[0, 25, 50, 80, 95, 100]} tickFormatter={(v: number) => `${v} %`} width={48} {...EJE} />
          <ReferenceLine yAxisId="porcentaje" y={80} stroke={COLOR.texto} strokeDasharray="4 4" />
          <ReferenceLine yAxisId="porcentaje" y={95} stroke={COLOR.texto} strokeDasharray="4 4" />
          <Tooltip content={Contenido} cursor={{ fill: COLOR.grilla }} />
          <Bar yAxisId="valor" dataKey="valorNumero" name="Valor vendido" radius={[4, 4, 0, 0]} {...animacion}>
            {filas?.map((p) => <Cell key={p.herramienta_id} fill={COLOR_CLASE[p.clase]} />)}
          </Bar>
          <Line yAxisId="porcentaje" type="monotone" dataKey="porcentaje_acumulado" name="% acumulado" stroke={COLOR.tinta} strokeWidth={2} dot={conCodigos ? { r: 2.5, fill: COLOR.tinta } : false} {...animacion} />
        </ComposedChart>
      </ResponsiveContainer>
    </TarjetaGrafico>
  )
}
