import { createBrowserRouter } from 'react-router-dom'
import { LoginPage } from '../features/auth/pages/LoginPage'
import { ProtectedRoute } from '../features/auth/components/ProtectedRoute'
import { RequireRol } from '../features/auth/components/RequireRol'
import { CatalogoPage } from '../features/catalogo/pages/CatalogoPage'
import { MovimientosPage } from '../features/movimientos/pages/MovimientosPage'
import { TransferenciasPage } from '../features/transferencias/pages/TransferenciasPage'
import { DashboardPage } from '../features/dashboard/pages/DashboardPage'
import { CrearUsuarioPage } from '../features/usuarios/pages/CrearUsuarioPage'
import { Rol } from '../shared/types/roles'

// Enrutamiento centralizado: cada feature expone su(s) página(s) en
// features/<feature>/pages y acá solo se mapean a rutas. Así ninguna
// feature depende de otra para saber por dónde se navega.
//
// Todas las rutas salvo /login viven bajo ProtectedRoute (exige sesión
// JWT válida); /usuarios/nuevo además exige rol ADMINISTRADOR vía
// RequireRol.
export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      { path: '/', element: <DashboardPage /> },
      { path: '/catalogo', element: <CatalogoPage /> },
      { path: '/movimientos', element: <MovimientosPage /> },
      { path: '/transferencias', element: <TransferenciasPage /> },
      {
        element: <RequireRol roles={[Rol.ADMINISTRADOR]} />,
        children: [{ path: '/usuarios/nuevo', element: <CrearUsuarioPage /> }],
      },
    ],
  },
])
