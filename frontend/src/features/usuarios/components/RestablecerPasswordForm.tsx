import type { FormEvent } from 'react'
import { KeyRound } from 'lucide-react'
import { Aviso, Button, Field, PasswordInput, PasswordStrength } from '../../../components/ui'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'
import { errorPassword, errorRepetir, useFormulario, type DatosCuenta, type Errores } from '../../../shared/validacion'
import { useRestablecerPassword } from '../hooks/useUsuarios'
import type { Usuario } from '../api/usuariosApi'

// HU3: el Administrador asigna una contraseña nueva a una cuenta (por
// ejemplo, cuando el empleado la olvidó). Se pide dos veces para evitar
// errores de tipeo. La barra de seguridad muestra la misma política que
// valida el backend; si además es una contraseña común, el aviso llega
// del backend debajo del campo.

interface FormState {
  password: string
  repetir: string
}

interface Props {
  usuario: Usuario
  onTerminar: () => void
}

export function RestablecerPasswordForm({ usuario, onTerminar }: Props) {
  const restablecer = useRestablecerPassword()
  const cuenta: DatosCuenta = {
    username: usuario.username,
    first_name: usuario.first_name,
    last_name: usuario.last_name,
    email: usuario.email,
  }
  const form = useFormulario<FormState>(
    { password: '', repetir: '' },
    (v): Errores<FormState> => ({
      password: errorPassword(v.password, cuenta),
      repetir: errorRepetir(v.password, v.repetir),
    }),
  )
  const erroresServidor = erroresPorCampo(restablecer.error)
  const errorGeneral =
    restablecer.isError && Object.keys(erroresServidor).length === 0
      ? mensajeDeError(restablecer.error, 'No se pudo restablecer la contraseña.')
      : null

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (!form.enviar()) return
    restablecer.mutate({ id: usuario.id, password: form.valores.password }, { onSuccess: () => form.reiniciar() })
  }

  if (restablecer.isSuccess) {
    return (
      <div className="space-y-4">
        <Aviso tono="exito">
          Contraseña de {usuario.username} restablecida. La anterior ya no sirve; comunícale la nueva en persona.
        </Aviso>
        <div className="flex justify-end">
          <Button onClick={onTerminar}>Cerrar</Button>
        </div>
      </div>
    )
  }

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <div className="space-y-4 rounded-card bg-surf p-5 shadow-sh">
        <Field etiqueta="Contraseña nueva" obligatorio error={form.error('password', erroresServidor)}>
          <PasswordInput
            autoComplete="new-password"
            value={form.valores.password}
            onChange={(e) => form.cambiar('password', e.target.value)}
            onBlur={() => form.tocar('password')}
            autoFocus
          />
        </Field>
        <PasswordStrength password={form.valores.password} cuenta={cuenta} />
        <Field etiqueta="Repetir contraseña" obligatorio error={form.error('repetir')}>
          <PasswordInput
            autoComplete="new-password"
            value={form.valores.repetir}
            onChange={(e) => form.cambiar('repetir', e.target.value)}
            onBlur={() => form.tocar('repetir')}
          />
        </Field>
      </div>

      {errorGeneral && <Aviso tono="error">{errorGeneral}</Aviso>}

      <div className="flex justify-end gap-2 pt-2">
        <Button variante="ghost" onClick={onTerminar}>Cancelar</Button>
        <Button
          type="submit"
          variante="primary"
          cargando={restablecer.isPending}
          disabled={!form.valido}
          icono={<KeyRound size={16} aria-hidden />}
        >
          Restablecer contraseña
        </Button>
      </div>
    </form>
  )
}
