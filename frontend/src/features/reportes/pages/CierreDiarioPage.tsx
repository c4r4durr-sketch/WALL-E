import { useState } from 'react'
import { CalendarCheck, Info } from 'lucide-react'
import {
  Aviso,
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  Field,
  Input,
  PageHeader,
  Select,
  SkeletonFilas,
  SkeletonIndicadores,
  Table,
  THead,
  Td,
  Th,
  Tr,
} from '../../../components/ui'
import { getSession } from '../../auth/session'
import { Rol } from '../../../shared/types/roles'
import { mensajeDeError } from '../../../shared/api/errores'
import { fechaLarga, hora, hoyEnLaPaz } from '../../../shared/formato'
import { StatTile } from '../../dashboard/components/StatTile'
import { CeldaHerramienta } from '../../catalogo/components/CeldaHerramienta'
import { useFotos } from '../../catalogo/hooks/useFotos'
import { ETIQUETA, cajas } from '../../movimientos/formato'
import { useSucursales } from '../../usuarios/hooks/useSucursales'
import { useCierreDiario } from '../hooks/useCierreDiario'
import { ExportarExcel } from '../components/ExportarExcel'
import type { CierreDiario, LineaCierre } from '../api/reportesApi'
import type { TipoMovimiento } from '../../movimientos/api/movimientosApi'

// Cierre y resumen diario (HU14): todos los movimientos del día de una
// sucursal, en hora de La Paz, para cuadrar la caja. El Administrador
// elige la sucursal; el Supervisor ve solo la suya (el backend responde
// 403 a cualquier otra, y al Empleado).

function unidades(cierre: CierreDiario, tipo: TipoMovimiento): number {
  return cierre.totales.find((t) => t.tipo_movimiento === tipo)?.unidades ?? 0
}

function cantidadRegistrada(l: LineaCierre): string {
  return l.tipo_unidad === 'CAJA' ? cajas(l.cantidad) : `${l.cantidad} u.`
}

