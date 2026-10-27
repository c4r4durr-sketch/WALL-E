import { useState } from 'react'
import { Link } from 'react-router-dom'
import { Hourglass, Tag } from 'lucide-react'
import {
  Aviso,
  Badge,
  Button,
  Card,
  ConfirmModal,
  EmptyState,
  PageHeader,
  SegmentedControl,
  SkeletonFilas,
  Table,
  THead,
  Td,
  Th,
  Tr,
  clasesBoton,
  type OpcionSegmento,
  type TonoBadge,
} from '../../../components/ui'
import { getSession } from '../../auth/session'
import { mensajeDeError } from '../../../shared/api/errores'
import { fechaCorta } from '../../../shared/formato'
import { CeldaHerramienta } from '../../catalogo/components/CeldaHerramienta'
import { useFotos } from '../../catalogo/hooks/useFotos'
import { puedeGestionarPromociones } from '../permisos'
import { usePromociones, useTerminarPromocion } from '../hooks/usePromociones'
import type { EstadoPromocion, Promocion } from '../api/promocionesApi'

// Promociones (HU23): descuentos sobre herramientas estancadas, por
// sucursal. Todos los roles las ven (el mostrador tiene que saber qué
// aplicar); el Administrador las crea desde "Antigüedad del stock" y acá
// puede terminarlas antes de su fecha de fin.

type Filtro = 'vigentes' | 'todas'

const FILTROS: OpcionSegmento<Filtro>[] = [
  { valor: 'vigentes', texto: 'Vigentes' },
  { valor: 'todas', texto: 'Todas' },
]

const ESTADO: Record<EstadoPromocion, { texto: string; tono: TonoBadge }> = {
  VIGENTE: { texto: 'Vigente', tono: 'ok' },
  VENCIDA: { texto: 'Vencida', tono: 'neutral' },
  TERMINADA: { texto: 'Terminada', tono: 'neutral' },
}

export function PromocionesPage() {
  const session = getSession()
  const esAdmin = session ? puedeGestionarPromociones(session.rol) : false
  const [filtro, setFiltro] = useState<Filtro>('vigentes')
  const [aTerminar, setATerminar] = useState<Promocion | null>(null)
  const { data: promociones, isLoading, isError, error, refetch } = usePromociones(filtro === 'vigentes')
  const terminar = useTerminarPromocion()
  const foto = useFotos()

  function cerrar() {
    setATerminar(null)
    terminar.reset()
  }

  return (
    <>
      <PageHeader
        migas={['Inventario', 'Promociones']}
        titulo="Promociones"
        subtitulo="Descuentos para sacar el stock estancado, por sucursal."
        acciones={<SegmentedControl etiqueta="Qué promociones mostrar" opciones={FILTROS} valor={filtro} onCambiar={setFiltro} />}
      />

      {isError && (
        <Aviso tono="error" accion={<Button tamano="sm" onClick={() => refetch()}>Reintentar</Button>}>
          {mensajeDeError(error, 'No se pudieron cargar las promociones.')}
        </Aviso>
      )}
      {isLoading && (
        <Card sinPadding><SkeletonFilas filas={5} columnas={6} /></Card>
      )}

      {promociones && promociones.length === 0 && (
        <Card sinPadding>
          <EmptyState
            icono={Tag}
            titulo={filtro === 'vigentes' ? 'Sin promociones vigentes' : 'Todavía no hay promociones'}
            ayuda="Se crean sobre herramientas con más de 40 días sin venta, desde Antigüedad del stock."
            accion={
              esAdmin ? (
                <Link to="/antiguedad" className={clasesBoton({ tamano: 'sm' })}>
                  <Hourglass size={14} aria-hidden /> Ver antigüedad del stock
                </Link>
              ) : undefined
            }
          />
        </Card>
      )}

      {promociones && promociones.length > 0 && (
        <Card sinPadding className="overflow-hidden">
          <Table>
            <THead>
              <tr>
                <Th>Herramienta</Th>
                <Th>Sucursal</Th>
                <Th numerico>Descuento</Th>
                <Th>Vigencia</Th>
                <Th>Estado</Th>
                <Th>Creada por</Th>
                <Th>Motivo</Th>
                {esAdmin && <Th><span className="sr-only">Acciones</span></Th>}
              </tr>
            </THead>
            <tbody>
              {promociones.map((p) => (
                <Tr key={p.id}>
                  <Td className="max-w-[260px]">
                    <CeldaHerramienta codigo={p.herramienta_codigo} nombre={p.herramienta_nombre} imagen={foto(p.herramienta_id)} />
                  </Td>
                  <Td>{p.sucursal_nombre}</Td>
                  <Td numerico className="font-semibold">−{p.descuento_porcentaje} %</Td>
                  <Td className="tabular-nums text-muted">{fechaCorta(p.fecha_inicio)} – {fechaCorta(p.fecha_fin)}</Td>
                  <Td><Badge tono={ESTADO[p.estado].tono}>{ESTADO[p.estado].texto}</Badge></Td>
                  <Td>{p.usuario}</Td>
                  <Td className="max-w-[220px] truncate text-muted">{p.motivo || '—'}</Td>
                  {esAdmin && (
                    <Td className="text-right">
                      {p.estado === 'VIGENTE' && (
                        <Button tamano="sm" variante="ghost" peligro onClick={() => setATerminar(p)}>Terminar</Button>
                      )}
                    </Td>
                  )}
                </Tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      <ConfirmModal
        abierto={aTerminar !== null}
        onCerrar={cerrar}
        onConfirmar={() => aTerminar && terminar.mutate(aTerminar.id, { onSuccess: cerrar })}
        titulo="Terminar la promoción"
        textoConfirmar="Terminar"
        cargando={terminar.isPending}
        error={terminar.isError ? mensajeDeError(terminar.error, 'No se pudo terminar la promoción.') : null}
      >
        {aTerminar && (
          <p>
            {aTerminar.herramienta_codigo} en {aTerminar.sucursal_nombre} deja de tener el {aTerminar.descuento_porcentaje} %
            de descuento desde ahora. Queda en el historial como terminada.
          </p>
        )}
      </ConfirmModal>
    </>
  )
}
