import { useState, type FormEvent } from 'react'
import { Save, X } from 'lucide-react'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'
import { useCrearProveedor, useEditarProveedor } from '../hooks/useProveedores'
import type { Proveedor } from '../api/proveedoresApi'

// Alta y edición de un proveedor (HU8). Con `proveedor` funciona en modo
// edición; sin él, en modo alta. Las mismas reglas que el backend se
// revisan antes de enviar (nombre y teléfono obligatorios, formatos), y
// los mensajes del backend (nombre repetido) se muestran junto al campo.

interface FormState {
  nombre: string
  telefono: string
  email: string
}

type Errores = Partial<Record<keyof FormState, string>>

const FORM_VACIO: FormState = { nombre: '', telefono: '', email: '' }

function validar(form: FormState): Errores {
  const errores: Errores = {}
  if (!form.nombre.trim()) errores.nombre = 'El nombre es obligatorio.'
  const digitos = form.telefono.replace(/\D/g, '').length
  if (!form.telefono.trim()) {
    errores.telefono = 'El teléfono es obligatorio.'
  } else if (!/^\+?[\d\s()-]+$/.test(form.telefono.trim()) || digitos < 7 || digitos > 15) {
    errores.telefono = 'De 7 a 15 dígitos (se permiten espacios, guiones, paréntesis y + al inicio).'
  }
  if (form.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
    errores.email = 'Correo no válido.'
  }
  return errores
}

function MensajeError({ mensaje }: { mensaje?: string }) {
  return mensaje ? <p className="mt-1 text-xs text-red-600">{mensaje}</p> : null
}

interface Props {
  proveedor?: Proveedor | null
  onTerminar: () => void
}

export function ProveedorForm({ proveedor, onTerminar }: Props) {
  const editando = Boolean(proveedor)
  const crear = useCrearProveedor()
  const editar = useEditarProveedor()
  const mutacion = editando ? editar : crear
  const [form, setForm] = useState<FormState>(
    proveedor ? { nombre: proveedor.nombre, telefono: proveedor.telefono, email: proveedor.email } : FORM_VACIO,
  )
  const [errores, setErrores] = useState<Errores>({})
  const erroresServidor = erroresPorCampo(mutacion.error) as Errores
  const visibles: Errores = { ...erroresServidor, ...errores }
  const errorGeneral =
    mutacion.isError && Object.keys(erroresServidor).length === 0
      ? mensajeDeError(mutacion.error, 'No se pudo guardar el proveedor. Intenta de nuevo.')
      : null

  function setCampo(campo: keyof FormState, valor: string) {
    setForm((prev) => ({ ...prev, [campo]: valor }))
    if (errores[campo]) setErrores((prev) => ({ ...prev, [campo]: undefined }))
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const nuevos = validar(form)
    setErrores(nuevos)
    if (Object.keys(nuevos).length > 0) return
    const payload = { nombre: form.nombre.trim(), telefono: form.telefono.trim(), email: form.email.trim() }
    if (proveedor) {
      editar.mutate({ id: proveedor.id, ...payload }, { onSuccess: onTerminar })
    } else {
      crear.mutate(payload, { onSuccess: onTerminar })
    }
  }

  const inputClass = (campo: keyof FormState) =>
    `w-full rounded-md border px-3 py-2 text-sm ${visibles[campo] ? 'border-red-500' : 'border-slate-300'}`

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className={`space-y-4 rounded-lg border bg-white p-6 shadow-sm ${editando ? 'border-blue-300' : 'border-slate-200'}`}
    >
      <h2 className="text-lg font-semibold text-slate-800">
        {proveedor ? `Editar proveedor ${proveedor.nombre}` : 'Nuevo proveedor'}
      </h2>
      <div className="grid grid-cols-3 gap-4">
        <div>
          <label htmlFor="nombre" className="mb-1 block text-sm font-medium text-slate-700">Nombre *</label>
          <input id="nombre" value={form.nombre} onChange={(e) => setCampo('nombre', e.target.value)} className={inputClass('nombre')} />
          <MensajeError mensaje={visibles.nombre} />
        </div>
        <div>
          <label htmlFor="telefono" className="mb-1 block text-sm font-medium text-slate-700">Teléfono *</label>
          <input
            id="telefono"
            type="tel"
            value={form.telefono}
            onChange={(e) => setCampo('telefono', e.target.value)}
            className={inputClass('telefono')}
          />
          <MensajeError mensaje={visibles.telefono} />
        </div>
        <div>
          <label htmlFor="email" className="mb-1 block text-sm font-medium text-slate-700">Correo (opcional)</label>
          <input
            id="email"
            type="email"
            value={form.email}
            onChange={(e) => setCampo('email', e.target.value)}
            className={inputClass('email')}
          />
          <MensajeError mensaje={visibles.email} />
        </div>
      </div>

      {errorGeneral && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errorGeneral}</p>
      )}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={mutacion.isPending}
          className="inline-flex items-center gap-2 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          <Save size={16} aria-hidden />
          {mutacion.isPending ? 'Guardando...' : editando ? 'Guardar cambios' : 'Guardar proveedor'}
        </button>
        <button
          type="button"
          onClick={onTerminar}
          className="inline-flex items-center gap-2 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          <X size={16} aria-hidden />
          Cancelar
        </button>
      </div>
    </form>
  )
}
