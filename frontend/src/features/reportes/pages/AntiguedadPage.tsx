import { useState } from 'react'
import { Hourglass, Tag } from 'lucide-react'
import {
  Aviso,
  Badge,
  Button,
  Card,
  EmptyState,
  Field,
  Modal,
  PageHeader,
  SegmentedControl,
  Select,
  SkeletonFilas,
  SkeletonIndicadores,
  StatCard,
  Table,
  THead,
  Td,
  Th,
  Tr,
  type OpcionSegmento,
  type TonoBadge,
} from '../../../components/ui'
import { getSession } from '../../auth/session'
import { Rol } from '../../../shared/types/roles'
import { mensajeDeError } from '../../../shared/api/errores'
import { fechaHora, monto } from '../../../shared/formato'
import { CeldaHerramienta } from '../../catalogo/components/CeldaHerramienta'
import { useFotos } from '../../catalogo/hooks/useFotos'
import { useSucursales } from '../../usuarios/hooks/useSucursales'
import { useAntiguedad } from '../hooks/useAntiguedad'
import { PromocionForm } from '../../promociones/components/PromocionForm'
import { usePromociones } from '../../promociones/hooks/usePromociones'
import { puedeGestionarPromociones } from '../../promociones/permisos'
import type { LineaAntiguedad } from '../api/reportesApi'

// Antigüedad del stock (HU22): cuántos días lleva cada herramienta sin
// venderse en cada sucursal, por tramos, y cuánto dinero inmoviliza lo
// estancado. El Administrador ve todas las sucursales o una; el
// Supervisor, solo la suya (el backend responde 403 a cualquier otra).
// HU23: la columna Promoción muestra el descuento vigente y, al
// Administrador, el botón para promocionar una estancada.

type Rango = '0' | '31' | '41' | '91'

const RANGOS: OpcionSegmento<Rango>[] = [
  { valor: '0', texto: 'Todo' },
  { valor: '31', texto: 'Más de 30 días' },
  { valor: '41', texto: 'Estancadas' },
  { valor: '91', texto: 'Más de 90 días' },
]

function tonoTramo(l: LineaAntiguedad): TonoBadge {
  if (l.dias_sin_venta > 90) return 'danger'
  return l.estancada ? 'warn' : 'neutral'
}

