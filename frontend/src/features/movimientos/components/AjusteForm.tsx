import { useState, type FormEvent } from 'react'
import type { Herramienta } from '../../catalogo/api/catalogoApi'
import type { Sucursal } from '../../usuarios/api/usuariosApi'
import type { TipoUnidad } from '../api/movimientosApi'
import { useRegistrarAjuste, useStock } from '../hooks/useMovimientos'
import { desgloseCajas } from '../formato'
import { erroresDelBackend } from '../errores'

// Ajuste de inventario: CORRECCIÓN de stock, no una operación normal del
// mostrador. Por eso vive en una sección aparte (ámbar, cerrada por
// defecto) y solo la ve Administrador/Supervisor. Los movimientos no se
// editan ni se borran: un error se corrige con un ajuste que queda en el
// historial con su motivo. No cuenta como demanda para EOQ/ABC.

interface Props {
  herramienta: Herramienta
  sucursales: Sucursal[]
}

export function AjusteForm({ herramienta, sucursales }: Props) {
  const [abierto, setAbierto] = useState(false)
  const [sentido, setSentido] = useState<'POSITIVO' | 'NEGATIVO'>('NEGATIVO')
  const [unidad, setUnidad] = useState<TipoUnidad>('UNIDAD')
  const [cantidad, setCantidad] = useState('')
  const [sucursal, setSucursal] = useState('')
  const [motivo, setMotivo] = useState('')
  const { data: stock } = useStock(herramienta.id)
  const { mutate, isPending, error, isSuccess, reset } = useRegistrarAjuste()
  const errores = erroresDelBackend(error)

  const cantidadNumero = Number(cantidad)
  const unidades = unidad === 'CAJA' ? cantidadNumero * herramienta.unidades_por_caja : cantidadNumero
  const stockSucursal = stock?.find((s) => String(s.sucursal_id) === sucursal)
  const stockResultante = (stockSucursal?.unidades ?? 0) + (sentido === 'POSITIVO' ? unidades : -unidades)
  const listo = sucursal !== '' && cantidadNumero >= 1 && motivo.trim() !== ''

  function limpiarAvisos() {
    if (error || isSuccess) reset()
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    mutate(
      {
        herramienta: herramienta.id,
        sucursal: Number(sucursal),
        sentido,
        tipo_unidad: unidad,
        cantidad: cantidadNumero,
        motivo: motivo.trim(),
      },
      { onSuccess: () => { setCantidad(''); setMotivo('') } },
    )
  }

  if (!abierto) {
    return (
      <button
        type="button"
        onClick={() => setAbierto(true)}
        className="w-full rounded-lg border border-dashed border-amber-400 bg-amber-50 px-4 py-3 text-left text-sm text-amber-800 hover:bg-amber-100"
      >
        <span className="font-medium">Registrar un ajuste de inventario…</span>
        <span className="block text-xs text-amber-700">
          Solo para corregir errores de conteo, roturas o pérdidas. No es una entrada ni una salida normal.
        </span>
      </button>
    )
  }

  const opcion = (activa: boolean) =>
    `flex-1 rounded-md border px-3 py-2 text-sm font-medium ${
      activa ? 'border-amber-700 bg-amber-700 text-white' : 'border-amber-300 bg-white text-amber-900 hover:bg-amber-100'
    }`

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border-2 border-amber-300 bg-amber-50 p-6" noValidate>
      <div className="flex items-start justify-between gap-4">
        <div>
          <h2 className="text-lg font-semibold text-amber-900">Ajuste de inventario (corrección)</h2>
          <p className="text-xs text-amber-800">
            Queda en el historial con tu usuario y el motivo. No cuenta como venta para los indicadores.
          </p>
        </div>
        <button type="button" onClick={() => { setAbierto(false); reset() }} className="text-sm text-amber-800 hover:underline">
          Cerrar
        </button>
      </div>

      <div className="flex gap-2" role="group" aria-label="Sentido del ajuste">
        <button type="button" className={opcion(sentido === 'POSITIVO')} onClick={() => { setSentido('POSITIVO'); limpiarAvisos() }}>
          Sumar al stock
        </button>
        <button type="button" className={opcion(sentido === 'NEGATIVO')} onClick={() => { setSentido('NEGATIVO'); limpiarAvisos() }}>
          Restar del stock
        </button>
      </div>

      <div>
        <label htmlFor="ajuste-sucursal" className="mb-1 block text-sm font-medium text-amber-900">Sucursal</label>
        <select
          id="ajuste-sucursal"
          value={sucursal}
          onChange={(event) => { setSucursal(event.target.value); limpiarAvisos() }}
          className="w-full rounded-md border border-amber-300 bg-white px-3 py-2 text-sm"
        >
          <option value="" disabled>Selecciona una sucursal</option>
          {sucursales.map((s) => (
            <option key={s.id} value={s.id}>{s.nombre}</option>
          ))}
        </select>
        {stockSucursal && (
          <p className="mt-1 text-xs text-amber-800">
            Stock actual: <span className="font-medium">{stockSucursal.unidades} unidades</span>
            {herramienta.unidades_por_caja > 1 &&
              ` (${desgloseCajas(stockSucursal.cajas_completas, stockSucursal.unidades_sueltas)})`}
            {cantidadNumero >= 1 && stockResultante >= 0 && ` → quedaría en ${stockResultante}`}
          </p>
        )}
        {stockSucursal && cantidadNumero >= 1 && stockResultante < 0 && (
          <p className="mt-1 text-xs font-medium text-red-600">
            No alcanza: no se pueden restar {unidades} unidades si hay {stockSucursal.unidades}.
          </p>
        )}
        {errores.sucursal && <p className="mt-1 text-xs text-red-600">{errores.sucursal}</p>}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="ajuste-cantidad" className="mb-1 block text-sm font-medium text-amber-900">Cantidad</label>
          <input
            id="ajuste-cantidad"
            type="number"
            min={1}
            step={1}
            value={cantidad}
            onChange={(event) => { setCantidad(event.target.value); limpiarAvisos() }}
            className="w-full rounded-md border border-amber-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <span className="mb-1 block text-sm font-medium text-amber-900">Unidad</span>
          <div className="flex gap-2" role="group" aria-label="Unidad del ajuste">
            {(['UNIDAD', 'CAJA'] as const).map((u) => (
              <button key={u} type="button" className={opcion(unidad === u)} onClick={() => { setUnidad(u); limpiarAvisos() }}>
                {u === 'UNIDAD' ? 'Unidades' : `Cajas (×${herramienta.unidades_por_caja})`}
              </button>
            ))}
          </div>
        </div>
      </div>
      {errores.cantidad && <p className="text-sm text-red-600">{errores.cantidad}</p>}

      <div>
        <label htmlFor="ajuste-motivo" className="mb-1 block text-sm font-medium text-amber-900">Motivo *</label>
        <textarea
          id="ajuste-motivo"
          rows={2}
          maxLength={255}
          value={motivo}
          placeholder="Ej.: conteo físico del 20/09 encontró 3 unidades menos"
          onChange={(event) => { setMotivo(event.target.value); limpiarAvisos() }}
          className="w-full rounded-md border border-amber-300 px-3 py-2 text-sm"
        />
        {errores.motivo && <p className="mt-1 text-xs text-red-600">{errores.motivo}</p>}
      </div>

      {errores.detail && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errores.detail}</p>
      )}
      {error && Object.keys(errores).length === 0 && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          No se pudo registrar el ajuste. Intenta de nuevo.
        </p>
      )}
      {isSuccess && (
        <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">Ajuste registrado.</p>
      )}

      <button
        type="submit"
        disabled={isPending || !listo}
        className="w-full rounded-md bg-amber-700 px-3 py-2 text-sm font-medium text-white hover:bg-amber-800 disabled:opacity-50"
      >
        {isPending ? 'Registrando...' : sentido === 'POSITIVO' ? 'Registrar ajuste (sumar)' : 'Registrar ajuste (restar)'}
      </button>
    </form>
  )
}
