import { LineChart as IconoLineas } from 'lucide-react'
import { CartesianGrid, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { mesCorto, mesLargo, miles } from '../../../../shared/formato'
import type { MovimientosMes } from '../../api/estadisticasApi'
import { CajaTooltip, Leyenda, TarjetaGrafico } from './comun'
import { COLOR, EJE, GRILLA, tooltipDe, useAnimacion } from './estilo'

// Líneas: unidades que entraron y salieron (ventas) cada mes. Las salidas
// en naranja (lo principal) y las entradas en gris punteado, para que se
// distingan también impresas en blanco y negro.

interface Props {
  meses: MovimientosMes[] | undefined
  cargando: boolean
  error: unknown
  onReintentar: () => void
}

const Contenido = tooltipDe<MovimientosMes>((m) => (
  <CajaTooltip
    titulo={mesLargo(m.mes)}
    filas={[
      { color: COLOR.principal, texto: 'Salidas', valor: `${miles(m.salidas)} u.` },
      { color: COLOR.secundario, texto: 'Entradas', valor: `${miles(m.entradas)} u.` },
      ...(m.ajustes_positivos || m.ajustes_negativos
        ? [{ texto: 'Ajustes + / −', valor: `${miles(m.ajustes_positivos)} / ${miles(m.ajustes_negativos)}` }]
        : []),
    ]}
  />
))

export function GraficoMovimientos({ meses, cargando, error, onReintentar }: Props) {
  const animacion = useAnimacion()
  return (
    <TarjetaGrafico
      titulo="Entradas y salidas por mes"
      descripcion="Unidades que ingresaron y que se vendieron cada mes."
      cargando={cargando}
      error={error}
      onReintentar={onReintentar}
      vacio={!meses?.length}
      iconoVacio={IconoLineas}
      ayudaVacio="No se registraron movimientos en el periodo elegido."
      leyenda={
        <Leyenda items={[
          { color: COLOR.principal, texto: 'Salidas', linea: true },
          { color: COLOR.secundario, texto: 'Entradas', punteada: true },
        ]} />
      }
    >
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={meses} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
          <CartesianGrid {...GRILLA} vertical={false} />
          <XAxis dataKey="mes" tickFormatter={mesCorto} {...EJE} />
          <YAxis tickFormatter={miles} width={52} allowDecimals={false} {...EJE} />
          <Tooltip content={Contenido} cursor={{ stroke: COLOR.grilla }} />
          <Line type="monotone" dataKey="entradas" name="Entradas" stroke={COLOR.secundario} strokeWidth={2} strokeDasharray="6 4" dot={false} activeDot={{ r: 4 }} {...animacion} />
          <Line type="monotone" dataKey="salidas" name="Salidas" stroke={COLOR.principal} strokeWidth={2.5} dot={false} activeDot={{ r: 4 }} {...animacion} />
        </LineChart>
      </ResponsiveContainer>
    </TarjetaGrafico>
  )
}
