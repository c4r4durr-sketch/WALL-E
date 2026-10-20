import { useState, type FormEvent } from 'react'
import { CheckCircle2, KeyRound, X } from 'lucide-react'
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
      <div className="flex items-center justify-between rounded-lg border border-green-200 bg-green-50 p-4 text-sm text-green-800">
        <span className="inline-flex items-center gap-2">
          <CheckCircle2 size={18} aria-hidden />
          Contraseña de {usuario.username} restablecida. La anterior ya no sirve; comunícale la nueva en persona.
        </span>
        <button type="button" onClick={onTerminar} className="font-medium hover:underline">
          Cerrar
        </button>
      </div>
    )
  }

  const mensaje = error ?? errorServidor

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="space-y-4 rounded-lg border border-amber-300 bg-white p-6 shadow-sm"
    >
      <h2 className="text-lg font-semibold text-slate-800">Restablecer contraseña de {usuario.username}</h2>
      <div className="grid grid-cols-2 gap-4">
        <div>
          <label htmlFor="password" className="mb-1 block text-sm font-medium text-slate-700">Contraseña nueva</label>
          <input
            id="password"
            type="password"
            autoComplete="new-password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
          <p className="mt-1 text-xs text-slate-500">
            Mínimo {LARGO_MINIMO} caracteres; no solo números ni parecida al usuario.
          </p>
        </div>
        <div>
          <label htmlFor="confirmacion" className="mb-1 block text-sm font-medium text-slate-700">Repetir contraseña</label>
          <input
            id="confirmacion"
            type="password"
            autoComplete="new-password"
            value={confirmacion}
            onChange={(e) => setConfirmacion(e.target.value)}
            className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
          />
        </div>
      </div>

      {mensaje && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{mensaje}</p>
      )}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={restablecer.isPending}
          className="inline-flex items-center gap-2 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          <KeyRound size={16} aria-hidden />
          {restablecer.isPending ? 'Guardando...' : 'Restablecer contraseña'}
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
