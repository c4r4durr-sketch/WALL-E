import { Navigate, Outlet } from 'react-router-dom'
import { getSession } from '../session'

// Layout route: envuelve todas las rutas privadas. Si no hay sesión válida
// (o expiró), redirige a /login en vez de dejar pasar la navegación.
export function ProtectedRoute() {
  const session = getSession()
  if (!session) {
    return <Navigate to="/login" replace />
  }
  return <Outlet />
}
