import type { FormEvent } from 'react'
import { Save } from 'lucide-react'
import { Aviso, Button, Field, Input, Select } from '../../../components/ui'
import { Rol } from '../../../shared/types/roles'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'
import { reglas, useFormulario, type Errores } from '../../../shared/validacion'
import { useSucursales } from '../hooks/useSucursales'
import { useEditarUsuario } from '../hooks/useUsuarios'
import { ROL_LABEL } from '../roles'
import type { Usuario } from '../api/usuariosApi'

// Edición de una cuenta (HU4/HU5), dentro del panel lateral: nombres,
// correo, rol y sucursal. El nombre de usuario y la contraseña no se
// editan acá (la contraseña tiene su propio formulario, HU3). Los formatos
// (shared/validacion) se revisan al instante; el backend los vuelve a
// revisar junto con las reglas que solo él conoce (sucursal activa, no
// quitarse el rol a uno mismo).

interface FormState {
  first_name: string
  last_name: string
  email: string
  rol: Rol
  sucursal: string
}

function validar(form: FormState): Errores<FormState> {
  return {
    first_name: reglas.nombrePersona(form.first_name),
    last_name: reglas.nombrePersona(form.last_name, 'El apellido'),
    email: reglas.email(form.email),
    sucursal: form.rol !== Rol.ADMINISTRADOR && !form.sucursal ? 'Selecciona una sucursal.' : null,
  }
}

interface Props {
  usuario: Usuario
  onTerminar: () => void
}

export function EditarUsuarioForm({ usuario, onTerminar }: Props) {
  const { data: sucursales } = useSucursales()
  const editar = useEditarUsuario()
  const formulario = useFormulario<FormState>(
    {
      first_name: usuario.first_name,
      last_name: usuario.last_name,
      email: usuario.email,
      rol: usuario.rol,
      sucursal: usuario.sucursal === null ? '' : String(usuario.sucursal),
    },
    validar,
  )
  const form = formulario.valores
  const erroresServidor = erroresPorCampo(editar.error)
  const errorDe = (campo: keyof FormState) => formulario.error(campo, erroresServidor)
  const errorGeneral =
    editar.isError && Object.keys(erroresServidor).length === 0
      ? mensajeDeError(editar.error, 'No se pudo guardar la cuenta. Intenta de nuevo.')
      : null

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!formulario.enviar()) return
    editar.mutate(
      {
        id: usuario.id,
        first_name: reglas.limpiar(form.first_name),
        last_name: reglas.limpiar(form.last_name),
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
          <Field etiqueta="Nombre" obligatorio error={errorDe('first_name')}>
            <Input
              maxLength={50}
              value={form.first_name}
              onChange={(e) => formulario.cambiar('first_name', e.target.value)}
              onBlur={() => formulario.tocar('first_name')}
            />
          </Field>
          <Field etiqueta="Apellido" obligatorio error={errorDe('last_name')}>
            <Input
              maxLength={50}
              value={form.last_name}
              onChange={(e) => formulario.cambiar('last_name', e.target.value)}
              onBlur={() => formulario.tocar('last_name')}
            />
          </Field>
        </div>
        <Field etiqueta="Correo" opcional error={errorDe('email')}>
          <Input
            type="email"
            maxLength={254}
            value={form.email}
            onChange={(e) => formulario.cambiar('email', e.target.value)}
            onBlur={() => formulario.tocar('email')}
          />
        </Field>
        <Field etiqueta="Rol" obligatorio>
          <Select
            value={form.rol}
            onChange={(e) => {
              const rol = e.target.value as Rol
              formulario.setValores((prev) => ({ ...prev, rol, sucursal: rol === Rol.ADMINISTRADOR ? '' : prev.sucursal }))
            }}
          >
            {Object.values(Rol).map((rol) => (
              <option key={rol} value={rol}>{ROL_LABEL[rol]}</option>
            ))}
          </Select>
        </Field>
        {form.rol !== Rol.ADMINISTRADOR && (
          <Field etiqueta="Sucursal" obligatorio error={errorDe('sucursal')}>
            <Select
              value={form.sucursal}
              onChange={(e) => formulario.cambiar('sucursal', e.target.value)}
              onBlur={() => formulario.tocar('sucursal')}
            >
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
        <Button
          type="submit"
          variante="primary"
          cargando={editar.isPending}
          disabled={!formulario.valido}
          icono={<Save size={16} aria-hidden />}
        >
          Guardar cambios
        </Button>
      </div>
    </form>
  )
}
