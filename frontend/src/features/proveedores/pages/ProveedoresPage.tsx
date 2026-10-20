import { useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, Pencil, Plus, Power, PowerOff, Search, Trash2 } from 'lucide-react'
import { getSession } from '../../auth/session'
import { BotonIcono } from '../../../shared/components/BotonIcono'
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

type Panel = { modo: 'nuevo' } | { modo: 'editar'; proveedor: Proveedor } | null

export function ProveedoresPage() {
  const session = getSession()
  const puedeGestionar = session ? puedeGestionarProveedores(session.rol) : false
  const [buscar, setBuscar] = useState('')
  const buscarDemorado = useDebounced(buscar.trim())
  const { data: proveedores, isLoading, isError, refetch } = useProveedores({ buscar: buscarDemorado })
  const editar = useEditarProveedor()
  const eliminar = useEliminarProveedor()
  const [panel, setPanel] = useState<Panel>(null)
  const [confirmandoId, setConfirmandoId] = useState<number | null>(null)

  const columnas = puedeGestionar ? 6 : 5
  const errorAccion = eliminar.isError
    ? mensajeDeError(eliminar.error, 'No se pudo eliminar el proveedor.')
    : editar.isError
      ? mensajeDeError(editar.error, 'No se pudo cambiar el estado del proveedor.')
      : null

  function abrir(nuevoPanel: Panel) {
    setPanel(nuevoPanel)
    setConfirmandoId(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function confirmarBorrado(id: number) {
    eliminar.mutate(id, { onSettled: () => setConfirmandoId(null) })
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <div className="flex items-end justify-between gap-4">
          <div>
            <Link to="/" className="inline-flex items-center gap-1 text-sm text-slate-500 hover:underline">
              <ArrowLeft size={14} aria-hidden />
              Volver
            </Link>
            <h1 className="mt-2 text-xl font-semibold text-slate-800">Proveedores</h1>
            {!puedeGestionar && (
              <p className="mt-1 text-sm text-slate-500">Solo consulta: el directorio lo mantiene el Administrador.</p>
            )}
          </div>
          {puedeGestionar && (
            <button
              type="button"
              onClick={() => abrir({ modo: 'nuevo' })}
              className="inline-flex items-center gap-2 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700"
            >
              <Plus size={16} aria-hidden />
              Nuevo proveedor
            </button>
          )}
        </div>

        {panel && (
          <ProveedorForm
            key={panel.modo === 'editar' ? panel.proveedor.id : 'nuevo'}
            proveedor={panel.modo === 'editar' ? panel.proveedor : null}
            onTerminar={() => setPanel(null)}
          />
        )}

        <div className="relative max-w-sm">
          <Search size={16} aria-hidden className="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            type="search"
            value={buscar}
            onChange={(e) => setBuscar(e.target.value)}
            placeholder="Buscar por nombre"
            aria-label="Buscar proveedor por nombre"
            className="w-full rounded-md border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm"
          />
        </div>

        {errorAccion && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errorAccion}</p>
        )}

        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-100 text-slate-600">
              <tr>
                <th className="px-3 py-2">Nombre</th>
                <th className="px-3 py-2">Teléfono</th>
                <th className="px-3 py-2">Correo</th>
                <th className="px-3 py-2 text-right">Herramientas</th>
                <th className="px-3 py-2">Estado</th>
                {puedeGestionar && <th className="px-3 py-2 text-right">Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={columnas} className="px-3 py-4 text-center text-slate-500">Cargando...</td></tr>
              )}
              {isError && (
                <tr>
                  <td colSpan={columnas} className="px-3 py-4 text-center text-red-600">
                    No se pudieron cargar los proveedores.{' '}
                    <button type="button" onClick={() => refetch()} className="font-medium underline">Reintentar</button>
                  </td>
                </tr>
              )}
              {proveedores?.length === 0 && (
                <tr>
                  <td colSpan={columnas} className="px-3 py-4 text-center text-slate-500">
                    {buscarDemorado ? `Ningún proveedor coincide con "${buscarDemorado}".` : 'Todavía no hay proveedores registrados.'}
                  </td>
                </tr>
              )}
              {proveedores?.map((p) => (
                <tr key={p.id} className={`border-t border-slate-100 ${p.activo ? '' : 'text-slate-400'}`}>
                  <td className="px-3 py-2 font-medium">{p.nombre}</td>
                  <td className="px-3 py-2">{p.telefono}</td>
                  <td className="px-3 py-2">{p.email || <span className="text-slate-400">—</span>}</td>
                  <td className="px-3 py-2 text-right tabular-nums">{p.cantidad_herramientas}</td>
                  <td className="px-3 py-2">
                    <span
                      className={`rounded-full px-2 py-0.5 text-xs font-medium ${
                        p.activo ? 'bg-green-100 text-green-800' : 'bg-slate-200 text-slate-600'
                      }`}
                    >
                      {p.activo ? 'Activo' : 'Inactivo'}
                    </span>
                  </td>
                  {puedeGestionar && (
                    <td className="whitespace-nowrap px-3 py-2 text-right">
                      {confirmandoId === p.id ? (
                        <span className="inline-flex items-center gap-2">
                          <span className="text-slate-600">¿Eliminar?</span>
                          <button
                            type="button"
                            onClick={() => confirmarBorrado(p.id)}
                            disabled={eliminar.isPending}
                            className="font-medium text-red-600 hover:underline disabled:opacity-50"
                          >
                            Sí
                          </button>
                          <button type="button" onClick={() => setConfirmandoId(null)} className="font-medium text-slate-600 hover:underline">
                            No
                          </button>
                        </span>
                      ) : (
                        <span className="inline-flex gap-1">
                          <BotonIcono titulo="Editar" onClick={() => abrir({ modo: 'editar', proveedor: p })}>
                            <Pencil size={16} aria-hidden />
                          </BotonIcono>
                          <BotonIcono
                            titulo={p.activo ? 'Desactivar' : 'Activar'}
                            disabled={editar.isPending}
                            onClick={() => {
                              eliminar.reset()
                              editar.mutate({ id: p.id, activo: !p.activo })
                            }}
                          >
                            {p.activo ? <PowerOff size={16} aria-hidden /> : <Power size={16} aria-hidden />}
                          </BotonIcono>
                          {/* Con herramientas asociadas no se elimina: solo se ofrece desactivar. */}
                          {p.cantidad_herramientas === 0 && (
                            <BotonIcono
                              titulo="Eliminar"
                              peligro
                              onClick={() => {
                                eliminar.reset()
                                editar.reset()
                                setConfirmandoId(p.id)
                              }}
                            >
                              <Trash2 size={16} aria-hidden />
                            </BotonIcono>
                          )}
                        </span>
                      )}
                    </td>
                  )}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
