import { useState, type FormEvent } from 'react'
import { Save } from 'lucide-react'
import { Aviso, Button, Field, Input } from '../../../components/ui'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'
import { useCrearProveedor, useEditarProveedor } from '../hooks/useProveedores'
import type { Proveedor } from '../api/proveedoresApi'

// Alta y edición de un proveedor (HU8), dentro del panel lateral. Con
// `proveedor` funciona en modo edición; sin él, en modo alta. Las mismas
// reglas que el backend se revisan antes de enviar (nombre y teléfono
// obligatorios, formatos), y los mensajes del backend (nombre repetido) se
// muestran junto al campo.

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

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <div className="space-y-4 rounded-card bg-surf p-5 shadow-sh">
        <Field etiqueta="Nombre" error={visibles.nombre}>
          <Input value={form.nombre} onChange={(e) => setCampo('nombre', e.target.value)} autoFocus />
        </Field>
        <Field etiqueta="Teléfono" error={visibles.telefono}>
          <Input type="tel" value={form.telefono} onChange={(e) => setCampo('telefono', e.target.value)} />
        </Field>
        <Field etiqueta="Correo" opcional error={visibles.email}>
          <Input type="email" value={form.email} onChange={(e) => setCampo('email', e.target.value)} />
        </Field>
      </div>

      {errorGeneral && <Aviso tono="error">{errorGeneral}</Aviso>}

      <div className="flex justify-end gap-2 pt-2">
        <Button variante="ghost" onClick={onTerminar}>Cancelar</Button>
        <Button type="submit" variante="primary" cargando={mutacion.isPending} icono={<Save size={16} aria-hidden />}>
          {editando ? 'Guardar cambios' : 'Guardar proveedor'}
        </Button>
      </div>
    </form>
  )
}
