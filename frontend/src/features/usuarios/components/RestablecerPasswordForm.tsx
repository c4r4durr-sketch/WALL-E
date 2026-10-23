import { useState, type FormEvent } from 'react'
import { KeyRound } from 'lucide-react'
import { Aviso, Button, Field, Input } from '../../../components/ui'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'
import { useRestablecerPassword } from '../hooks/useUsuarios'
import type { Usuario } from '../api/usuariosApi'

// HU3: el Administrador asigna una contraseña nueva a una cuenta (por
// ejemplo, cuando el empleado la olvidó). Se pide dos veces para evitar
// errores de tipeo; la política completa (largo, comunes, parecida al
// usuario) la valida el backend y sus mensajes se muestran acá.

const LARGO_MINIMO = 8

interface Props {
  usuario: Usuario
  onTerminar: () => void
}

export function RestablecerPasswordForm({ usuario, onTerminar }: Props) {
  const restablecer = useRestablecerPassword()
  const [password, setPassword] = useState('')
  const [confirmacion, setConfirmacion] = useState('')
  const [error, setError] = useState<string | null>(null)

  const errorServidor =
    erroresPorCampo(restablecer.error).password ??
    (restablecer.isError ? mensajeDeError(restablecer.error, 'No se pudo restablecer la contraseña.') : null)

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    if (password.length < LARGO_MINIMO) {
      setError(`Debe tener al menos ${LARGO_MINIMO} caracteres.`)
      return
    }
    if (password !== confirmacion) {
      setError('Las contraseñas no coinciden.')
      return
    }
    setError(null)
    restablecer.mutate(
      { id: usuario.id, password },
      {
        onSuccess: () => {
          setPassword('')
          setConfirmacion('')
        },
      },
    )
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

  const mensaje = error ?? errorServidor

  return (
    <form onSubmit={handleSubmit} noValidate className="space-y-4">
      <div className="space-y-4 rounded-card bg-surf p-5 shadow-sh">
        <Field etiqueta="Contraseña nueva" ayuda={`Mínimo ${LARGO_MINIMO} caracteres; no solo números ni parecida al usuario.`}>
          <Input type="password" autoComplete="new-password" value={password} onChange={(e) => setPassword(e.target.value)} autoFocus />
        </Field>
        <Field etiqueta="Repetir contraseña">
          <Input type="password" autoComplete="new-password" value={confirmacion} onChange={(e) => setConfirmacion(e.target.value)} />
        </Field>
      </div>

      {mensaje && <Aviso tono="error">{mensaje}</Aviso>}

      <div className="flex justify-end gap-2 pt-2">
        <Button variante="ghost" onClick={onTerminar}>Cancelar</Button>
        <Button type="submit" variante="primary" cargando={restablecer.isPending} icono={<KeyRound size={16} aria-hidden />}>
          Restablecer contraseña
        </Button>
      </div>
    </form>
  )
}
