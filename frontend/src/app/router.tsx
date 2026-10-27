import { createBrowserRouter } from 'react-router-dom'
import { LoginPage } from '../features/auth/pages/LoginPage'
import { ProtectedRoute } from '../features/auth/components/ProtectedRoute'
import { RequireRol } from '../features/auth/components/RequireRol'
import { CatalogoPage } from '../features/catalogo/pages/CatalogoPage'
import { MovimientosPage } from '../features/movimientos/pages/MovimientosPage'
import { TransferenciasPage } from '../features/transferencias/pages/TransferenciasPage'
import { DashboardPage } from '../features/dashboard/pages/DashboardPage'
import { IndicadoresPage } from '../features/dashboard/pages/IndicadoresPage'
import { ReposicionPage } from '../features/dashboard/pages/ReposicionPage'
import { ClasificacionABCPage } from '../features/dashboard/pages/ClasificacionABCPage'
import { CrearUsuarioPage } from '../features/usuarios/pages/CrearUsuarioPage'
import { UsuariosPage } from '../features/usuarios/pages/UsuariosPage'
import { ProveedoresPage } from '../features/proveedores/pages/ProveedoresPage'
import { CierreDiarioPage } from '../features/reportes/pages/CierreDiarioPage'
import { AntiguedadPage } from '../features/reportes/pages/AntiguedadPage'
import { HistorialPage } from '../features/auditoria/pages/HistorialPage'
import { Rol } from '../shared/types/roles'
import { AppLayout } from './layout/AppLayout'

// Enrutamiento centralizado: cada feature expone su(s) página(s) en
// features/<feature>/pages y acá solo se mapean a rutas. Así ninguna
// feature depende de otra para saber por dónde se navega.
//
// Todas las rutas salvo /login viven bajo ProtectedRoute (exige sesión
// JWT válida) y dentro de AppLayout (barra lateral); /usuarios y
// /usuarios/nuevo además exigen rol ADMINISTRADOR, y /cierre-diario,
// /antiguedad e /historial ADMINISTRADOR o SUPERVISOR, vía RequireRol (el backend aplica
// la misma regla). La barra lateral (layout/navegacion.ts) oculta lo que
// cada rol no puede abrir.
export const router = createBrowserRouter([
  { path: '/login', element: <LoginPage /> },
  {
    element: <ProtectedRoute />,
    children: [
      {
        element: <AppLayout />,
        children: [
          { path: '/', element: <DashboardPage /> },
          { path: '/catalogo', element: <CatalogoPage /> },
          { path: '/proveedores', element: <ProveedoresPage /> },
          { path: '/movimientos', element: <MovimientosPage /> },
          { path: '/transferencias', element: <TransferenciasPage /> },
          { path: '/indicadores', element: <IndicadoresPage /> },
          { path: '/reposicion', element: <ReposicionPage /> },
          { path: '/abc', element: <ClasificacionABCPage /> },
          {
            element: <RequireRol roles={[Rol.ADMINISTRADOR, Rol.SUPERVISOR]} />,
            children: [
              { path: '/cierre-diario', element: <CierreDiarioPage /> },
              { path: '/antiguedad', element: <AntiguedadPage /> },
              { path: '/historial', element: <HistorialPage /> },
            ],
          },
          {
            element: <RequireRol roles={[Rol.ADMINISTRADOR]} />,
            children: [
              { path: '/usuarios', element: <UsuariosPage /> },
              { path: '/usuarios/nuevo', element: <CrearUsuarioPage /> },
            ],
          },
        ],
      },
    ],
  },
])
