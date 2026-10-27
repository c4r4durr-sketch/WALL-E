import { useState, type FormEvent } from 'react'
import { Save } from 'lucide-react'
import { Aviso, Button, Field, Input, Select } from '../../../components/ui'
import { Rol } from '../../../shared/types/roles'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'
import { useSucursales } from '../hooks/useSucursales'
import { useEditarUsuario } from '../hooks/useUsuarios'
import { ROL_LABEL } from '../roles'
import type { Usuario } from '../api/usuariosApi'

// Edición de una cuenta (HU4/HU5), dentro del panel lateral: nombres,
// correo, rol y sucursal. El nombre de usuario y la contraseña no se
// editan acá (la contraseña tiene su propio formulario, HU3). La
// validación real (sucursal activa obligatoria, no quitarse el rol a uno
// mismo) la hace el backend.

interface FormState {
  first_name: string
  last_name: string
  email: string
  rol: Rol
  sucursal: string
}

type Errores = Partial<Record<keyof FormState, string>>

function validar(form: FormState): Errores {
  const errores: Errores = {}
  if (!form.first_name.trim()) errores.first_name = 'El nombre es obligatorio.'
  if (!form.last_name.trim()) errores.last_name = 'El apellido es obligatorio.'
  if (form.email.trim() && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email.trim())) {
    errores.email = 'Correo no válido.'
  }
  if (form.rol !== Rol.ADMINISTRADOR && !form.sucursal) errores.sucursal = 'Selecciona una sucursal.'
  return errores
}

interface Props {
  usuario: Usuario
  onTerminar: () => void
}

export function EditarUsuarioForm({ usuario, onTerminar }: Props) {
  const { data: sucursales } = useSucursales()
  const editar = useEditarUsuario()
  const [form, setForm] = useState<FormState>({
    first_name: usuario.first_name,
    last_name: usuario.last_name,
    email: usuario.email,
    rol: usuario.rol,
    sucursal: usuario.sucursal === null ? '' : String(usuario.sucursal),
  })
  const [errores, setErrores] = useState<Errores>({})
  const erroresServidor = erroresPorCampo(editar.error)
  const errorDe = (campo: keyof FormState) => errores[campo] ?? erroresServidor[campo]
  const errorGeneral =
    editar.isError && Object.keys(erroresServidor).length === 0
      ? mensajeDeError(editar.error, 'No se pudo guardar la cuenta. Intenta de nuevo.')
      : null

  function setCampo<K extends keyof FormState>(campo: K, valor: FormState[K]) {
    setForm((prev) => ({ ...prev, [campo]: valor }))
    if (errores[campo]) setErrores((prev) => ({ ...prev, [campo]: undefined }))
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const nuevos = validar(form)
    setErrores(nuevos)
    if (Object.keys(nuevos).length > 0) return
    editar.mutate(
      {
        id: usuario.id,
        first_name: form.first_name.trim(),
        last_name: form.last_name.trim(),
        email: form.email.trim(),
        rol: form.rol,
        sucursal: form.rol === Rol.ADMINISTRADOR ? null : Number(form.sucursal),
      },
      { onSuccess: onTerminar },
    )
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <div className="space-y-4 rounded-card bg-surf p-5 shadow-sh">
        <div className="grid grid-cols-2 gap-4">
          <Field etiqueta="Nombre" error={errorDe('first_name')}>
            <Input value={form.first_name} onChange={(e) => setCampo('first_name', e.target.value)} />
          </Field>
          <Field etiqueta="Apellido" error={errorDe('last_name')}>
            <Input value={form.last_name} onChange={(e) => setCampo('last_name', e.target.value)} />
          </Field>
        </div>
        <Field etiqueta="Correo" opcional error={errorDe('email')}>
          <Input type="email" value={form.email} onChange={(e) => setCampo('email', e.target.value)} />
        </Field>
        <Field etiqueta="Rol">
          <Select
            value={form.rol}
            onChange={(e) => {
              const rol = e.target.value as Rol
              setForm((prev) => ({ ...prev, rol, sucursal: rol === Rol.ADMINISTRADOR ? '' : prev.sucursal }))
              setErrores((prev) => ({ ...prev, sucursal: undefined }))
            }}
          >
            {Object.values(Rol).map((rol) => (
              <option key={rol} value={rol}>{ROL_LABEL[rol]}</option>
            ))}
          </Select>
        </Field>
        {form.rol !== Rol.ADMINISTRADOR && (
          <Field etiqueta="Sucursal" error={errorDe('sucursal')}>
            <Select value={form.sucursal} onChange={(e) => setCampo('sucursal', e.target.value)}>
              <option value="" disabled>Selecciona una sucursal</option>
              {sucursales?.map((s) => (
                <option key={s.id} value={s.id}>{s.nombre}</option>
              ))}
            </Select>
          </Field>
        )}
      </div>

      {errorGeneral && <Aviso tono="error">{errorGeneral}</Aviso>}

      <div className="flex justify-end gap-2 pt-2">
        <Button variante="ghost" onClick={onTerminar}>Cancelar</Button>
        <Button type="submit" variante="primary" cargando={editar.isPending} icono={<Save size={16} aria-hidden />}>
          Guardar cambios
        </Button>
      </div>
    </form>
  )
}
