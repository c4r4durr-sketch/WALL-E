import { useMemo, useState } from 'react'
import { isAxiosError } from 'axios'
import { Boxes, History, LayoutGrid, List, Pencil, Plus, SearchX, Trash2 } from 'lucide-react'
import {
  Aparecer,
  Aviso,
  Badge,
  Button,
  Card,
  ConfirmModal,
  EmptyState,
  IconButton,
  PageHeader,
  ProductImage,
  SearchInput,
  SegmentedControl,
  SidePanel,
  SkeletonFilas,
  SkeletonTarjetas,
  Table,
  THead,
  Td,
  Th,
  Tr,
} from '../../../components/ui'
import { getSession } from '../../auth/session'
import { monto } from '../../../shared/formato'
import { usePreferencia } from '../../../shared/hooks/usePreferencia'
import { CeldaHerramienta } from '../components/CeldaHerramienta'
import { HerramientaForm } from '../components/HerramientaForm'
import { HistorialCostos } from '../components/HistorialCostos'
import { EtiquetaPromocion } from '../../promociones/components/EtiquetaPromocion'
import { usePromocionesVigentes } from '../../promociones/hooks/usePromociones'
import { useHerramientas } from '../hooks/useHerramientas'
import { useEliminarHerramienta } from '../hooks/useEliminarHerramienta'
import { puedeCambiarCosto, puedeEditarCatalogo } from '../permisos'
import type { Herramienta } from '../api/catalogoApi'

// Catálogo de herramientas (HU6): cuadrícula de tarjetas con foto (o
// lista), búsqueda y filtros, para todos los roles; alta, edición y
// borrado solo para Administrador y Supervisor (el Empleado no ve esos
// botones), en un panel lateral. HU7: el costo unitario lo cambia solo el
// Administrador; su historial lo consultan todos.

type Filtro = 'todas' | 'listas' | 'faltan' | 'sin-foto'
type Vista = 'cuadricula' | 'lista'
type Panel = { tipo: 'nueva' } | { tipo: 'editar' | 'historial'; herramienta: Herramienta }

function faltanDatosEOQ(h: Herramienta): boolean {
  return [h.demanda_anual, h.costo_pedido, h.costo_almacenamiento_unitario, h.tiempo_entrega_dias].some((v) => v === null)
}

const FILTROS: Record<Filtro, (h: Herramienta) => boolean> = {
  todas: () => true,
  listas: (h) => !faltanDatosEOQ(h),
  faltan: faltanDatosEOQ,
  'sin-foto': (h) => !h.imagen,
}

function coincide(h: Herramienta, texto: string): boolean {
  const buscado = texto.toLocaleLowerCase('es')
  return [h.codigo, h.nombre, h.modelo, h.proveedor_nombre ?? ''].some((v) => v.toLocaleLowerCase('es').includes(buscado))
}

function mensajeErrorBorrado(error: unknown): string {
  if (isAxiosError(error) && error.response?.status === 409) {
    return (error.response.data as { detail?: string }).detail ?? 'La herramienta está en uso.'
  }
  return 'No se pudo eliminar la herramienta. Intenta de nuevo.'
}

const vacio = <span className="text-muted">—</span>

interface AccionesProps {
  herramienta: Herramienta
  puedeEditar: boolean
  onAbrir: (panel: Panel) => void
  onEliminar: (h: Herramienta) => void
}

function Acciones({ herramienta: h, puedeEditar, onAbrir, onEliminar }: AccionesProps) {
  return (
    <div className="flex items-center justify-end gap-0.5">
      <IconButton etiqueta={`Historial de costos de ${h.nombre}`} onClick={() => onAbrir({ tipo: 'historial', herramienta: h })}>
        <History size={17} aria-hidden />
      </IconButton>
      {puedeEditar && (
        <>
          <IconButton etiqueta={`Editar ${h.nombre}`} onClick={() => onAbrir({ tipo: 'editar', herramienta: h })}>
            <Pencil size={17} aria-hidden />
          </IconButton>
          <IconButton etiqueta={`Eliminar ${h.nombre}`} peligro onClick={() => onEliminar(h)}>
            <Trash2 size={17} aria-hidden />
          </IconButton>
        </>
      )}
    </div>
  )
}

