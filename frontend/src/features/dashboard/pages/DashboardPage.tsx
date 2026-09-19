import { Link } from 'react-router-dom'
import { getSession } from '../../auth/session'
import { useLogout } from '../../auth/hooks/useLogout'
import { Rol } from '../../../shared/types/roles'

const ROL_LABEL: Record<Rol, string> = {
  ADMINISTRADOR: 'Administrador',
  SUPERVISOR: 'Supervisor',
  EMPLEADO: 'Empleado',
}

// Contenido temporal de "/": confirma visualmente que el login JWT
// funciona de punta a punta (checkpoint de hoy). El consolidado real de
// indicadores (EOQ/ROP/ABC) reemplaza este contenido más adelante.
export function DashboardPage() {
  const session = getSession()
  const logout = useLogout()

  if (!session) return null

  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 p-6">
      <div className="w-full max-w-md rounded-lg border border-slate-200 bg-white p-6 shadow-sm">
        <h1 className="text-xl font-semibold text-slate-800">
          Bienvenido, {session.first_name} {session.last_name}
        </h1>
        <p className="mt-2 text-sm text-slate-500">
          Rol: <span className="font-medium text-slate-700">{ROL_LABEL[session.rol]}</span>
          {session.sucursal_nombre && (
            <>
              {' · '}Sucursal: <span className="font-medium text-slate-700">{session.sucursal_nombre}</span>
            </>
          )}
        </p>
        {session.rol === Rol.ADMINISTRADOR && (
          <Link
            to="/usuarios/nuevo"
            className="mt-4 inline-block text-sm font-medium text-blue-600 hover:underline"
          >
            Crear nueva cuenta →
          </Link>
        )}
        <button
          onClick={logout}
          className="mt-6 w-full rounded-md border border-slate-300 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
        >
          Cerrar sesión
        </button>
      </div>
    </div>
  )
}
