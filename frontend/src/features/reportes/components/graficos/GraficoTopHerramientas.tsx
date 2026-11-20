import { BarChartHorizontal } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { bs, miles } from '../../../../shared/formato'
import type { VentaHerramienta } from '../../api/estadisticasApi'
import { CajaTooltip, TarjetaGrafico } from './comun'
import { COLOR, EJE, GRILLA, tooltipDe, useAnimacion } from './estilo'

// Barras horizontales: las 10 herramientas con más unidades vendidas; el
// tooltip suma el monto (salidas × costo unitario).

interface Props {
  herramientas: VentaHerramienta[] | undefined
  cargando: boolean
  error: unknown
  onReintentar: () => void
}

const Contenido = tooltipDe<VentaHerramienta>((h) => (
  <CajaTooltip
    titulo={`${h.codigo} · ${h.nombre}`}
    filas={[
      { color: COLOR.principal, texto: 'Unidades vendidas', valor: miles(h.unidades) },
      { texto: 'Monto (al costo)', valor: h.monto === null ? 'Sin costo cargado' : bs(Number(h.monto)) },
    ]}
  />
))

export function GraficoTopHerramientas({ herramientas, cargando, error, onReintentar }: Props) {
  const animacion = useAnimacion()
  return (
    <TarjetaGrafico
      titulo="Top 10 herramientas vendidas"
      descripcion="Las que más unidades vendieron en el periodo."
      cargando={cargando}
      error={error}
      onReintentar={onReintentar}
      vacio={!herramientas?.length}
      iconoVacio={BarChartHorizontal}
      ayudaVacio="No hubo ventas en el periodo elegido."
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={herramientas} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 0 }} barCategoryGap={6}>
          <CartesianGrid {...GRILLA} horizontal={false} />
          <XAxis type="number" tickFormatter={miles} allowDecimals={false} {...EJE} />
          <YAxis type="category" dataKey="codigo" width={92} interval={0} {...EJE} tick={{ ...EJE.tick, fill: COLOR.tinta }} />
          <Tooltip content={Contenido} cursor={{ fill: COLOR.grilla }} />
          <Bar dataKey="unidades" name="Unidades vendidas" fill={COLOR.principal} radius={[0, 6, 6, 0]} maxBarSize={22} {...animacion} />
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafico>
  )
}
