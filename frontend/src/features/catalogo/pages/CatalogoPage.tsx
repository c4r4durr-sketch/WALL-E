import { useState } from 'react'
import { Link } from 'react-router-dom'
import { isAxiosError } from 'axios'
import { getSession } from '../../auth/session'
import { HerramientaForm } from '../components/HerramientaForm'
import { useHerramientas } from '../hooks/useHerramientas'
import { useEliminarHerramienta } from '../hooks/useEliminarHerramienta'
import { puedeEditarCatalogo } from '../permisos'
import type { Herramienta } from '../api/catalogoApi'

// Catálogo de herramientas (HU6): listado para todos los roles; alta,
// edición y borrado solo para Administrador y Supervisor (el Empleado ve
// la tabla sin formulario ni botones).
function mostrar(valor: number | null) {
  return valor ?? <span className="text-slate-400">—</span>
}

function mensajeErrorBorrado(error: unknown): string {
  if (isAxiosError(error) && error.response?.status === 409) {
    return (error.response.data as { detail?: string }).detail ?? 'La herramienta está en uso.'
  }
  return 'No se pudo eliminar la herramienta. Intenta de nuevo.'
}

export function CatalogoPage() {
  const session = getSession()
  const puedeEditar = session ? puedeEditarCatalogo(session.rol) : false
  const { data: herramientas, isLoading, isError } = useHerramientas()
  const eliminar = useEliminarHerramienta()
  const [editando, setEditando] = useState<Herramienta | null>(null)
  const [confirmandoId, setConfirmandoId] = useState<number | null>(null)

  function empezarEdicion(herramienta: Herramienta) {
    setEditando(herramienta)
    setConfirmandoId(null)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  function confirmarBorrado(id: number) {
    eliminar.mutate(id, {
      onSettled: () => setConfirmandoId(null),
      onSuccess: () => {
        if (editando?.id === id) setEditando(null)
      },
    })
  }

  const columnas = puedeEditar ? 9 : 8

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <Link to="/" className="text-sm text-slate-500 hover:underline">
            ← Volver
          </Link>
          <h1 className="mt-2 text-xl font-semibold text-slate-800">Catálogo de herramientas</h1>
          {!puedeEditar && (
            <p className="mt-1 text-sm text-slate-500">Solo consulta: el alta y la edición las hace un Administrador o Supervisor.</p>
          )}
        </div>

        {puedeEditar && (
          <HerramientaForm
            key={editando?.id ?? 'nueva'}
            herramienta={editando}
            onTerminar={() => setEditando(null)}
          />
        )}

        {eliminar.isError && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            {mensajeErrorBorrado(eliminar.error)}
          </p>
        )}

        <div className="overflow-x-auto rounded-lg border border-slate-200 bg-white shadow-sm">
          <table className="w-full text-left text-sm">
            <thead className="bg-slate-100 text-slate-600">
              <tr>
                <th className="px-3 py-2">Código</th>
                <th className="px-3 py-2">Nombre</th>
                <th className="px-3 py-2">Modelo</th>
                <th className="px-3 py-2 text-right">Unid./caja</th>
                <th className="px-3 py-2 text-right">Demanda anual</th>
                <th className="px-3 py-2 text-right">Costo pedido</th>
                <th className="px-3 py-2 text-right">Costo almac.</th>
                <th className="px-3 py-2 text-right">Entrega (días)</th>
                {puedeEditar && <th className="px-3 py-2 text-right">Acciones</th>}
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={columnas} className="px-3 py-4 text-center text-slate-500">Cargando...</td></tr>
              )}
              {isError && (
                <tr><td colSpan={columnas} className="px-3 py-4 text-center text-red-600">No se pudo cargar el catálogo.</td></tr>
              )}
              {herramientas?.length === 0 && (
                <tr><td colSpan={columnas} className="px-3 py-4 text-center text-slate-500">Todavía no hay herramientas cargadas.</td></tr>
              )}
              {herramientas?.map((h) => (
                <tr key={h.id} className={`border-t border-slate-100 ${editando?.id === h.id ? 'bg-blue-50' : ''}`}>
                  <td className="px-3 py-2 font-medium text-slate-800">{h.codigo}</td>
                  <td className="px-3 py-2">{h.nombre}</td>
                  <td className="px-3 py-2">{h.modelo || <span className="text-slate-400">—</span>}</td>
                  <td className="px-3 py-2 text-right">{h.unidades_por_caja}</td>
                  <td className="px-3 py-2 text-right">{mostrar(h.demanda_anual)}</td>
                  <td className="px-3 py-2 text-right">{mostrar(h.costo_pedido)}</td>
                  <td className="px-3 py-2 text-right">{mostrar(h.costo_almacenamiento_unitario)}</td>
                  <td className="px-3 py-2 text-right">{mostrar(h.tiempo_entrega_dias)}</td>
                  {puedeEditar && (
                    <td className="whitespace-nowrap px-3 py-2 text-right">
                      {confirmandoId === h.id ? (
                        <span className="inline-flex items-center gap-2">
                          <span className="text-slate-600">¿Eliminar?</span>
                          <button
                            type="button"
                            onClick={() => confirmarBorrado(h.id)}
                            disabled={eliminar.isPending}
                            className="font-medium text-red-600 hover:underline disabled:opacity-50"
                          >
                            Sí
                          </button>
                          <button
                            type="button"
                            onClick={() => setConfirmandoId(null)}
                            className="font-medium text-slate-600 hover:underline"
                          >
                            No
                          </button>
                        </span>
                      ) : (
                        <span className="inline-flex gap-3">
                          <button
                            type="button"
                            onClick={() => empezarEdicion(h)}
                            className="font-medium text-blue-600 hover:underline"
                          >
                            Editar
                          </button>
                          <button
                            type="button"
                            onClick={() => {
                              eliminar.reset()
                              setConfirmandoId(h.id)
                            }}
                            className="font-medium text-red-600 hover:underline"
                          >
                            Eliminar
                          </button>
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
