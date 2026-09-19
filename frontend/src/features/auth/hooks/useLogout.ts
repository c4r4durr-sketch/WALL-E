import { useNavigate } from 'react-router-dom'
import { clearSession } from '../session'

// No hay endpoint de logout en el backend (JWT es stateless): "cerrar
// sesión" es solo borrar los tokens guardados y volver a /login.
export function useLogout() {
  const navigate = useNavigate()
  return () => {
    clearSession()
    navigate('/login', { replace: true })
  }
}