export function CatalogoPage() {
  const session = getSession()
  const puedeEditar = session ? puedeEditarCatalogo(session.rol) : false
  const { data: herramientas, isLoading, isError, refetch } = useHerramientas()
  // HU23: la etiqueta de promoción también se ve en el catálogo.
  const vigentes = usePromocionesVigentes()
  const eliminar = useEliminarHerramienta()
  const [buscar, setBuscar] = useState('')
  const [filtro, setFiltro] = useState<Filtro>('todas')
  const [vista, setVista] = usePreferencia<Vista>('catalogo-vista', 'cuadricula')
  // El contenido del panel se conserva mientras se cierra (animación);
  // `clave` reinicia el formulario cada vez que se abre.
  const [panel, setPanel] = useState<Panel & { clave: number }>({ tipo: 'nueva', clave: 0 })
  const [panelAbierto, setPanelAbierto] = useState(false)
  const [porEliminar, setPorEliminar] = useState<Herramienta | null>(null)

  const visibles = useMemo(
    () => (herramientas ?? []).filter((h) => FILTROS[filtro](h) && (!buscar.trim() || coincide(h, buscar.trim()))),
    [herramientas, filtro, buscar],
  )

  function abrir(nuevo: Panel) {
    setPanel((anterior) => ({ ...nuevo, clave: anterior.clave + 1 }))
    setPanelAbierto(true)
  }

  function pedirBorrado(h: Herramienta) {
    eliminar.reset()
    setPorEliminar(h)
  }

  function confirmarBorrado() {
    if (!porEliminar) return
    eliminar.mutate(porEliminar.id, { onSuccess: () => setPorEliminar(null) })
  }

  const tituloPanel =
    panel.tipo === 'nueva' ? 'Nueva herramienta' : panel.tipo === 'editar' ? `Editar ${panel.herramienta.nombre}` : 'Historial de costos'
  const descripcionPanel =
    panel.tipo === 'historial' ? `${panel.herramienta.codigo} · ${panel.herramienta.nombre}` : panel.tipo === 'editar' ? panel.herramienta.codigo : undefined

  const hayFiltro = filtro !== 'todas' || buscar.trim() !== ''

  return (
    <>
      <PageHeader
        migas={['Inventario', 'Catálogo']}
        titulo="Catálogo"
        subtitulo={
          puedeEditar
            ? 'Herramientas con su foto, proveedor y datos de compra.'
            : 'Solo consulta: el alta y la edición las hace un Administrador o Supervisor.'
        }
        acciones={
          puedeEditar && (
            <Button variante="primary" icono={<Plus size={16} aria-hidden />} onClick={() => abrir({ tipo: 'nueva' })}>
              Nueva herramienta
            </Button>
          )
        }
      />

      <div className="flex flex-wrap items-center gap-3">
        <SearchInput
          etiqueta="Buscar herramienta"
          placeholder="Buscar por código, nombre, modelo o proveedor"
          value={buscar}
          onChange={(e) => setBuscar(e.target.value)}
          className="w-[340px]"
        />
        <SegmentedControl<Filtro>
          etiqueta="Filtrar herramientas"
          valor={filtro}
          onCambiar={setFiltro}
          opciones={[
            { valor: 'todas', texto: 'Todas' },
            { valor: 'listas', texto: 'Con datos EOQ' },
            { valor: 'faltan', texto: 'Faltan datos' },
            { valor: 'sin-foto', texto: 'Sin foto' },
          ]}
        />
        <SegmentedControl<Vista>
          etiqueta="Vista"
          className="ml-auto"
          valor={vista}
          onCambiar={setVista}
          opciones={[
            { valor: 'cuadricula', texto: <LayoutGrid size={16} aria-hidden />, etiqueta: 'Vista en tarjetas' },
            { valor: 'lista', texto: <List size={16} aria-hidden />, etiqueta: 'Vista en lista' },
          ]}
        />
      </div>

      {isError && (
        <Aviso tono="error" accion={<Button tamano="sm" onClick={() => refetch()}>Reintentar</Button>}>
          No se pudo cargar el catálogo.
        </Aviso>
      )}

      {isLoading &&
        (vista === 'cuadricula' ? (
          <SkeletonTarjetas />
        ) : (
          <Card sinPadding>
            <SkeletonFilas filas={6} columnas={6} />
          </Card>
        ))}

      {herramientas && visibles.length === 0 && (
        <Card sinPadding>
          {hayFiltro ? (
            <EmptyState
              icono={SearchX}
              titulo="Ninguna herramienta coincide"
              ayuda="Prueba con otro texto o quita el filtro."
              accion={<Button onClick={() => { setBuscar(''); setFiltro('todas') }}>Ver todas</Button>}
            />
          ) : (
            <EmptyState
              icono={Boxes}
              titulo="Todavía no hay herramientas"
              ayuda={puedeEditar ? 'Carga la primera con su foto y sus datos de compra.' : 'Cuando se carguen, aparecerán acá.'}
              accion={puedeEditar && <Button icono={<Plus size={16} aria-hidden />} onClick={() => abrir({ tipo: 'nueva' })}>Nueva herramienta</Button>}
            />
          )}
        </Card>
      )}

      {visibles.length > 0 && vista === 'cuadricula' && (
        <ul className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-5">
          {visibles.map((h, i) => (
            <li key={h.id}>
              <Aparecer indice={i} className="h-full">
                <Card interactiva sinPadding className="flex h-full flex-col p-3">
                  <ProductImage src={h.imagen} alt={h.nombre} />
                  <div className="flex flex-1 flex-col px-2 pt-3.5">
                    <p className="text-xs font-semibold text-muted">{h.codigo}</p>
                    <h2 className="mt-0.5 line-clamp-2 text-[15px] font-semibold leading-snug tracking-[-0.01em] text-ink">{h.nombre}</h2>
                    <p className="mt-0.5 truncate text-xs text-muted">
                      {[h.modelo, h.proveedor_nombre].filter(Boolean).join(' · ') || 'Sin modelo ni proveedor'}
                    </p>
                    <div className="mt-3 flex items-center gap-2">
                      <span className="text-[17px] font-bold tracking-[-0.03em] text-ink tabular-nums">
                        {h.costo_unitario === null ? vacio : monto(h.costo_unitario)}
                      </span>
                      <span className="text-xs text-muted tabular-nums">· caja de {h.unidades_por_caja}</span>
                    </div>
                    {vigentes(h.id).length > 0 && (
                      <div className="mt-2 flex flex-wrap gap-1.5">
                        {vigentes(h.id).map((p) => (
                          <EtiquetaPromocion key={p.id} descuento={p.descuento_porcentaje} sucursal={p.sucursal_nombre} />
                        ))}
                      </div>
                    )}
                    <div className="mt-auto flex items-center justify-between gap-2 pt-3">
                      {faltanDatosEOQ(h) ? <Badge tono="warn">Faltan datos EOQ</Badge> : <Badge tono="ok">Datos EOQ</Badge>}
                      <Acciones herramienta={h} puedeEditar={puedeEditar} onAbrir={abrir} onEliminar={pedirBorrado} />
                    </div>
                  </div>
                </Card>
              </Aparecer>
            </li>
          ))}
        </ul>
      )}

      {visibles.length > 0 && vista === 'lista' && (
        <Card sinPadding className="overflow-hidden">
          <Table>
            <THead>
              <tr>
                <Th>Herramienta</Th>
                <Th>Proveedor</Th>
                <Th numerico>Unid./caja</Th>
                <Th numerico>Costo unit.</Th>
                <Th numerico>Demanda anual</Th>
                <Th numerico>Costo pedido</Th>
                <Th numerico>Costo almac.</Th>
                <Th numerico>Entrega (días)</Th>
                <Th>Promoción</Th>
                <Th><span className="sr-only">Acciones</span></Th>
              </tr>
            </THead>
            <tbody>
              {visibles.map((h) => (
                <Tr key={h.id}>
                  <Td className="max-w-[280px]"><CeldaHerramienta codigo={h.codigo} nombre={h.nombre} imagen={h.imagen} /></Td>
                  <Td>{h.proveedor_nombre ?? vacio}</Td>
                  <Td numerico>{h.unidades_por_caja}</Td>
                  <Td numerico className="font-semibold">{h.costo_unitario === null ? vacio : monto(h.costo_unitario)}</Td>
                  <Td numerico>{h.demanda_anual ?? vacio}</Td>
                  <Td numerico>{h.costo_pedido ?? vacio}</Td>
                  <Td numerico>{h.costo_almacenamiento_unitario ?? vacio}</Td>
                  <Td numerico>{h.tiempo_entrega_dias ?? vacio}</Td>
                  <Td>
                    {vigentes(h.id).length > 0 ? (
                      <div className="flex flex-wrap gap-1.5">
                        {vigentes(h.id).map((p) => (
                          <EtiquetaPromocion key={p.id} descuento={p.descuento_porcentaje} sucursal={p.sucursal_nombre} />
                        ))}
                      </div>
                    ) : vacio}
                  </Td>
                  <Td><Acciones herramienta={h} puedeEditar={puedeEditar} onAbrir={abrir} onEliminar={pedirBorrado} /></Td>
                </Tr>
              ))}
            </tbody>
          </Table>
        </Card>
      )}

      <SidePanel
        abierto={panelAbierto}
        onCerrar={() => setPanelAbierto(false)}
        titulo={tituloPanel}
        descripcion={descripcionPanel}
        ancho={panel.tipo === 'historial' ? 'md' : 'lg'}
      >
        {panel.tipo === 'historial' ? (
          <HistorialCostos key={panel.clave} herramienta={panel.herramienta} />
        ) : (
          <HerramientaForm
            key={panel.clave}
            herramienta={panel.tipo === 'editar' ? panel.herramienta : null}
            onTerminar={() => setPanelAbierto(false)}
            puedeCambiarCosto={session ? puedeCambiarCosto(session.rol) : false}
          />
        )}
      </SidePanel>

      <ConfirmModal
        abierto={porEliminar !== null}
        onCerrar={() => setPorEliminar(null)}
        onConfirmar={confirmarBorrado}
        titulo="¿Eliminar la herramienta?"
        textoConfirmar="Eliminar"
        cargando={eliminar.isPending}
        error={eliminar.isError ? mensajeErrorBorrado(eliminar.error) : null}
      >
        {porEliminar && (
          <>
            Se eliminará <strong className="font-semibold text-ink">{porEliminar.codigo} · {porEliminar.nombre}</strong>. Si
            ya tiene movimientos o historial de costos, no se puede eliminar.
          </>
        )}
      </ConfirmModal>
    </>
  )
}
