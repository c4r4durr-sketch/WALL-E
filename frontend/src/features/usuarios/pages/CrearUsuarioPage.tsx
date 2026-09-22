import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Rol } from '../../../shared/types/roles'
import { useSucursales } from '../hooks/useSucursales'
import { useCrearUsuario } from '../hooks/useCrearUsuario'

const ROL_LABEL: Record<Rol, string> = {
  ADMINISTRADOR: 'Administrador',
  SUPERVISOR: 'Supervisor',
  EMPLEADO: 'Empleado',
}

// HU4/HU5: el Administrador crea una cuenta asignando rol y, si no es
// Administrador, sucursal obligatoria. El formulario solo guía al usuario:
// la regla real la valida el backend (usuarios/domain/reglas.py, aplicada
// en UsuarioSerializer.validate), que responde 400 si falta la sucursal.
// Flujo mínimo demostrable: falta validación fina y feedback de carga más
// pulido.
export function CrearUsuarioPage() {
  const navigate = useNavigate()
  const { data: sucursales } = useSucursales()
  const { mutate, isPending, error, isSuccess } = useCrearUsuario()

  const [form, setForm] = useState({
    username: '',
    password: '',
    first_name: '',
    last_name: '',
    rol: Rol.EMPLEADO as Rol,
    sucursal: '',
  })

  function handleSubmit(event: FormEvent) {
    event.preventDefault()
    mutate({
      username: form.username,
      password: form.password,
      first_name: form.first_name,
      last_name: form.last_name,
      rol: form.rol,
      sucursal: form.rol === Rol.ADMINISTRADOR ? null : Number(form.sucursal),
    })
  }

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <button
          type="button"
          onClick={() => navigate('/')}
          className="mb-4 text-sm text-slate-500 hover:underline"
        >
          ← Volver
        </button>
        <h1 className="mb-4 text-xl font-semibold text-slate-800">Crear cuenta nueva</h1>
        <form onSubmit={handleSubmit} className="space-y-4" noValidate>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Usuario</label>
            <input
              value={form.username}
              onChange={(event) => setForm({ ...form, username: event.target.value })}
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Contraseña</label>
            <input
              type="password"
              value={form.password}
              onChange={(event) => setForm({ ...form, password: event.target.value })}
              required
              className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
            />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Nombre</label>
              <input
                value={form.first_name}
                onChange={(event) => setForm({ ...form, first_name: event.target.value })}
                required
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-slate-700">Apellido</label>
              <input
                value={form.last_name}
                onChange={(event) => setForm({ ...form, last_name: event.target.value })}
                required
                className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          </div>
          <div>
            <label className="mb-1 block text-sm font-medium text-slate-700">Rol</label>
            <select
              value={form.rol}
              onChange={(event) => setForm({ ...form, rol: event.target.value as Rol })}
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
                onChange={(event) => setForm({ ...form, sucursal: event.target.value })}
                required
                className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm"
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
            </div>
          )}
          {error && (
            <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
              No se pudo crear la cuenta. Revisa los datos.
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
