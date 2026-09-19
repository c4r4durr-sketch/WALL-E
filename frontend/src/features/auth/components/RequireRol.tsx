import { Navigate, Outlet } from 'react-router-dom'
import { getSession } from '../session'
import type { Rol } from '../../../shared/types/roles'

// Igual que ProtectedRoute pero además exige que el rol de la sesión esté
// en la lista permitida (ej. crear cuentas es solo para ADMINISTRADOR).
export function RequireRol({ roles }: { roles: Rol[] }) {
  const session = getSession()
  if (!session) {
    return <Navigate to="/login" replace />
  }
  if (!roles.includes(session.rol)) {
    return <Navigate to="/" replace />
  }
  return <Outlet />
}
