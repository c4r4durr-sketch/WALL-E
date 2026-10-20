import { useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { Rol } from '../../../shared/types/roles'
import { useSucursales } from '../hooks/useSucursales'
import { useCrearUsuario } from '../hooks/useCrearUsuario'
import { ROL_LABEL } from '../roles'
import { erroresPorCampo, mensajeDeError } from '../../../shared/api/errores'

type FormState = {
  username: string
  password: string
  first_name: string
  last_name: string
  rol: Rol
  sucursal: string
}

type Errores = Partial<Record<keyof FormState, string>>

// Declarado fuera del componente: si se crea dentro del render, React lo
// trata como un componente nuevo en cada render (oxlint static-components).
function MensajeError({ mensaje }: { mensaje?: string }) {
  return mensaje ? <p className="mt-1 text-xs text-red-600">{mensaje}</p> : null
}

function validar(form: FormState): Errores {
  const errores: Errores = {}

  if (!form.username.trim()) {
    errores.username = 'El usuario es obligatorio.'
  } else if (form.username.trim().length < 3) {
    errores.username = 'Debe tener al menos 3 caracteres.'
  } else if (/\s/.test(form.username)) {
    errores.username = 'No puede contener espacios.'
  }

  if (!form.password) {
    errores.password = 'La contraseña es obligatoria.'
  } else if (form.password.length < 8) {
    errores.password = 'Debe tener al menos 8 caracteres.'
  }

  if (!form.first_name.trim()) errores.first_name = 'El nombre es obligatorio.'
  if (!form.last_name.trim()) errores.last_name = 'El apellido es obligatorio.'

  if (form.rol !== Rol.ADMINISTRADOR && !form.sucursal) {
    errores.sucursal = 'Selecciona una sucursal.'
  }

  return errores
}

export function CrearUsuarioPage() {
  const { data: sucursales } = useSucursales()
  const { mutate, isPending, error, isSuccess, reset } = useCrearUsuario()

  const [form, setForm] = useState<FormState>({
    username: '',
    password: '',
    first_name: '',
    last_name: '',
    rol: Rol.EMPLEADO,
    sucursal: '',
  })
  const [errores, setErrores] = useState<Errores>({})
  // Errores del backend (usuario repetido, contraseña débil...) junto a su
  // campo; los del formulario tienen prioridad mientras se corrigen.
  const erroresServidor = erroresPorCampo(error) as Errores
  const visibles: Errores = { ...erroresServidor, ...errores }
  const errorGeneral =
    error && Object.keys(erroresServidor).length === 0
      ? mensajeDeError(error, 'No se pudo crear la cuenta. Intenta de nuevo.')
      : null

  // Actualiza un campo y limpia su error mientras el usuario escribe
  function setCampo<K extends keyof FormState>(campo: K, valor: FormState[K]) {
    setForm((prev) => ({ ...prev, [campo]: valor }))
    if (isSuccess) reset()
    if (errores[campo]) {
      setErrores((prev) => ({ ...prev, [campo]: undefined }))
    }
  }

  function handleSubmit(event: FormEvent) {
    event.preventDefault()

    const erroresNuevos = validar(form)
    setErrores(erroresNuevos)
    if (Object.keys(erroresNuevos).length > 0) return // no envía

    mutate({
      username: form.username.trim(),
      password: form.password,
      first_name: form.first_name.trim(),
      last_name: form.last_name.trim(),
      rol: form.rol,
      sucursal: form.rol === Rol.ADMINISTRADOR ? null : Number(form.sucursal),
    }, {
      onSuccess: () => setForm((prev) => ({ ...prev, username: '', password: '', first_name: '', last_name: '' })),
    })
  }

  const inputClass = (campo: keyof FormState) =>
    `w-full rounded-md border px-3 py-2 text-sm ${
      visibles[campo] ? 'border-red-500' : 'border-slate-300'
    }`

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <Link to="/usuarios" className="mb-4 inline-flex items-center gap-1 text-sm text-slate-500 hover:underline">
          <ArrowLeft size={14} aria-hidden />
          Volver a cuentas
        </Link>
        <h1 className="mb-4 text-xl font-semibold text-slate-800">Crear cuenta nueva</h1>

        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Usuario</label>
            <input
              value={form.username}
              onChange={(e) => setCampo('username', e.target.value)}
              className={inputClass('username')}
            />
            <MensajeError mensaje={visibles.username} />
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Contraseña</label>
            <input
              type="password"
              value={form.password}
              onChange={(e) => setCampo('password', e.target.value)}
              className={inputClass('password')}
            />
            <MensajeError mensaje={visibles.password} />
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Nombre</label>
              <input
                value={form.first_name}
                onChange={(e) => setCampo('first_name', e.target.value)}
                className={inputClass('first_name')}
              />
              <MensajeError mensaje={visibles.first_name} />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Apellido</label>
              <input
                value={form.last_name}
                onChange={(e) => setCampo('last_name', e.target.value)}
                className={inputClass('last_name')}
              />
              <MensajeError mensaje={visibles.last_name} />
            </div>
          </div>

          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Rol</label>
            <select
              value={form.rol}
              onChange={(e) => {
                const rol = e.target.value as Rol
                setForm((prev) => ({
                  ...prev,
                  rol,
                  // al pasar a Administrador, la sucursal ya no aplica
                  sucursal: rol === Rol.ADMINISTRADOR ? '' : prev.sucursal,
                }))
                setErrores((prev) => ({ ...prev, sucursal: undefined }))
              }}
              className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
            >
              {Object.values(Rol).map((rol) => (
                <option key={rol} value={rol}>
                  {ROL_LABEL[rol]}
                </option>
              ))}
            </select>
          </div>

          {form.rol !== Rol.ADMINISTRADOR && (
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Sucursal</label>
              <select
                value={form.sucursal}
                onChange={(e) => setCampo('sucursal', e.target.value)}
                className={`${inputClass('sucursal')} bg-white`}
              >
                <option value="" disabled>
                  Selecciona una sucursal
                </option>
                {sucursales?.map((sucursal) => (
                  <option key={sucursal.id} value={sucursal.id}>
                    {sucursal.nombre}
                  </option>
                ))}
              </select>
              <MensajeError mensaje={visibles.sucursal} />
            </div>
          )}

          {errorGeneral && (
            <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              {errorGeneral}
            </p>
          )}
          {isSuccess && (
            <p className="rounded-md bg-green-50 px-3 py-2 text-sm text-green-700">
              Cuenta creada correctamente.
            </p>
          )}

          <button
            type="submit"
            disabled={isPending}
            className="w-full rounded-md bg-slate-800 px-3 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-50"
          >
            {isPending ? 'Creando...' : 'Crear cuenta'}
          </button>
        </form>
      </div>
    </div>
  )
}