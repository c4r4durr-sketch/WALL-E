import { Warehouse } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { bs, bsCorto, fechaCorta, miles } from '../../../../shared/formato'
import type { StockSucursal } from '../../api/estadisticasApi'
import { CajaTooltip, Leyenda, TarjetaGrafico } from './comun'
import { COLOR, EJE, GRILLA, tooltipDe, useAnimacion } from './estilo'

// Barras: unidades en stock (gris, eje izquierdo) y su valor en Bs
// (naranja, eje derecho) de cada sucursal, al cierre del día "hasta".

interface Props {
  sucursales: StockSucursal[] | undefined
  hasta: string
  cargando: boolean
  error: unknown
  onReintentar: () => void
}

interface Fila extends StockSucursal {
  valorNumero: number
}

const Contenido = tooltipDe<Fila>((s) => (
  <CajaTooltip
    titulo={s.nombre}
    filas={[
      { color: COLOR.secundario, texto: 'Unidades', valor: miles(s.unidades) },
      { color: COLOR.principal, texto: 'Valor (al costo)', valor: bs(s.valorNumero) },
      ...(s.unidades_sin_costo ? [{ texto: 'Unidades sin costo', valor: miles(s.unidades_sin_costo) }] : []),
    ]}
  />
))

export function GraficoStockSucursal({ sucursales, hasta, cargando, error, onReintentar }: Props) {
  const animacion = useAnimacion()
  const filas: Fila[] | undefined = sucursales?.map((s) => ({ ...s, valorNumero: Number(s.valor) }))
  return (
    <TarjetaGrafico
      titulo="Stock y valor por sucursal"
      descripcion={`Unidades en stock y su valor al costo, al cierre del ${fechaCorta(hasta)}.`}
      cargando={cargando}
      error={error}
      onReintentar={onReintentar}
      vacio={!filas?.length}
      iconoVacio={Warehouse}
      ayudaVacio="La sucursal no tenía stock registrado a esa fecha."
      leyenda={
        <Leyenda items={[
          { color: COLOR.secundario, texto: 'Unidades (eje izquierdo)' },
          { color: COLOR.principal, texto: 'Valor en Bs (eje derecho)' },
        ]} />
      }
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} margin={{ top: 8, right: 4, bottom: 0, left: 0 }} barGap={6}>
          <CartesianGrid {...GRILLA} vertical={false} />
          <XAxis dataKey="nombre" {...EJE} tick={{ ...EJE.tick, fill: COLOR.tinta }} />
          <YAxis yAxisId="unidades" tickFormatter={miles} width={52} allowDecimals={false} {...EJE} />
          <YAxis yAxisId="valor" orientation="right" tickFormatter={bsCorto} width={76} {...EJE} />
          <Tooltip content={Contenido} cursor={{ fill: COLOR.grilla }} />
          <Bar yAxisId="unidades" dataKey="unidades" name="Unidades" fill={COLOR.secundario} radius={[6, 6, 0, 0]} maxBarSize={48} {...animacion} />
          <Bar yAxisId="valor" dataKey="valorNumero" name="Valor" fill={COLOR.principal} radius={[6, 6, 0, 0]} maxBarSize={48} {...animacion} />
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafico>
  )
}
