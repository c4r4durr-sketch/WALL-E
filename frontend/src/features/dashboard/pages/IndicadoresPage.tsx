import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useClasificacionABC } from '../hooks/useIndicadores'
import { TablaABC } from '../components/TablaABC'
import { DetalleEOQROP } from '../components/DetalleEOQROP'

// Indicadores de compra (HU17–HU21): clasificación ABC de todo el catálogo
// y, al elegir una herramienta, cuánto pedir (EOQ) y cuándo (ROP).
export function IndicadoresPage() {
  const { data: abc, isLoading, isError } = useClasificacionABC()
  const [seleccionada, setSeleccionada] = useState<number | null>(null)

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <div>
          <Link to="/" className="text-sm text-slate-500 hover:underline">← Volver</Link>
          <h1 className="mt-2 text-xl font-semibold text-slate-800">Indicadores de compra</h1>
          <p className="text-sm text-slate-500">Elige una herramienta de la tabla para ver su EOQ y su punto de reorden.</p>
        </div>

        {seleccionada !== null && <DetalleEOQROP herramientaId={seleccionada} />}

        {isLoading && <p className="text-sm text-slate-500">Cargando...</p>}
        {isError && <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">No se pudo cargar la clasificación.</p>}
        {abc && <TablaABC filas={abc} seleccionada={seleccionada} onSeleccionar={setSeleccionada} />}
      </div>
    </div>
  )
}
