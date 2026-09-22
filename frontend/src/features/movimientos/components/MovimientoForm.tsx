import { useState, type FormEvent } from 'react'
import type { Herramienta } from '../../catalogo/api/catalogoApi'
import type { Sucursal } from '../../usuarios/api/usuariosApi'
import type { TipoOperacion, TipoUnidad } from '../api/movimientosApi'
import { useRegistrarMovimiento, useStock } from '../hooks/useMovimientos'
import { desgloseCajas } from '../formato'
import { erroresDelBackend } from '../errores'

// Formulario de entrada/salida (HU9) para la herramienta elegida en la
// página. Muestra el stock actual de la sucursal y, si se registra en
// cajas, su equivalente en unidades. La validación real (stock suficiente,
// sucursal del empleado) la hace el backend; acá solo se informa.

interface Props {
  herramienta: Herramienta
  sucursales: Sucursal[]
  // Empleado: su sucursal viene fija (solo puede operar en su mostrador).
  sucursalFija: number | null
}

export function MovimientoForm({ herramienta, sucursales, sucursalFija }: Props) {
  const [tipo, setTipo] = useState<TipoOperacion>('ENTRADA')
  const [unidad, setUnidad] = useState<TipoUnidad>('UNIDAD')
  const [cantidad, setCantidad] = useState('')
  const [sucursal, setSucursal] = useState<string>(sucursalFija ? String(sucursalFija) : '')
  const { data: stock } = useStock(herramienta.id)
  const { mutate, isPending, error, isSuccess, reset } = useRegistrarMovimiento()
  const errores = erroresDelBackend(error)

  const cantidadNumero = Number(cantidad)
  const unidadesEquivalentes = unidad === 'CAJA' ? cantidadNumero * herramienta.unidades_por_caja : cantidadNumero
  const stockSucursal = stock?.find((s) => String(s.sucursal_id) === sucursal)

  function limpiarAvisos() {
    if (error || isSuccess) reset()
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    mutate(
      {
        herramienta: herramienta.id,
        sucursal: Number(sucursal),
        tipo_movimiento: tipo,
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

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm" noValidate>
      <h2 className="text-lg font-semibold text-slate-800">Registrar movimiento</h2>

      <div className="flex gap-2" role="group" aria-label="Tipo de movimiento">
        {(['ENTRADA', 'SALIDA'] as const).map((t) => (
          <button key={t} type="button" className={opcion(tipo === t)} onClick={() => { setTipo(t); limpiarAvisos() }}>
            {t === 'ENTRADA' ? 'Entrada' : 'Salida'}
          </button>
        ))}
      </div>

      <div>
        <label htmlFor="sucursal" className="mb-1 block text-sm font-medium text-slate-700">Sucursal</label>
        <select
          id="sucursal"
          value={sucursal}
          disabled={sucursalFija !== null}
          onChange={(event) => { setSucursal(event.target.value); limpiarAvisos() }}
          className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm disabled:bg-slate-100"
        >
          <option value="" disabled>Selecciona una sucursal</option>
          {sucursales.map((s) => (
            <option key={s.id} value={s.id}>{s.nombre}</option>
          ))}
        </select>
        {stockSucursal && (
          <p className="mt-1 text-xs text-slate-500">
            Stock actual: <span className="font-medium text-slate-700">{stockSucursal.unidades} unidades</span>
            {herramienta.unidades_por_caja > 1 &&
              ` (${desgloseCajas(stockSucursal.cajas_completas, stockSucursal.unidades_sueltas)})`}
          </p>
        )}
        {errores.sucursal && <p className="mt-1 text-xs text-red-600">{errores.sucursal}</p>}
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <div>
          <label htmlFor="cantidad" className="mb-1 block text-sm font-medium text-slate-700">Cantidad</label>
          <input
            id="cantidad"
            type="number"
            min={1}
            step={1}
            value={cantidad}
            onChange={(event) => { setCantidad(event.target.value); limpiarAvisos() }}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
        <div>
          <span className="mb-1 block text-sm font-medium text-slate-700">Unidad</span>
          <div className="flex gap-2" role="group" aria-label="Unidad">
            {(['UNIDAD', 'CAJA'] as const).map((u) => (
              <button key={u} type="button" className={opcion(unidad === u)} onClick={() => { setUnidad(u); limpiarAvisos() }}>
                {u === 'UNIDAD' ? 'Unidades' : `Cajas (×${herramienta.unidades_por_caja})`}
              </button>
            ))}
          </div>
        </div>
      </div>
      {unidad === 'CAJA' && cantidadNumero > 0 && (
        <p className="text-xs text-slate-500">
          = {unidadesEquivalentes} unidades ({cantidadNumero} × {herramienta.unidades_por_caja})
        </p>
      )}
      {errores.cantidad && <p className="text-sm text-red-600">{errores.cantidad}</p>}

      {errores.detail && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errores.detail}</p>
      )}
      {error && Object.keys(errores).length === 0 && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          No se pudo registrar el movimiento. Intenta de nuevo.
        </p>
      )}
      {isSuccess && (
        <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">Movimiento registrado.</p>
      )}

      <button
        type="submit"
        disabled={isPending || !sucursal || !(cantidadNumero >= 1)}
        className="w-full rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
      >
        {isPending ? 'Registrando...' : tipo === 'ENTRADA' ? 'Registrar entrada' : 'Registrar salida'}
      </button>
    </form>
  )
}
