import { Hourglass } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { bs, bsCorto, fechaCorta, miles } from '../../../../shared/formato'
import type { TramoValor } from '../../api/estadisticasApi'
import { CajaTooltip, TarjetaGrafico } from './comun'
import { COLOR, EJE, GRILLA, tooltipDe, useAnimacion } from './estilo'

// Barras: dinero inmovilizado (stock × costo) según los días sin venta, al
// cierre del día "hasta". Lo reciente en grises y lo estancado (más de 40
// días) en naranja, más fuerte cuanto más viejo.

const COLOR_TRAMO = [COLOR.tenue, COLOR.secundario, COLOR.principal, COLOR.principal]
const OPACIDAD_TRAMO = [1, 1, 0.6, 1]

interface Props {
  tramos: TramoValor[] | undefined
  hasta: string
  sinCosto: number
  cargando: boolean
  error: unknown
  onReintentar: () => void
}

interface Fila extends TramoValor {
  valorNumero: number
}

const Contenido = tooltipDe<Fila>((t) => (
  <CajaTooltip
    titulo={t.tramo}
    filas={[
      { texto: 'Valor inmovilizado', valor: bs(t.valorNumero) },
      { texto: 'Unidades', valor: miles(t.unidades) },
      { texto: 'Herramientas por sucursal', valor: miles(t.herramientas) },
    ]}
  />
))

export function GraficoAntiguedad({ tramos, hasta, sinCosto, cargando, error, onReintentar }: Props) {
  const animacion = useAnimacion()
  const filas: Fila[] | undefined = tramos?.map((t) => ({ ...t, valorNumero: Number(t.valor) }))
  return (
    <TarjetaGrafico
      titulo="Valor inmovilizado por antigüedad"
      descripcion={`Dinero en stock según los días sin venta, al cierre del ${fechaCorta(hasta)}.`}
      cargando={cargando}
      error={error}
      onReintentar={onReintentar}
      vacio={!filas?.length}
      iconoVacio={Hourglass}
      ayudaVacio="No había stock a esa fecha."
      pie={
        <p className="text-xs text-muted">
          Más de 40 días sin venta = estancada.
          {sinCosto > 0 && ` ${sinCosto} líneas sin costo cargado no suman valor.`}
        </p>
      }
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} margin={{ top: 8, right: 4, bottom: 0, left: 0 }}>
          <CartesianGrid {...GRILLA} vertical={false} />
          <XAxis dataKey="tramo" {...EJE} tick={{ ...EJE.tick, fill: COLOR.tinta }} />
          <YAxis tickFormatter={bsCorto} width={76} {...EJE} />
          <Tooltip content={Contenido} cursor={{ fill: COLOR.grilla }} />
          <Bar dataKey="valorNumero" name="Valor inmovilizado" radius={[6, 6, 0, 0]} maxBarSize={64} {...animacion}>
            {filas?.map((t, i) => <Cell key={t.tramo} fill={COLOR_TRAMO[i]} fillOpacity={OPACIDAD_TRAMO[i]} />)}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafico>
  )
}
