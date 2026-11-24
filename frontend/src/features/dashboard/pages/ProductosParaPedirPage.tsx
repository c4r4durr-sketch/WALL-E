import { Link, useSearchParams } from 'react-router-dom'
import { CheckCircle2 } from 'lucide-react'
import {
  Aviso,
  Button,
  Card,
  CardHeader,
  EmptyState,
  Field,
  PageHeader,
  Select,
  SkeletonFilas,
  Table,
  THead,
  Td,
  Th,
  Tr,
} from '../../../components/ui'
import { decimal } from '../../../shared/formato'
import { CeldaHerramienta } from '../../catalogo/components/CeldaHerramienta'
import { useFotos } from '../../catalogo/hooks/useFotos'
import { useSucursales } from '../../usuarios/hooks/useSucursales'
import { GraficoPedirPorSucursal, GraficoStockVsRop } from '../components/GraficosParaPedir'
import { StatTile } from '../components/StatTile'
import { pedidoEnCajas } from '../formato'
import { useProductosParaPedir } from '../hooks/useIndicadores'

// Dashboard "Productos para pedir": por cada sucursal, las herramientas
// cuyo stock está en o bajo el punto de reorden de ESA sucursal (con lo que
// vendió ella en 12 meses), y cuánto pedir (su EOQ en cajas cerradas). La
// sucursal elegida va en la URL (?sucursal=id).
export function ProductosParaPedirPage() {
  const [params, setParams] = useSearchParams()
  const sucursal = Number(params.get('sucursal')) || null
  const { data: sucursales } = useSucursales()
  const { data, isLoading, isError, refetch } = useProductosParaPedir(sucursal)
  const foto = useFotos()

  function elegir(valor: string) {
    setParams(valor ? { sucursal: valor } : {}, { replace: true })
  }

  return (
    <>
      <PageHeader
        migas={['Análisis', 'Productos para pedir']}
        titulo="Productos para pedir"
        subtitulo="Por sucursal: herramientas con stock en o bajo su punto de reorden y cuánto pedir (EOQ en cajas cerradas)."
      />

      <Card className="mb-5">
        <Field etiqueta="Sucursal" className="max-w-sm">
          <Select value={sucursal ?? ''} onChange={(e) => elegir(e.target.value)}>
            <option value="">Todas las sucursales</option>
            {sucursales?.filter((s) => s.activa).map((s) => (
              <option key={s.id} value={s.id}>{s.nombre}</option>
            ))}
          </Select>
        </Field>
      </Card>

      {isError && (
        <Aviso tono="error" accion={<Button tamano="sm" onClick={() => refetch()}>Reintentar</Button>}>
          No se pudo cargar la lista de productos para pedir.
        </Aviso>
      )}
      {isLoading && (
        <Card sinPadding>
          <SkeletonFilas filas={6} />
        </Card>
      )}
      {data && (
        <>
          <div className="mb-5 grid grid-cols-3 gap-5">
            <StatTile etiqueta="Pedidos por hacer" valor={data.total_lineas} alerta={data.total_lineas > 0}
              nota="Herramienta × sucursal" />
            <StatTile etiqueta="Herramientas distintas" valor={data.total_herramientas} />
            <StatTile etiqueta="Sin datos para calcular" valor={data.herramientas_sin_datos}
              nota="Falta demanda o tiempo de entrega" />
          </div>

          {data.lineas.length > 0 && (
            <div className="mb-5 grid grid-cols-2 items-start gap-5">
              <GraficoPedirPorSucursal
                lineas={data.lineas}
                sucursales={(sucursales ?? []).filter((s) => s.activa && (sucursal === null || s.id === sucursal))}
              />
              <GraficoStockVsRop lineas={data.lineas} unaSucursal={sucursal !== null} />
            </div>
          )}

          <Card sinPadding className="overflow-hidden">
            <CardHeader
              titulo="Para pedir"
              descripcion="Lo más urgente primero (más por debajo de su punto de reorden). S, H y tiempo de entrega son los del catálogo."
              className="px-6 pb-4 pt-6"
            />
            {data.lineas.length === 0 ? (
              <EmptyState compacto icono={CheckCircle2} titulo="Nada que pedir"
                ayuda="Ninguna sucursal llegó al punto de reorden de sus herramientas." className="border-t border-line" />
            ) : (
              <Table>
                <THead>
                  <tr>
                    <Th>Herramienta</Th>
                    <Th>Sucursal</Th>
                    <Th numerico>Stock</Th>
                    <Th numerico>Punto de reorden</Th>
                    <Th numerico>Vendido en 12 meses</Th>
                    <Th numerico>Pedido sugerido</Th>
                  </tr>
                </THead>
                <tbody>
                  {data.lineas.map((l) => (
                    <Tr key={`${l.herramienta_id}-${l.sucursal_id}`}>
                      <Td>
                        <Link to={`/indicadores?herramienta=${l.herramienta_id}`} className="hover:underline">
                          <CeldaHerramienta codigo={l.codigo} nombre={l.nombre} imagen={foto(l.herramienta_id)} />
                        </Link>
                      </Td>
                      <Td>{l.sucursal_nombre}</Td>
                      <Td numerico className="font-semibold text-warn">{l.stock}</Td>
                      <Td numerico>{l.punto_reorden === null ? '—' : decimal(l.punto_reorden)}</Td>
                      <Td numerico>
                        {l.demanda_observada}
                        {l.fuente_demanda === 'ESTIMADA' && (
                          <span className="block text-xs text-muted">sin ventas: estimada {l.demanda_usada}</span>
                        )}
                      </Td>
                      <Td numerico>
                        {l.eoq_ajustado_cajas === null ? (
                          <span className="text-xs text-muted">Faltan costos en el catálogo</span>
                        ) : (
                          <span className="font-semibold">{pedidoEnCajas(l.eoq_ajustado_cajas, l.unidades_por_caja)}</span>
                        )}
                      </Td>
                    </Tr>
                  ))}
                </tbody>
              </Table>
            )}
          </Card>
        </>
      )}
    </>
  )
}
