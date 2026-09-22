import { Link } from 'react-router-dom'
import { HerramientaForm } from '../components/HerramientaForm'
import { useHerramientas } from '../hooks/useHerramientas'

// Catálogo de herramientas. Por ahora: alta (con los datos de EOQ/ROP) y
// listado de solo lectura. Editar y eliminar llegan con el CRUD completo
// (sub-paso 4.2).
function mostrar(valor: number | null) {
  return valor ?? <span className="text-slate-400">—</span>
}

export function CatalogoPage() {
  const { data: herramientas, isLoading, isError } = useHerramientas()

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <Link to="/" className="text-sm text-slate-500 hover:underline">
            ← Volver
          </Link>
          <h1 className="mt-2 text-xl font-semibold text-slate-800">Catálogo de herramientas</h1>
        </div>

        <HerramientaForm />

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
              </tr>
            </thead>
            <tbody>
              {isLoading && (
                <tr><td colSpan={8} className="px-3 py-4 text-center text-slate-500">Cargando...</td></tr>
              )}
              {isError && (
                <tr><td colSpan={8} className="px-3 py-4 text-center text-red-600">No se pudo cargar el catálogo.</td></tr>
              )}
              {herramientas?.length === 0 && (
                <tr><td colSpan={8} className="px-3 py-4 text-center text-slate-500">Todavía no hay herramientas cargadas.</td></tr>
              )}
              {herramientas?.map((h) => (
                <tr key={h.id} className="border-t border-slate-100">
                  <td className="px-3 py-2 font-medium text-slate-800">{h.codigo}</td>
                  <td className="px-3 py-2">{h.nombre}</td>
                  <td className="px-3 py-2">{h.modelo || <span className="text-slate-400">—</span>}</td>
                  <td className="px-3 py-2 text-right">{h.unidades_por_caja}</td>
                  <td className="px-3 py-2 text-right">{mostrar(h.demanda_anual)}</td>
                  <td className="px-3 py-2 text-right">{mostrar(h.costo_pedido)}</td>
                  <td className="px-3 py-2 text-right">{mostrar(h.costo_almacenamiento_unitario)}</td>
                  <td className="px-3 py-2 text-right">{mostrar(h.tiempo_entrega_dias)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
