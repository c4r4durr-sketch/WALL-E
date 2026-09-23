import { useState, type FormEvent } from 'react'
import type { Herramienta } from '../../catalogo/api/catalogoApi'
import type { Sucursal } from '../../usuarios/api/usuariosApi'
import type { TipoUnidad } from '../../movimientos/api/movimientosApi'
import { useStock } from '../../movimientos/hooks/useMovimientos'
import { desgloseCajas } from '../../movimientos/formato'
import { erroresDelBackend } from '../../movimientos/errores'
import { useSolicitarTransferencia } from '../hooks/useTransferencias'

// Solicitud de transferencia (HU12). Queda PENDIENTE: el stock no se mueve
// hasta que un Administrador/Supervisor la completa. Muestra el stock en
// origen para no pedir más de lo que hay (el backend igual lo valida).

interface Props {
  herramientas: Herramienta[]
  sucursales: Sucursal[]
  // Empleado: el origen es siempre su sucursal.
  origenFijo: number | null
}

export function SolicitudForm({ herramientas, sucursales, origenFijo }: Props) {
  const [herramientaId, setHerramientaId] = useState('')
  const [origen, setOrigen] = useState(origenFijo ? String(origenFijo) : '')
  const [destino, setDestino] = useState('')
  const [unidad, setUnidad] = useState<TipoUnidad>('UNIDAD')
  const [cantidad, setCantidad] = useState('')
  const herramienta = herramientas.find((h) => String(h.id) === herramientaId)
  const { data: stock } = useStock(herramienta?.id ?? null)
  const { mutate, isPending, error, isSuccess, reset } = useSolicitarTransferencia()
  const errores = erroresDelBackend(error)

  const cantidadNumero = Number(cantidad)
  const unidades = herramienta && unidad === 'CAJA' ? cantidadNumero * herramienta.unidades_por_caja : cantidadNumero
  const stockOrigen = stock?.find((s) => String(s.sucursal_id) === origen)
  const listo = herramienta && origen && destino && origen !== destino && cantidadNumero >= 1

  function cambiar<T>(setter: (v: T) => void) {
    return (valor: T) => {
      setter(valor)
      if (error || isSuccess) reset()
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    mutate(
      {
        herramienta: Number(herramientaId),
        sucursal_origen: Number(origen),
        sucursal_destino: Number(destino),
        tipo_unidad: unidad,
        cantidad: cantidadNumero,
      },
      { onSuccess: () => setCantidad('') },
    )
  }

  const opcion = (activa: boolean) =>
    `flex-1 rounded-md border px-3 py-2 text-sm font-medium ${
      activa ? 'border-slate-800 bg-slate-800 text-white' : 'border-slate-300 bg-white text-slate-700 hover:bg-slate-100'
    }`
  const select = 'w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm disabled:bg-slate-100'

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm" noValidate>
      <div>
        <h2 className="text-lg font-semibold text-slate-800">Solicitar transferencia</h2>
        <p className="text-xs text-slate-500">Queda pendiente hasta que un Administrador o Supervisor la complete.</p>
      </div>

      <div>
        <label htmlFor="t-herramienta" className="mb-1 block text-sm font-medium text-slate-700">Herramienta</label>
        <select id="t-herramienta" value={herramientaId} onChange={(e) => cambiar(setHerramientaId)(e.target.value)} className={select}>
          <option value="">Selecciona una herramienta</option>
          {herramientas.map((h) => <option key={h.id} value={h.id}>{h.codigo} · {h.nombre}</option>)}
        </select>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="t-origen" className="mb-1 block text-sm font-medium text-slate-700">Desde (origen)</label>
          <select id="t-origen" value={origen} disabled={origenFijo !== null} onChange={(e) => cambiar(setOrigen)(e.target.value)} className={select}>
            <option value="" disabled>Selecciona</option>
            {sucursales.map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
          </select>
          {herramienta && stockOrigen && (
            <p className="mt-1 text-xs text-slate-500">
              Disponible: <span className="font-medium text-slate-700">{stockOrigen.unidades} unidades</span>
              {herramienta.unidades_por_caja > 1 && ` (${desgloseCajas(stockOrigen.cajas_completas, stockOrigen.unidades_sueltas)})`}
            </p>
          )}
          {errores.sucursal_origen && <p className="mt-1 text-xs text-red-600">{errores.sucursal_origen}</p>}
        </div>
        <div>
          <label htmlFor="t-destino" className="mb-1 block text-sm font-medium text-slate-700">Hacia (destino)</label>
          <select id="t-destino" value={destino} onChange={(e) => cambiar(setDestino)(e.target.value)} className={select}>
            <option value="" disabled>Selecciona</option>
            {sucursales.filter((s) => String(s.id) !== origen).map((s) => <option key={s.id} value={s.id}>{s.nombre}</option>)}
          </select>
          {errores.sucursal_destino && <p className="mt-1 text-xs text-red-600">{errores.sucursal_destino}</p>}
        </div>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="t-cantidad" className="mb-1 block text-sm font-medium text-slate-700">Cantidad</label>
          <input id="t-cantidad" type="number" min={1} step={1} value={cantidad}
            onChange={(e) => cambiar(setCantidad)(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm" />
        </div>
        <div>
          <span className="mb-1 block text-sm font-medium text-slate-700">Unidad</span>
          <div className="flex gap-2" role="group" aria-label="Unidad">
            {(['UNIDAD', 'CAJA'] as const).map((u) => (
              <button key={u} type="button" className={opcion(unidad === u)} onClick={() => cambiar(setUnidad)(u)}>
                {u === 'UNIDAD' ? 'Unidades' : `Cajas${herramienta ? ` (×${herramienta.unidades_por_caja})` : ''}`}
              </button>
            ))}
          </div>
        </div>
      </div>
      {herramienta && unidad === 'CAJA' && cantidadNumero > 0 && (
        <p className="text-xs text-slate-500">= {unidades} unidades</p>
      )}
      {errores.cantidad && <p className="text-sm text-red-600">{errores.cantidad}</p>}
      {errores.detail && <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errores.detail}</p>}
      {error && Object.keys(errores).length === 0 && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">No se pudo solicitar la transferencia.</p>
      )}
      {isSuccess && <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">Transferencia solicitada: queda pendiente de aprobación.</p>}

      <button type="submit" disabled={isPending || !listo}
        className="w-full rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50">
        {isPending ? 'Enviando...' : 'Solicitar transferencia'}
      </button>
    </form>
  )
}
