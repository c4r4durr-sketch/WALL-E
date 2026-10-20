import { useState, type FormEvent } from 'react'
import { Save, X } from 'lucide-react'
import { Rol } from '../../../shared/types/roles'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'
import { useSucursales } from '../hooks/useSucursales'
import { useEditarUsuario } from '../hooks/useUsuarios'
import { ROL_LABEL } from '../roles'
import type { Usuario } from '../api/usuariosApi'

// Edición de una cuenta (HU4/HU5): nombres, correo, rol y sucursal. El
// nombre de usuario y la contraseña no se editan acá (la contraseña tiene
// su propio formulario, HU3). La validación real (sucursal activa
// obligatoria, no quitarse el rol a uno mismo) la hace el backend.

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

function MensajeError({ mensaje }: { mensaje?: string }) {
  return mensaje ? <p className="mt-1 text-xs text-red-600">{mensaje}</p> : null
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

  const inputClass = (campo: keyof FormState) =>
    `w-full rounded-md border px-3 py-2 text-sm ${errorDe(campo) ? 'border-red-500' : 'border-slate-300'}`

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className="space-y-4 rounded-lg border border-blue-300 bg-white p-6 shadow-sm"
    >
      <h2 className="text-lg font-semibold text-slate-800">Editar cuenta {usuario.username}</h2>

      <div className="grid grid-cols-3 gap-4">
        <div>
          <label htmlFor="first_name" className="mb-1 block text-sm font-medium text-slate-700">Nombre</label>
          <input
            id="first_name"
            value={form.first_name}
            onChange={(e) => setCampo('first_name', e.target.value)}
            className={inputClass('first_name')}
          />
          <MensajeError mensaje={errorDe('first_name')} />
        </div>
        <div>
          <label htmlFor="last_name" className="mb-1 block text-sm font-medium text-slate-700">Apellido</label>
          <input
            id="last_name"
            value={form.last_name}
            onChange={(e) => setCampo('last_name', e.target.value)}
            className={inputClass('last_name')}
          />
          <MensajeError mensaje={errorDe('last_name')} />
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
          <MensajeError mensaje={errorDe('email')} />
        </div>
        <div>
          <label htmlFor="rol" className="mb-1 block text-sm font-medium text-slate-700">Rol</label>
          <select
            id="rol"
            value={form.rol}
            onChange={(e) => {
              const rol = e.target.value as Rol
              setForm((prev) => ({ ...prev, rol, sucursal: rol === Rol.ADMINISTRADOR ? '' : prev.sucursal }))
              setErrores((prev) => ({ ...prev, sucursal: undefined }))
            }}
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
          >
            {Object.values(Rol).map((rol) => (
              <option key={rol} value={rol}>{ROL_LABEL[rol]}</option>
            ))}
          </select>
        </div>
        {form.rol !== Rol.ADMINISTRADOR && (
          <div>
            <label htmlFor="sucursal" className="mb-1 block text-sm font-medium text-slate-700">Sucursal</label>
            <select
              id="sucursal"
              value={form.sucursal}
              onChange={(e) => setCampo('sucursal', e.target.value)}
              className={`${inputClass('sucursal')} bg-white`}
            >
              <option value="" disabled>Selecciona una sucursal</option>
              {sucursales?.map((s) => (
                <option key={s.id} value={s.id}>{s.nombre}</option>
              ))}
            </select>
            <MensajeError mensaje={errorDe('sucursal')} />
          </div>
        )}
      </div>

      {errorGeneral && (
        <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">{errorGeneral}</p>
      )}

      <div className="flex gap-2">
        <button
          type="submit"
          disabled={editar.isPending}
          className="inline-flex items-center gap-2 rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
        >
          <Save size={16} aria-hidden />
          {editar.isPending ? 'Guardando...' : 'Guardar cambios'}
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
