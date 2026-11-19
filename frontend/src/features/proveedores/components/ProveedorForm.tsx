import type { FormEvent } from 'react'
import { Save } from 'lucide-react'
import { Aviso, Button, Field, Input } from '../../../components/ui'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'
import { reglas, useFormulario, type Errores } from '../../../shared/validacion'
import { useCrearProveedor, useEditarProveedor } from '../hooks/useProveedores'
import type { Proveedor } from '../api/proveedoresApi'

// Alta y edición de un proveedor (HU8), dentro del panel lateral. Con
// `proveedor` funciona en modo edición; sin él, en modo alta. Las mismas
// reglas que el backend (shared/validacion) se revisan al instante, y los
// mensajes del backend (nombre repetido) se muestran junto al campo. El
// nombre es el de una empresa: admite números y símbolos.

interface FormState {
  nombre: string
  telefono: string
  email: string
}

const FORM_VACIO: FormState = { nombre: '', telefono: '', email: '' }

// `telefonoOriginal`: en la edición, un teléfono cargado antes de la regla
// actual se puede conservar (el backend tampoco lo revisa si no cambia).
function validador(telefonoOriginal: string | null) {
  return (form: FormState): Errores<FormState> => ({
    nombre: reglas.texto(form.nombre, { etiqueta: 'El nombre', requerido: true, min: 2, max: 150 }),
    telefono: form.telefono === telefonoOriginal ? null : reglas.telefono(form.telefono),
    email: reglas.email(form.email),
  })
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
  const form = useFormulario<FormState>(
    proveedor ? { nombre: proveedor.nombre, telefono: proveedor.telefono, email: proveedor.email } : FORM_VACIO,
    validador(proveedor?.telefono ?? null),
  )
  const erroresServidor = erroresPorCampo(mutacion.error)
  const errorGeneral =
    mutacion.isError && Object.keys(erroresServidor).length === 0
      ? mensajeDeError(mutacion.error, 'No se pudo guardar el proveedor. Intenta de nuevo.')
      : null

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!form.enviar()) return
    const v = form.valores
    const payload = { nombre: reglas.limpiar(v.nombre), telefono: v.telefono.trim(), email: v.email.trim() }
    if (proveedor) {
      editar.mutate({ id: proveedor.id, ...payload }, { onSuccess: onTerminar })
    } else {
      crear.mutate(payload, { onSuccess: onTerminar })
    }
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <div className="space-y-4 rounded-card bg-surf p-5 shadow-sh">
        <Field etiqueta="Nombre" obligatorio error={form.error('nombre', erroresServidor)}>
          <Input
            maxLength={150}
            value={form.valores.nombre}
            onChange={(e) => form.cambiar('nombre', e.target.value)}
            onBlur={() => form.tocar('nombre')}
            autoFocus
          />
        </Field>
        <Field
          etiqueta="Teléfono"
          obligatorio
          ayuda="De 7 a 15 dígitos. Ej.: +591 2 2456789"
          error={form.error('telefono', erroresServidor)}
        >
          <Input
            type="tel"
            inputMode="tel"
            maxLength={30}
            value={form.valores.telefono}
            onChange={(e) => form.cambiar('telefono', e.target.value)}
            onBlur={() => form.tocar('telefono')}
          />
        </Field>
        <Field etiqueta="Correo" opcional error={form.error('email', erroresServidor)}>
          <Input
            type="email"
            maxLength={254}
            value={form.valores.email}
            onChange={(e) => form.cambiar('email', e.target.value)}
            onBlur={() => form.tocar('email')}
          />
        </Field>
      </div>

      {errorGeneral && <Aviso tono="error">{errorGeneral}</Aviso>}

      <div className="flex justify-end gap-2 pt-2">
        <Button variante="ghost" onClick={onTerminar}>Cancelar</Button>
        <Button
          type="submit"
          variante="primary"
          cargando={mutacion.isPending}
          disabled={!form.valido}
          icono={<Save size={16} aria-hidden />}
        >
          {editando ? 'Guardar cambios' : 'Guardar proveedor'}
        </Button>
      </div>
    </form>
  )
}