export function AntiguedadPage() {
  const session = getSession()
  const esAdmin = session?.rol === Rol.ADMINISTRADOR
  const gestionaPromociones = session ? puedeGestionarPromociones(session.rol) : false
  const [aPromocionar, setAPromocionar] = useState<LineaAntiguedad | null>(null)
  const { data: vigentes } = usePromociones(true)
  const [sucursal, setSucursal] = useState('')
  const [rango, setRango] = useState<Rango>('0')
  const { data: sucursales } = useSucursales()
  const foto = useFotos()
  const { data: reporte, isLoading, isError, error, refetch } = useAntiguedad({
    sucursal: esAdmin && sucursal !== '' ? Number(sucursal) : undefined,
    dias_minimos: Number(rango),
  })
  const todas = reporte?.sucursal_id === null
  const masDe90 = reporte?.tramos.at(-1)
  const descuento = (l: LineaAntiguedad) =>
    vigentes?.find((p) => p.herramienta_id === l.herramienta_id && p.sucursal_id === l.sucursal_id)?.descuento_porcentaje

  return (
    <>
      <PageHeader
        migas={['Análisis', 'Antigüedad del stock']}
        titulo="Antigüedad del stock"
        subtitulo="Días sin venta de cada herramienta con stock, por sucursal."
      />

      <Card className="flex flex-wrap items-end gap-5">
        {esAdmin ? (
          <Field etiqueta="Sucursal" className="w-64">
            <Select value={sucursal} onChange={(e) => setSucursal(e.target.value)}>
              <option value="">Todas las sucursales</option>
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
        <div>
          <p className="mb-1.5 text-xs font-semibold text-muted">Mostrar</p>
          <SegmentedControl etiqueta="Rango de días sin venta" opciones={RANGOS} valor={rango} onCambiar={setRango} />
        </div>
      </Card>

      {isError && (
        <Aviso tono="error" accion={<Button tamano="sm" onClick={() => refetch()}>Reintentar</Button>}>
          {mensajeDeError(error, 'No se pudo cargar el reporte de antigüedad.')}
        </Aviso>
      )}
      {isLoading && (
        <>
          <SkeletonIndicadores />
          <Card sinPadding><SkeletonFilas filas={6} columnas={6} /></Card>
        </>
      )}

      {reporte && (
        <>
          <div className="grid grid-cols-4 gap-5">
            <StatCard etiqueta="Unidades en stock" valor={reporte.total_unidades} nota={`${reporte.lineas.length} herramientas por sucursal`} />
            <StatCard
              etiqueta="Estancadas"
              valor={reporte.total_estancadas}
              nota={`Más de ${reporte.dias_para_estancamiento} días sin venta`}
              alerta={reporte.total_estancadas > 0}
            />
            <StatCard
              etiqueta="Valor inmovilizado (estancadas)"
              valor={monto(Number(reporte.valor_inmovilizado_estancado))}
              nota={reporte.lineas_sin_costo > 0 ? `${reporte.lineas_sin_costo} sin costo cargado` : 'Stock × costo unitario'}
            />
            <StatCard
              etiqueta="Más de 90 días sin venta"
              valor={masDe90?.lineas ?? 0}
              nota={`${masDe90?.unidades ?? 0} unidades`}
            />
          </div>

          {reporte.lineas.length === 0 ? (
            <Card sinPadding>
              <EmptyState
                icono={Hourglass}
                titulo="Nada en este rango"
                ayuda="Ninguna herramienta con stock lleva tantos días sin venderse."
              />
            </Card>
          ) : (
            <Card sinPadding className="overflow-hidden">
              <Table>
                <THead>
                  <tr>
                    <Th>Herramienta</Th>
                    {todas && <Th>Sucursal</Th>}
                    <Th numerico>Stock</Th>
                    <Th>Última venta</Th>
                    <Th numerico>Días sin venta</Th>
                    <Th>Tramo</Th>
                    <Th numerico>Valor inmovilizado</Th>
                    <Th>Promoción</Th>
                  </tr>
                </THead>
                <tbody>
                  {reporte.lineas.map((l) => (
                    <Tr key={`${l.herramienta_id}-${l.sucursal_id}`}>
                      <Td className="max-w-[280px]"><CeldaHerramienta codigo={l.codigo} nombre={l.nombre} imagen={foto(l.herramienta_id)} /></Td>
                      {todas && <Td>{l.sucursal_nombre}</Td>}
                      <Td numerico>{l.stock}</Td>
                      <Td className="tabular-nums text-muted">{l.ultima_venta ? fechaHora(l.ultima_venta) : 'Nunca vendida'}</Td>
                      <Td numerico className="font-semibold">{l.dias_sin_venta}</Td>
                      <Td><Badge tono={tonoTramo(l)}>{l.tramo}</Badge></Td>
                      <Td numerico>{l.valor_inmovilizado === null ? '—' : monto(Number(l.valor_inmovilizado))}</Td>
                      <Td>
                        {descuento(l) !== undefined ? (
                          <Badge tono="acc" icono={<Tag size={12} aria-hidden />}>−{descuento(l)} %</Badge>
                        ) : gestionaPromociones && l.estancada ? (
                          <Button tamano="sm" onClick={() => setAPromocionar(l)}>Promocionar</Button>
                        ) : (
                          <span className="text-muted">—</span>
                        )}
                      </Td>
                    </Tr>
                  ))}
                </tbody>
              </Table>
            </Card>
          )}
        </>
      )}

      <Modal
        abierto={aPromocionar !== null}
        onCerrar={() => setAPromocionar(null)}
        titulo="Nueva promoción"
        descripcion="Empieza hoy. El mostrador la ve en Promociones."
      >
        {aPromocionar && <PromocionForm key={`${aPromocionar.herramienta_id}-${aPromocionar.sucursal_id}`} linea={aPromocionar} onTerminar={() => setAPromocionar(null)} />}
      </Modal>
    </>
  )
}
