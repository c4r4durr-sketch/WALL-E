import { History } from 'lucide-react'
import { Aviso, Badge, Card, CardHeader, EmptyState, SkeletonFilas, Table, THead, Td, Th, Tr, cx } from '../../../components/ui'
import { fechaHora } from '../../../shared/formato'
import type { Herramienta } from '../../catalogo/api/catalogoApi'
import type { Sucursal } from '../../usuarios/api/usuariosApi'
import type { Movimiento, TipoMovimiento } from '../api/movimientosApi'
import { useHistorialMovimientos } from '../hooks/useMovimientos'
import { ETIQUETA, cajas } from '../formato'

// Historial de movimientos de una herramienta (todas las sucursales, del
// más reciente al más antiguo), HU11. El stock por sucursal lo muestra la
// página, arriba.

// Tipos que suman al stock (espejo de EFECTO_EN_STOCK del backend).
const SUMA = new Set<TipoMovimiento>(['ENTRADA', 'AJUSTE_POSITIVO', 'TRANSFERENCIA_ENTRADA'])

function cantidadRegistrada(m: Movimiento): string {
  return m.tipo_unidad === 'CAJA' ? cajas(m.cantidad) : `${m.cantidad} u.`
}

interface Props {
  herramienta: Herramienta
  sucursales: Sucursal[]
}

export function HistorialMovimientos({ herramienta, sucursales }: Props) {
  const { data: movimientos, isLoading, isError } = useHistorialMovimientos(herramienta.id)
  const nombreSucursal = (id: number) => sucursales.find((s) => s.id === id)?.nombre ?? `#${id}`

  return (
    <Card sinPadding className="overflow-hidden">
      <CardHeader className="px-6 pb-4 pt-6" titulo="Historial" descripcion={`${herramienta.codigo} · ${herramienta.nombre}, todas las sucursales`} />
      {isLoading && <SkeletonFilas filas={5} columnas={5} />}
      {isError && <Aviso tono="error" className="mx-6 mb-6">No se pudo cargar el historial.</Aviso>}
      {movimientos?.length === 0 && (
        <EmptyState compacto icono={History} className="border-t border-line" titulo="Sin movimientos" ayuda="Esta herramienta todavía no tiene entradas ni salidas." />
      )}
      {movimientos && movimientos.length > 0 && (
        <Table>
          <THead>
            <tr>
              <Th>Fecha</Th>
              <Th>Sucursal</Th>
              <Th>Tipo</Th>
              <Th numerico>Registrado</Th>
              <Th numerico>Unidades</Th>
              <Th>Usuario</Th>
            </tr>
          </THead>
          <tbody>
            {movimientos.map((m) => (
              <Tr key={m.id}>
                <Td className="whitespace-nowrap tabular-nums">{fechaHora(m.creado_en)}</Td>
                <Td>{nombreSucursal(m.sucursal)}</Td>
                <Td>
                  <Badge tono={ETIQUETA[m.tipo_movimiento].tono}>{ETIQUETA[m.tipo_movimiento].texto}</Badge>
                  {m.motivo && <p className="mt-1 max-w-xs text-xs italic text-muted">{m.motivo}</p>}
                </Td>
                <Td numerico>{cantidadRegistrada(m)}</Td>
                <Td numerico className={cx('font-semibold', SUMA.has(m.tipo_movimiento) ? 'text-ok' : 'text-danger')}>
                  {SUMA.has(m.tipo_movimiento) ? '+' : '−'}{m.cantidad_unidades}
                </Td>
                <Td>{m.usuario_username}</Td>
              </Tr>
            ))}
          </tbody>
        </Table>
      )}
    </Card>
  )
}