export function CierreDiarioPage() {
  const session = getSession()
  const esAdmin = session?.rol === Rol.ADMINISTRADOR
  const hoy = hoyEnLaPaz()
  const [fecha, setFecha] = useState(hoy)
  const [sucursal, setSucursal] = useState<string>(session?.sucursal_id ? String(session.sucursal_id) : '')
  const { data: sucursales } = useSucursales()
  const foto = useFotos()

  const fechaValida = /^\d{4}-\d{2}-\d{2}$/.test(fecha) && fecha <= hoy
  const listo = fechaValida && (!esAdmin || sucursal !== '')
  const { data: cierre, isLoading, isError, error, refetch } = useCierreDiario(
    { sucursal: esAdmin ? Number(sucursal) : undefined, fecha },
    listo,
  )

  return (
    <>
      <PageHeader
        migas={['Inventario', 'Cierre diario']}
        titulo="Cierre diario"
        subtitulo="Movimientos del día por sucursal, en hora de La Paz."
        acciones={
          <ExportarExcel
            url="/indicadores/cierre-diario/excel/"
            params={{ sucursal: esAdmin ? Number(sucursal) : undefined, fecha }}
            nombre={`cierre-diario-${fecha}`}
            deshabilitado={!listo || !cierre}
          />
        }
      />

      <Card className="flex flex-wrap items-start gap-5">
        <Field etiqueta="Fecha" error={fechaValida ? null : 'Elige una fecha que no sea posterior a hoy.'} className="w-48">
          <Input type="date" value={fecha} max={hoy} onChange={(e) => setFecha(e.target.value)} />
        </Field>
        {esAdmin ? (
          <Field etiqueta="Sucursal" className="w-64">
            <Select value={sucursal} onChange={(e) => setSucursal(e.target.value)}>
              <option value="" disabled>Selecciona una sucursal</option>
              {sucursales?.map((s) => (
                <option key={s.id} value={s.id}>{s.nombre}</option>
              ))}
            </Select>
          </Field>
        ) : (
          <div>
            <p className="mb-1.5 text-xs font-semibold text-muted">Sucursal</p>
            <p className="flex h-10 items-center text-sm font-semibold text-ink">{session?.sucursal_nombre}</p>
          </div>
        )}
      </Card>

      {esAdmin && sucursal === '' && (
        <Card sinPadding>
          <EmptyState icono={CalendarCheck} titulo="Elige una sucursal" ayuda="El cierre se arma por sucursal y por día." />
        </Card>
      )}
      {isLoading && listo && (
        <>
          <SkeletonIndicadores />
          <Card sinPadding><SkeletonFilas filas={5} columnas={6} /></Card>
        </>
      )}
      {isError && (
        <Aviso tono="error" accion={<Button tamano="sm" onClick={() => refetch()}>Reintentar</Button>}>
          {mensajeDeError(error, 'No se pudo cargar el cierre diario.')}
        </Aviso>
      )}

      {cierre && listo && (
        <>
          <h2 className="text-xl font-bold tracking-[-0.02em] text-ink">
            {cierre.sucursal_nombre} · <span className="font-medium text-muted">{fechaLarga(cierre.fecha)}</span>
          </h2>

          <div className="grid grid-cols-4 gap-5">
            <StatTile
              etiqueta="Salidas (unidades)"
              valor={cierre.total_salidas_unidades}
              nota={`${cierre.cantidad_salidas} ${cierre.cantidad_salidas === 1 ? 'venta registrada' : 'ventas registradas'}`}
            />
            <StatTile etiqueta="Entradas (unidades)" valor={unidades(cierre, 'ENTRADA')} />
            <StatTile
              etiqueta="Transferencias (unidades)"
              valor={unidades(cierre, 'TRANSFERENCIA_SALIDA') + unidades(cierre, 'TRANSFERENCIA_ENTRADA')}
              nota={`${unidades(cierre, 'TRANSFERENCIA_SALIDA')} enviadas · ${unidades(cierre, 'TRANSFERENCIA_ENTRADA')} recibidas`}
            />
            <StatTile
              etiqueta="Ajustes (unidades)"
              valor={unidades(cierre, 'AJUSTE_POSITIVO') + unidades(cierre, 'AJUSTE_NEGATIVO')}
              nota={`+${unidades(cierre, 'AJUSTE_POSITIVO')} · −${unidades(cierre, 'AJUSTE_NEGATIVO')}`}
            />
          </div>

          {/* CA3: un día sin salidas muestra un aviso, no una tabla vacía. */}
          {cierre.cantidad_salidas === 0 && cierre.lineas.length > 0 && (
            <Aviso tono="info">No hubo salidas (ventas) este día en {cierre.sucursal_nombre}.</Aviso>
          )}

          {cierre.lineas.length === 0 ? (
            <Card sinPadding>
              <EmptyState
                icono={Info}
                titulo="Sin movimientos este día"
                ayuda={`No hubo salidas (ventas) ni otros movimientos en ${cierre.sucursal_nombre}.`}
              />
            </Card>
          ) : (
            <Card sinPadding className="overflow-hidden">
              <CardHeader className="px-6 pb-4 pt-6" titulo="Movimientos del día" />
              <Table>
                <THead>
                  <tr>
                    <Th>Hora</Th>
                    <Th>Tipo</Th>
                    <Th>Herramienta</Th>
                    <Th numerico>Cantidad</Th>
                    <Th numerico>Unidades</Th>
                    <Th>Usuario</Th>
                    <Th>Motivo</Th>
                  </tr>
                </THead>
                <tbody>
                  {cierre.lineas.map((l) => (
                    <Tr key={l.movimiento_id}>
                      <Td className="tabular-nums">{hora(l.fecha_hora)}</Td>
                      <Td><Badge tono={ETIQUETA[l.tipo_movimiento].tono}>{ETIQUETA[l.tipo_movimiento].texto}</Badge></Td>
                      <Td className="max-w-[260px]"><CeldaHerramienta codigo={l.codigo} nombre={l.nombre} imagen={foto(l.herramienta_id)} /></Td>
                      <Td numerico>{cantidadRegistrada(l)}</Td>
                      <Td numerico className="font-semibold">{l.cantidad_unidades}</Td>
                      <Td>{l.usuario}</Td>
                      <Td className="text-muted">{l.motivo || '—'}</Td>
                    </Tr>
                  ))}
                </tbody>
                <tfoot>
                  <tr className="h-14 border-t border-line bg-surf2 font-semibold">
                    <td colSpan={4} className="px-4 text-right">Total de salidas del día</td>
                    <td className="px-4 text-right tabular-nums">{cierre.total_salidas_unidades}</td>
                    <td colSpan={2} />
                  </tr>
                </tfoot>
              </Table>
            </Card>
          )}
        </>
      )}
    </>
  )
}
