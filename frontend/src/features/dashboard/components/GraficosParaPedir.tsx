import { BarChart3, BarChartHorizontal } from 'lucide-react'
import { Bar, BarChart, CartesianGrid, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { decimal, miles } from '../../../shared/formato'
import { CajaTooltip, Leyenda, TarjetaGrafico } from '../../reportes/components/graficos/comun'
import { COLOR, EJE, GRILLA, tooltipDe, useAnimacion } from '../../reportes/components/graficos/estilo'
import type { ReposicionSucursal } from '../api/indicadoresApi'
import { pedidoEnCajas } from '../formato'

// Gráficos de /productos-para-pedir, con las mismas piezas que /reportes
// (colores como variables CSS: siguen al tema claro/oscuro). Reciben las
// líneas ya filtradas por la sucursal elegida en la página.

interface SucursalBasica {
  id: number
  nombre: string
}

// ---------- Productos para pedir por sucursal ----------

interface FilaSucursal {
  nombre: string
  productos: number
}

const ContenidoSucursal = tooltipDe<FilaSucursal>((s) => (
  <CajaTooltip
    titulo={s.nombre}
    filas={[{ color: COLOR.principal, texto: 'Productos para pedir', valor: miles(s.productos) }]}
  />
))

// Cuenta las líneas de cada sucursal. Con "Todas" se muestran también las
// sucursales activas sin nada que pedir (barra en 0); con una sucursal
// elegida, solo esa.
function contarPorSucursal(lineas: ReposicionSucursal[], sucursales: SucursalBasica[]): FilaSucursal[] {
  const conteo = new Map<number, FilaSucursal>()
  for (const s of sucursales) conteo.set(s.id, { nombre: s.nombre, productos: 0 })
  for (const l of lineas) {
    const fila = conteo.get(l.sucursal_id) ?? { nombre: l.sucursal_nombre, productos: 0 }
    fila.productos += 1
    conteo.set(l.sucursal_id, fila)
  }
  return [...conteo.values()]
}

export function GraficoPedirPorSucursal({
  lineas,
  sucursales,
}: {
  lineas: ReposicionSucursal[]
  sucursales: SucursalBasica[]
}) {
  const animacion = useAnimacion()
  const filas = contarPorSucursal(lineas, sucursales)
  return (
    <TarjetaGrafico
      titulo="Productos para pedir por sucursal"
      descripcion="Cuántas herramientas llegaron a su punto de reorden en cada sucursal."
      cargando={false}
      vacio={filas.length === 0}
      iconoVacio={BarChart3}
      ayudaVacio="Ninguna sucursal tiene productos para pedir."
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} margin={{ top: 8, right: 4, bottom: 0, left: 0 }}>
          <CartesianGrid {...GRILLA} vertical={false} />
          <XAxis dataKey="nombre" interval={0} {...EJE} tick={{ ...EJE.tick, fill: COLOR.tinta }} />
          <YAxis tickFormatter={miles} width={40} allowDecimals={false} {...EJE} />
          <Tooltip content={ContenidoSucursal} cursor={{ fill: COLOR.grilla }} />
          <Bar dataKey="productos" name="Productos para pedir" fill={COLOR.principal} radius={[6, 6, 0, 0]} maxBarSize={48} {...animacion} />
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafico>
  )
}

// ---------- Stock actual frente al punto de reorden ----------

interface FilaUrgencia {
  clave: string
  etiqueta: string
  linea: ReposicionSucursal
  stock: number
  rop: number
}

const ContenidoUrgencia = tooltipDe<FilaUrgencia>(({ linea, stock, rop }) => (
  <CajaTooltip
    titulo={`${linea.codigo} · ${linea.nombre}`}
    filas={[
      { texto: 'Sucursal', valor: linea.sucursal_nombre },
      { color: COLOR.principal, texto: 'Stock actual', valor: miles(stock) },
      { color: COLOR.tenue, texto: 'Punto de reorden', valor: decimal(rop) },
      { texto: 'Por debajo del ROP', valor: decimal(Math.max(rop - stock, 0)) },
      {
        texto: 'Pedido sugerido',
        valor: linea.eoq_ajustado_cajas === null ? 'Faltan costos' : pedidoEnCajas(linea.eoq_ajustado_cajas, linea.unidades_por_caja),
      },
    ]}
  />
))

const ALTO_FILA = 34

export function GraficoStockVsRop({ lineas, unaSucursal }: { lineas: ReposicionSucursal[]; unaSucursal: boolean }) {
  const animacion = useAnimacion()
  // Más urgente primero: la que está más por debajo de su ROP (mismo
  // criterio que la tabla).
  const filas: FilaUrgencia[] = lineas
    .filter((l) => l.punto_reorden !== null)
    .map((l) => ({
      clave: `${l.herramienta_id}-${l.sucursal_id}`,
      // Con "Todas" una herramienta puede salir en varias sucursales.
      etiqueta: unaSucursal ? l.codigo : `${l.codigo} · ${l.sucursal_nombre}`,
      linea: l,
      stock: l.stock,
      rop: l.punto_reorden as number,
    }))
    .sort((a, b) => a.stock - a.rop - (b.stock - b.rop))
  const etiquetaDe = new Map(filas.map((f) => [f.clave, f.etiqueta]))
  return (
    <TarjetaGrafico
      titulo="Stock actual frente al punto de reorden"
      descripcion="Cada producto de la lista, del más urgente (más por debajo de su ROP) al menos urgente."
      cargando={false}
      vacio={filas.length === 0}
      iconoVacio={BarChartHorizontal}
      ayudaVacio="No hay productos con punto de reorden calculado."
      alto={Math.max(filas.length * ALTO_FILA + 32, 160)}
      leyenda={
        <Leyenda items={[
          { color: COLOR.principal, texto: 'Stock actual' },
          { color: COLOR.tenue, texto: 'Punto de reorden' },
        ]} />
      }
    >
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={filas} layout="vertical" margin={{ top: 0, right: 16, bottom: 0, left: 0 }} barGap={2} barCategoryGap={6}>
          <CartesianGrid {...GRILLA} horizontal={false} />
          <XAxis type="number" tickFormatter={miles} allowDecimals={false} {...EJE} />
          <YAxis
            type="category"
            dataKey="clave"
            tickFormatter={(clave: string) => etiquetaDe.get(clave) ?? clave}
            width={unaSucursal ? 92 : 170}
            interval={0}
            {...EJE}
            tick={{ ...EJE.tick, fill: COLOR.tinta }}
          />
          <Tooltip content={ContenidoUrgencia} cursor={{ fill: COLOR.grilla }} />
          <Bar dataKey="stock" name="Stock actual" fill={COLOR.principal} radius={[0, 6, 6, 0]} maxBarSize={12} {...animacion} />
          <Bar dataKey="rop" name="Punto de reorden" fill={COLOR.tenue} radius={[0, 6, 6, 0]} maxBarSize={12} {...animacion} />
        </BarChart>
      </ResponsiveContainer>
    </TarjetaGrafico>
  )
}
