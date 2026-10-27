import { useState } from 'react'
import { Check, Truck, X } from 'lucide-react'
import {
  Badge,
  Button,
  Card,
  CardHeader,
  EmptyState,
  Input,
  SegmentedControl,
  SkeletonFilas,
  Table,
  THead,
  Td,
  Th,
  Tr,
  Aviso,
  type TonoBadge,
} from '../../../components/ui'
import { fechaHora } from '../../../shared/formato'
import type { Herramienta } from '../../catalogo/api/catalogoApi'
import { CeldaHerramienta } from '../../catalogo/components/CeldaHerramienta'
import type { Sucursal } from '../../usuarios/api/usuariosApi'
import { cajas } from '../../movimientos/formato'
import { erroresDelBackend } from '../../movimientos/errores'
import type { EstadoTransferencia, Transferencia } from '../api/transferenciasApi'
import { useCompletarTransferencia, useRechazarTransferencia, useTransferencias } from '../hooks/useTransferencias'

// Listado de transferencias (pendientes o todas). Administrador/Supervisor
// resuelven las pendientes desde la misma fila: completar (mueve el stock)
// o rechazar (con motivo). Los errores del backend (ej. 409: ya no hay
// stock en origen) se muestran en la fila afectada.

const ESTADO: Record<EstadoTransferencia, { texto: string; tono: TonoBadge }> = {
  PENDIENTE: { texto: 'Pendiente', tono: 'warn' },
  COMPLETADA: { texto: 'Completada', tono: 'ok' },
  RECHAZADA: { texto: 'Rechazada', tono: 'neutral' },
}

interface Props {
  herramientas: Herramienta[]
  sucursales: Sucursal[]
  puedeResolver: boolean
}

function mensajeError(error: unknown): string | null {
  if (!error) return null
  const e = erroresDelBackend(error)
  return e.detail ?? e.motivo ?? 'No se pudo resolver la transferencia.'
}

function FilaAcciones({ t }: { t: Transferencia }) {
  const completar = useCompletarTransferencia()
  const rechazar = useRechazarTransferencia()
  const [rechazando, setRechazando] = useState(false)
  const [motivo, setMotivo] = useState('')
  const ocupado = completar.isPending || rechazar.isPending
  const error = mensajeError(completar.error) ?? mensajeError(rechazar.error)

  return (
    <div className="space-y-1.5 py-1">
      {rechazando ? (
        <div className="flex items-center gap-2">
          <Input
            aria-label="Motivo del rechazo"
            value={motivo}
            maxLength={255}
            placeholder="Motivo del rechazo"
            autoFocus
            onChange={(e) => { setMotivo(e.target.value); rechazar.reset() }}
            className="h-8! min-w-40 text-xs"
          />
          <Button tamano="sm" peligro disabled={!motivo.trim()} cargando={rechazar.isPending}
            onClick={() => rechazar.mutate({ id: t.id, motivo: motivo.trim() })}>
            Rechazar
          </Button>
          <Button tamano="sm" variante="ghost" onClick={() => { setRechazando(false); rechazar.reset() }}>
            Cancelar
          </Button>
        </div>
      ) : (
        <div className="flex gap-2">
          <Button tamano="sm" disabled={ocupado} cargando={completar.isPending} icono={<Check size={14} aria-hidden />}
            onClick={() => completar.mutate(t.id)}>
            Completar
          </Button>
          <Button tamano="sm" variante="ghost" peligro disabled={ocupado} icono={<X size={14} aria-hidden />}
            onClick={() => { setRechazando(true); completar.reset() }}>
            Rechazar
          </Button>
        </div>
      )}
      {error && <p role="alert" className="max-w-xs text-xs font-medium text-danger">{error}</p>}
    </div>
  )
}

export function TablaTransferencias({ herramientas, sucursales, puedeResolver }: Props) {
  const [filtro, setFiltro] = useState<'PENDIENTE' | 'TODAS'>('PENDIENTE')
  const { data: transferencias, isLoading, isError } = useTransferencias(filtro === 'TODAS' ? undefined : filtro)
  const herramienta = (id: number) => herramientas.find((h) => h.id === id)
  const sucursal = (id: number) => sucursales.find((s) => s.id === id)?.nombre ?? `#${id}`

  return (
    <Card sinPadding className="overflow-hidden">
      <CardHeader
        className="px-6 pb-4 pt-6"
        titulo="Transferencias"
        acciones={
          <SegmentedControl<'PENDIENTE' | 'TODAS'>
            etiqueta="Filtro de transferencias"
            valor={filtro}
            onCambiar={setFiltro}
            opciones={[
              { valor: 'PENDIENTE', texto: 'Pendientes' },
              { valor: 'TODAS', texto: 'Todas' },
            ]}
          />
        }
      />
      {isLoading && <SkeletonFilas filas={4} columnas={5} />}
      {isError && <Aviso tono="error" className="mx-6 mb-6">No se pudieron cargar las transferencias.</Aviso>}
      {transferencias?.length === 0 && (
        <EmptyState
          compacto
          icono={Truck}
          className="border-t border-line"
          titulo={filtro === 'PENDIENTE' ? 'Nada pendiente' : 'Todavía no hay transferencias'}
          ayuda={filtro === 'PENDIENTE' ? 'No hay transferencias esperando aprobación.' : 'Las solicitudes aparecerán acá.'}
        />
      )}
      {transferencias && transferencias.length > 0 && (
        <Table>
          <THead>
            <tr>
              <Th>Herramienta</Th>
              <Th>Desde → hacia</Th>
              <Th numerico>Cantidad</Th>
              <Th>Estado</Th>
              <Th>Solicitó / resolvió</Th>
              {puedeResolver && <Th><span className="sr-only">Acciones</span></Th>}
            </tr>
          </THead>
          <tbody>
            {transferencias.map((t) => {
              const h = herramienta(t.herramienta)
              return (
                <Tr key={t.id}>
                  <Td className="max-w-[240px]">
                    <CeldaHerramienta codigo={h?.codigo ?? `#${t.herramienta}`} nombre={h?.nombre ?? 'Herramienta'} imagen={h?.imagen} />
                  </Td>
                  <Td>
                    <span className="whitespace-nowrap">{sucursal(t.sucursal_origen)} → {sucursal(t.sucursal_destino)}</span>
                    <span className="block text-xs text-muted tabular-nums">{fechaHora(t.creado_en)}</span>
                  </Td>
                  <Td numerico className="whitespace-nowrap">
                    {t.tipo_unidad === 'CAJA' ? `${cajas(t.cantidad)} (${t.cantidad_unidades} u.)` : `${t.cantidad} u.`}
                  </Td>
                  <Td>
                    <Badge tono={ESTADO[t.estado].tono}>{ESTADO[t.estado].texto}</Badge>
                    {t.motivo_rechazo && <p className="mt-1 max-w-xs text-xs italic text-muted">{t.motivo_rechazo}</p>}
                  </Td>
                  <Td className="text-xs text-muted">
                    {t.usuario_username}
                    {t.resuelto_por_username && <span className="block">→ {t.resuelto_por_username}</span>}
                  </Td>
                  {puedeResolver && <Td>{t.estado === 'PENDIENTE' ? <FilaAcciones t={t} /> : null}</Td>}
                </Tr>
              )
            })}
          </tbody>
        </Table>
      )}
    </Card>
  )
}
