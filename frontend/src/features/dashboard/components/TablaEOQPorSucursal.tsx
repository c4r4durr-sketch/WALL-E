import { AlertTriangle, CheckCircle2 } from 'lucide-react'
import { Aviso, Card, CardHeader, SkeletonFilas, Table, THead, Td, Th, Tr } from '../../../components/ui'
import { decimal } from '../../../shared/formato'
import { useEOQPorSucursal } from '../hooks/useIndicadores'
import type { ReposicionSucursal } from '../api/indicadoresApi'
import { pedidoEnCajas } from '../formato'

// EOQ y punto de reorden de una herramienta en cada sucursal activa: misma
// fórmula que las tarjetas generales, con lo vendido y el stock de esa
// sucursal (S, H y tiempo de entrega del catálogo).

function Estado({ linea }: { linea: ReposicionSucursal }) {
  if (linea.punto_reorden === null) return <span className="text-xs text-muted">Faltan datos</span>
  if (linea.requiere_reorden) {
    return (
      <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-warn">
        <AlertTriangle size={14} aria-hidden />
        Pedir
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-ok">
      <CheckCircle2 size={14} aria-hidden />
      En orden
    </span>
  )
}

function Demanda({ linea }: { linea: ReposicionSucursal }) {
  if (linea.demanda_usada === null) return <>—</>
  return (
    <>
      {linea.demanda_usada}
      {linea.fuente_demanda === 'ESTIMADA' && <span className="block text-xs text-muted">estimada, repartida</span>}
    </>
  )
}

export function TablaEOQPorSucursal({ herramientaId }: { herramientaId: number }) {
  const { data, isLoading, isError } = useEOQPorSucursal(herramientaId)

  return (
    <Card sinPadding className="mt-5 overflow-hidden">
      <CardHeader
        titulo="Por sucursal"
        descripcion="Cada sucursal con lo que vendió en los últimos 12 meses y su propio stock. Una entrada sube el stock, pero no cambia el EOQ: ese depende de las ventas."
        className="px-6 pb-4 pt-6"
      />
      {isLoading && <SkeletonFilas filas={2} />}
      {isError && <Aviso tono="error" className="mx-6 mb-6">No se pudo calcular el detalle por sucursal.</Aviso>}
      {data && (
        <Table>
          <THead>
            <tr>
              <Th>Sucursal</Th>
              <Th numerico>Vendido (D)</Th>
              <Th numerico>Stock</Th>
              <Th numerico>Punto de reorden</Th>
              <Th numerico>EOQ</Th>
              <Th numerico>Pedido sugerido</Th>
              <Th>Estado</Th>
            </tr>
          </THead>
          <tbody>
            {data.sucursales.map((s) => (
              <Tr key={s.sucursal_id}>
                <Td>{s.sucursal_nombre}</Td>
                <Td numerico><Demanda linea={s} /></Td>
                <Td numerico className={s.requiere_reorden ? 'font-semibold text-warn' : undefined}>{s.stock}</Td>
                <Td numerico>{s.punto_reorden === null ? '—' : decimal(s.punto_reorden)}</Td>
                <Td numerico>{s.eoq === null ? '—' : decimal(s.eoq)}</Td>
                <Td numerico>{pedidoEnCajas(s.eoq_ajustado_cajas, s.unidades_por_caja)}</Td>
                <Td><Estado linea={s} /></Td>
              </Tr>
            ))}
          </tbody>
        </Table>
      )}
    </Card>
  )
}
