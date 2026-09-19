import { createBrowserRouter } from 'react-router-dom'
import { LoginPage } from '../features/auth/pages/LoginPage'
import { CatalogoPage } from '../features/catalogo/pages/CatalogoPage'
import { MovimientosPage } from '../features/movimientos/pages/MovimientosPage'
import { TransferenciasPage } from '../features/transferencias/pages/TransferenciasPage'
import { DashboardPage } from '../features/dashboard/pages/DashboardPage'

// Enrutamiento centralizado: cada feature expone su(s) página(s) en
// features/<feature>/pages y acá solo se mapean a rutas. Así ninguna
// feature depende de otra para saber por dónde se navega.
//
// Pendiente (junto con la feature auth): proteger las rutas privadas según
// sesión y rol (Administrador/Supervisor/Empleado).
export const router = createBrowserRouter([
  { path: '/', element: <DashboardPage /> },
  { path: '/login', element: <LoginPage /> },
  { path: '/catalogo', element: <CatalogoPage /> },
  { path: '/movimientos', element: <MovimientosPage /> },
  { path: '/transferencias', element: <TransferenciasPage /> },
])
