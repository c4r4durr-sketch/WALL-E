import { useState } from 'react'
import { ClipboardList, Pencil, Plus, Power, PowerOff, SearchX, Trash2 } from 'lucide-react'
import {
  Aviso,
  Badge,
  Button,
  Card,
  ConfirmModal,
  EmptyState,
  IconButton,
  PageHeader,
  SearchInput,
  SidePanel,
  SkeletonFilas,
  Table,
  THead,
  Td,
  Th,
  Tr,
  cx,
} from '../../../components/ui'
import { getSession } from '../../auth/session'
import { mensajeDeError } from '../../../shared/api/errores'
import { useDebounced } from '../../../shared/hooks/useDebounced'
import { ProveedorForm } from '../components/ProveedorForm'
import { useEditarProveedor, useEliminarProveedor, useProveedores } from '../hooks/useProveedores'
import { puedeGestionarProveedores } from '../permisos'
import type { Proveedor } from '../api/proveedoresApi'

// Directorio de proveedores (HU8): todos consultan y buscan por nombre;
// solo el Administrador registra, edita, desactiva o elimina. Un proveedor
// con herramientas asociadas no se elimina (el backend responde 409): se
// desactiva, y entonces ya no se puede asignar a otras herramientas.

export function ProveedoresPage() {
  const session = getSession()
  const puedeGestionar = session ? puedeGestionarProveedores(session.rol) : false
  const [buscar, setBuscar] = useState('')
  const buscarDemorado = useDebounced(buscar.trim())
  const { data: proveedores, isLoading, isError, refetch } = useProveedores({ buscar: buscarDemorado })
  const editar = useEditarProveedor()
  const eliminar = useEliminarProveedor()
  // El contenido del panel se conserva mientras se cierra (animación).
  const [panel, setPanel] = useState<{ proveedor: Proveedor | null; clave: number }>({ proveedor: null, clave: 0 })
  const [panelAbierto, setPanelAbierto] = useState(false)
  const [porEliminar, setPorEliminar] = useState<Proveedor | null>(null)

  const errorEstado = editar.isError ? mensajeDeError(editar.error, 'No se pudo cambiar el estado del proveedor.') : null

  function abrir(proveedor: Proveedor | null) {
    setPanel((anterior) => ({ proveedor, clave: anterior.clave + 1 }))
    setPanelAbierto(true)
  }

  function confirmarBorrado() {
    if (!porEliminar) return
    eliminar.mutate(porEliminar.id, { onSuccess: () => setPorEliminar(null) })
  }

  return (
    <>
      <PageHeader
        migas={['Compras', 'Proveedores']}
        titulo="Proveedores"
        subtitulo={puedeGestionar ? 'A quién se le compra cada herramienta.' : 'Solo consulta: el directorio lo mantiene el Administrador.'}
        acciones={
          puedeGestionar && (
            <Button variante="primary" icono={<Plus size={16} aria-hidden />} onClick={() => abrir(null)}>
              Nuevo proveedor
            </Button>
          )
        }
      />

      <SearchInput
        etiqueta="Buscar proveedor por nombre"
        placeholder="Buscar por nombre"
        value={buscar}
        onChange={(e) => setBuscar(e.target.value)}
        className="w-[340px]"
      />

      {errorEstado && <Aviso tono="error">{errorEstado}</Aviso>}
      {isError && (
        <Aviso tono="error" accion={<Button tamano="sm" onClick={() => refetch()}>Reintentar</Button>}>
          No se pudieron cargar los proveedores.
        </Aviso>
      )}

      <Card sinPadding className="overflow-hidden">
        {isLoading && <SkeletonFilas filas={5} columnas={5} />}
        {proveedores?.length === 0 &&
          (buscarDemorado ? (
            <EmptyState
              icono={SearchX}
              titulo="Sin resultados"
              ayuda={`Ningún proveedor coincide con "${buscarDemorado}".`}
              accion={<Button onClick={() => setBuscar('')}>Limpiar búsqueda</Button>}
            />
          ) : (
            <EmptyState
              icono={ClipboardList}
              titulo="Todavía no hay proveedores"
              ayuda={puedeGestionar ? 'Registra el primero para asignarlo a las herramientas.' : 'Cuando se registren, aparecerán acá.'}
              accion={puedeGestionar && <Button icono={<Plus size={16} aria-hidden />} onClick={() => abrir(null)}>Nuevo proveedor</Button>}
            />
          ))}
        {proveedores && proveedores.length > 0 && (
          <Table>
            <THead>
              <tr>
                <Th>Nombre</Th>
                <Th>Teléfono</Th>
                <Th>Correo</Th>
                <Th numerico>Herramientas</Th>
                <Th>Estado</Th>
                {puedeGestionar && <Th><span className="sr-only">Acciones</span></Th>}
              </tr>
            </THead>
            <tbody>
              {proveedores.map((p) => (
                <Tr key={p.id} className={cx(!p.activo && 'text-muted')}>
                  <Td className="font-semibold">{p.nombre}</Td>
                  <Td className="tabular-nums">{p.telefono}</Td>
                  <Td>{p.email || <span className="text-muted">—</span>}</Td>
                  <Td numerico>{p.cantidad_herramientas}</Td>
                  <Td><Badge tono={p.activo ? 'ok' : 'neutral'}>{p.activo ? 'Activo' : 'Inactivo'}</Badge></Td>
                  {puedeGestionar && (
                    <Td>
                      <div className="flex justify-end gap-0.5">
                        <IconButton etiqueta={`Editar ${p.nombre}`} onClick={() => abrir(p)}>
                          <Pencil size={17} aria-hidden />
                        </IconButton>
                        <IconButton
                          etiqueta={p.activo ? `Desactivar ${p.nombre}` : `Activar ${p.nombre}`}
                          disabled={editar.isPending}
                          onClick={() => {
                            eliminar.reset()
                            editar.mutate({ id: p.id, activo: !p.activo })
                          }}
                        >
                          {p.activo ? <PowerOff size={17} aria-hidden /> : <Power size={17} aria-hidden />}
                        </IconButton>
                        {/* Con herramientas asociadas no se elimina: solo se ofrece desactivar. */}
                        {p.cantidad_herramientas === 0 && (
                          <IconButton
                            etiqueta={`Eliminar ${p.nombre}`}
                            peligro
                            onClick={() => {
                              eliminar.reset()
                              editar.reset()
                              setPorEliminar(p)
                            }}
                          >
                            <Trash2 size={17} aria-hidden />
                          </IconButton>
                        )}
                      </div>
                    </Td>
                  )}
                </Tr>
              ))}
            </tbody>
          </Table>
        )}
      </Card>

      <SidePanel
        abierto={panelAbierto}
        onCerrar={() => setPanelAbierto(false)}
        titulo={panel.proveedor ? `Editar ${panel.proveedor.nombre}` : 'Nuevo proveedor'}
      >
        <ProveedorForm key={panel.clave} proveedor={panel.proveedor} onTerminar={() => setPanelAbierto(false)} />
      </SidePanel>

      <ConfirmModal
        abierto={porEliminar !== null}
        onCerrar={() => setPorEliminar(null)}
        onConfirmar={confirmarBorrado}
        titulo="¿Eliminar el proveedor?"
        textoConfirmar="Eliminar"
        cargando={eliminar.isPending}
        error={eliminar.isError ? mensajeDeError(eliminar.error, 'No se pudo eliminar el proveedor.') : null}
      >
        {porEliminar && (
          <>Se eliminará <strong className="font-semibold text-ink">{porEliminar.nombre}</strong> del directorio.</>
        )}
      </ConfirmModal>
    </>
  )
}
