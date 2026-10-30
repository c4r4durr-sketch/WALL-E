import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { CheckCircle2, Clock, type LucideIcon } from 'lucide-react'
import { Card, CardHeader, EmptyState, Table, THead, Td, Th, Tr, cx } from '../../../components/ui'
import { CeldaHerramienta } from '../../catalogo/components/CeldaHerramienta'
import { useFotos } from '../../catalogo/hooks/useFotos'
import { EtiquetaPromocion } from '../../promociones/components/EtiquetaPromocion'
import { usePromocionesVigentes } from '../../promociones/hooks/usePromociones'
import type { AlertaReorden, HerramientaEstancada } from '../api/indicadoresApi'

// Detalle de las alertas del panel y de la pantalla de reposición. Tablas
// (no gráficos): lo que importa es qué herramienta, cuánto hay y qué
// hacer, y eso se lee mejor en filas.

function Seccion({ titulo, descripcion, acciones, children }: {
  titulo: string
  descripcion: string
  acciones?: ReactNode
  children: ReactNode
}) {
  return (
    <Card sinPadding className="overflow-hidden">
      <CardHeader titulo={titulo} descripcion={descripcion} acciones={acciones} className="px-6 pb-4 pt-6" />
      {children}
    </Card>
  )
}

function Vacio({ icono, titulo, ayuda }: { icono: LucideIcon; titulo: string; ayuda: string }) {
  return <EmptyState compacto icono={icono} titulo={titulo} ayuda={ayuda} className="border-t border-line" />
}

function pedidoEnCajas(a: AlertaReorden): string {
  if (a.pedido_sugerido === null) return '—'
  const unidades = Math.round(a.pedido_sugerido)
  if (a.unidades_por_caja <= 1) return `${unidades} u.`
  const cajas = Math.round(unidades / a.unidades_por_caja)
  return `${cajas} ${cajas === 1 ? 'caja' : 'cajas'} (${unidades} u.)`
}

interface PropsAlertas {
  alertas: AlertaReorden[]
  sinDatos: number
  // En el panel se muestran las primeras y un enlace a la pantalla completa.
  limite?: number
}

export function TablaAlertasReorden({ alertas, sinDatos, limite }: PropsAlertas) {
  const foto = useFotos()
  const filas = limite ? alertas.slice(0, limite) : alertas
  return (
    <Seccion
      titulo="Alertas de reorden"
      descripcion="Stock total (todas las sucursales) en o por debajo del punto de reorden. Pedido sugerido = EOQ en cajas cerradas."
      acciones={
        limite && alertas.length > limite ? (
          <Link to="/reposicion" className="text-sm font-semibold text-softink hover:underline">
            Ver las {alertas.length}
          </Link>
        ) : undefined
      }
    >
      {alertas.length === 0 ? (
        <Vacio icono={CheckCircle2} titulo="Todo en orden" ayuda="Ninguna herramienta llegó a su punto de reorden." />
      ) : (
        <Table>
          <THead>
            <tr>
              <Th>Herramienta</Th>
              <Th numerico>Stock total</Th>
              <Th numerico>Punto de reorden</Th>
              <Th numerico>Pedido sugerido</Th>
            </tr>
          </THead>
          <tbody>
            {filas.map((a) => (
              <Tr key={a.herramienta_id}>
                <Td><CeldaHerramienta codigo={a.codigo} nombre={a.nombre} imagen={foto(a.herramienta_id)} /></Td>
                <Td numerico className="font-semibold text-warn">{a.stock_total}</Td>
                <Td numerico>{a.punto_reorden}</Td>
                <Td numerico>
                  {a.pedido_sugerido === null ? (
                    <span className="text-xs text-muted">Faltan costos en el catálogo</span>
                  ) : (
                    <span className="font-semibold">{pedidoEnCajas(a)}</span>
                  )}
                </Td>
              </Tr>
            ))}
          </tbody>
        </Table>
      )}
      {sinDatos > 0 && (
        <p className={cx('border-t border-line px-6 py-4 text-xs text-muted')}>
          {sinDatos} {sinDatos === 1 ? 'herramienta no tiene' : 'herramientas no tienen'} demanda anual o tiempo de
          entrega, así que no se puede calcular su punto de reorden.{' '}
          <Link to="/catalogo" className="font-semibold text-softink hover:underline">Completar en el catálogo</Link>
        </p>
      )}
    </Seccion>
  )
}

export function TablaEstancadas({ estancadas, dias }: { estancadas: HerramientaEstancada[]; dias: number }) {
  const foto = useFotos()
  const vigentes = usePromocionesVigentes()
  return (
    <Seccion
      titulo={`Sin ventas hace más de ${dias} días`}
      descripcion="Herramientas con stock en una sucursal que no registran salidas (los ajustes no cuentan como venta)."
    >
      {estancadas.length === 0 ? (
        <Vacio icono={Clock} titulo="Nada estancado" ayuda="Todas las herramientas con stock se vendieron hace poco." />
      ) : (
        <Table>
          <THead>
            <tr>
              <Th>Herramienta</Th>
              <Th>Sucursal</Th>
              <Th numerico>Stock</Th>
              <Th numerico>Días sin venta</Th>
              <Th>Promoción</Th>
            </tr>
          </THead>
          <tbody>
            {estancadas.map((e) => (
              <Tr key={`${e.herramienta_id}-${e.sucursal_id}`}>
                <Td><CeldaHerramienta codigo={e.codigo} nombre={e.nombre} imagen={foto(e.herramienta_id)} /></Td>
                <Td>{e.sucursal_nombre}</Td>
                <Td numerico>{e.stock}</Td>
                <Td numerico>
                  <span className="font-semibold">{e.dias_sin_venta}</span>
                  {e.nunca_vendida && <span className="block text-xs text-muted">nunca vendida</span>}
                </Td>
                <Td>
                  {vigentes(e.herramienta_id, e.sucursal_id).map((p) => (
                    <EtiquetaPromocion key={p.id} descuento={p.descuento_porcentaje} />
                  ))}
                </Td>
              </Tr>
            ))}
          </tbody>
        </Table>
      )}
    </Seccion>
  )
}
