import { Navigate, Outlet } from 'react-router-dom'
import { getSession } from '../../features/auth/session'
import { Sidebar } from './Sidebar'

// Marco de todas las pantallas con sesión: barra lateral flotante a la
// izquierda y el contenido a la derecha, con 14 px de margen al borde.
export function AppLayout() {
  const sesion = getSession()
  if (!sesion) return <Navigate to="/login" replace />

  return (
    <>
      <a
        href="#contenido"
        className="sr-only z-50 rounded-full bg-surf px-4 py-2 text-sm font-semibold text-ink shadow-sh focus:not-sr-only focus:fixed focus:left-4 focus:top-4"
      >
        Saltar al contenido
      </a>
      <Sidebar sesion={sesion} />
      <main id="contenido" className="ml-[292px] min-h-screen px-3.5 py-3.5">
        <div className="mx-auto max-w-[1280px] space-y-6 px-6 py-6">
          <Outlet />
        </div>
      </main>
    </>
  )
}
