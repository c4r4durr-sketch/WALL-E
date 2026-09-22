import { useState, type FormEvent } from 'react'
import { isAxiosError } from 'axios'
import { useCrearHerramienta } from '../hooks/useCrearHerramienta'
import type { HerramientaPayload } from '../api/catalogoApi'

// Formulario de alta de herramientas (HU6), incluidos los datos de
// entrada de EOQ/ROP (HU15/HU16). Esos cuatro son opcionales: un campo
// vacío se envía como null y el indicador correspondiente queda sin
// calcular hasta que se complete.

const FORM_VACIO = {
  codigo: '',
  nombre: '',
  modelo: '',
  unidades_por_caja: '1',
  demanda_anual: '',
  costo_pedido: '',
  costo_almacenamiento_unitario: '',
  tiempo_entrega_dias: '',
}

type CampoForm = keyof typeof FORM_VACIO

function numeroONull(valor: string): number | null {
  return valor.trim() === '' ? null : Number(valor)
}

// El backend responde 400 con { campo: ["mensaje", ...] }: se muestra cada
// mensaje debajo de su campo en vez de un error genérico.
function erroresPorCampo(error: unknown): Record<string, string> {
  if (!isAxiosError(error) || error.response?.status !== 400) return {}
  const datos = error.response.data as Record<string, string[] | string>
  return Object.fromEntries(
    Object.entries(datos).map(([campo, mensajes]) => [
      campo,
      Array.isArray(mensajes) ? mensajes.join(' ') : String(mensajes),
    ]),
  )
}

export function HerramientaForm() {
  const [form, setForm] = useState(FORM_VACIO)
  const { mutate, isPending, error, isSuccess, reset } = useCrearHerramienta()
  const errores = erroresPorCampo(error)

  function actualizar(campo: CampoForm, valor: string) {
    setForm({ ...form, [campo]: valor })
    if (isSuccess) reset()
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const payload: HerramientaPayload = {
      codigo: form.codigo.trim(),
      nombre: form.nombre.trim(),
      modelo: form.modelo.trim(),
      unidades_por_caja: Number(form.unidades_por_caja),
      demanda_anual: numeroONull(form.demanda_anual),
      costo_pedido: numeroONull(form.costo_pedido),
      costo_almacenamiento_unitario: numeroONull(form.costo_almacenamiento_unitario),
      tiempo_entrega_dias: numeroONull(form.tiempo_entrega_dias),
    }
    mutate(payload, { onSuccess: () => setForm(FORM_VACIO) })
  }

  function campo(nombre: CampoForm, etiqueta: string, props: { type?: string; step?: string; ayuda?: string } = {}) {
    return (
      <div>
        <label htmlFor={nombre} className="mb-1 block text-sm font-medium text-slate-700">
          {etiqueta}
        </label>
        <input
          id={nombre}
          type={props.type ?? 'text'}
          step={props.step}
          min={props.type === 'number' ? 0 : undefined}
          value={form[nombre]}
          onChange={(event) => actualizar(nombre, event.target.value)}
          className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
        />
        {props.ayuda && !errores[nombre] && <p className="mt-1 text-xs text-slate-500">{props.ayuda}</p>}
        {errores[nombre] && <p className="mt-1 text-xs text-red-600">{errores[nombre]}</p>}
      </div>
    )
  }

  const errorGeneral = error && Object.keys(errores).length === 0

  return (
    <form onSubmit={handleSubmit} className="space-y-4 rounded-lg border border-slate-200 bg-white p-6 shadow-sm" noValidate>
      <h2 className="text-lg font-semibold text-slate-800">Nueva herramienta</h2>

      <div className="grid gap-3 sm:grid-cols-2">
        {campo('codigo', 'Código *')}
        {campo('nombre', 'Nombre *')}
        {campo('modelo', 'Modelo')}
        {campo('unidades_por_caja', 'Unidades por caja *', { type: 'number', step: '1' })}
      </div>

      <fieldset className="rounded-md border border-slate-200 p-4">
        <legend className="px-1 text-sm font-medium text-slate-700">Datos para EOQ / Punto de reorden (opcionales)</legend>
        <div className="grid gap-3 sm:grid-cols-2">
          {campo('demanda_anual', 'Demanda anual (unidades)', { type: 'number', step: '1', ayuda: 'D en la fórmula EOQ.' })}
          {campo('costo_pedido', 'Costo por pedido', { type: 'number', step: '0.01', ayuda: 'S: costo fijo de cada pedido.' })}
          {campo('costo_almacenamiento_unitario', 'Costo de almacenamiento por unidad/año', { type: 'number', step: '0.01', ayuda: 'H en la fórmula EOQ.' })}
          {campo('tiempo_entrega_dias', 'Tiempo de entrega (días)', { type: 'number', step: '1', ayuda: 'Para el punto de reorden.' })}
        </div>
      </fieldset>

      {errores.non_field_errors && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errores.non_field_errors}</p>
      )}
      {errorGeneral && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
          No se pudo guardar la herramienta. Intenta de nuevo.
        </p>
      )}
      {isSuccess && (
        <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">Herramienta guardada correctamente.</p>
      )}

      <button
        type="submit"
        disabled={isPending}
        className="w-full rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
      >
        {isPending ? 'Guardando...' : 'Guardar herramienta'}
      </button>
    </form>
  )
}
