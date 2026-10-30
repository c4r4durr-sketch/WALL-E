import { lazy, type ComponentType } from 'react'
import { createBrowserRouter } from 'react-router-dom'
import { LoginPage } from '../features/auth/pages/LoginPage'
import { ProtectedRoute } from '../features/auth/components/ProtectedRoute'
import { RequireRol } from '../features/auth/components/RequireRol'
import { Rol } from '../shared/types/roles'
import { AppLayout } from './layout/AppLayout'

// Cada pantalla se descarga recién cuando se abre su ruta (un archivo JS
// por página): el paquete inicial solo trae el login, la barra lateral y
// las librerías comunes. Mientras llega, AppLayout muestra un skeleton.
// Las páginas se exportan con nombre; React.lazy espera un `default`.
function perezosa<K extends string>(cargar: () => Promise<Record<K, ComponentType>>, nombre: K) {
  return lazy(() => cargar().then((modulo) => ({ default: modulo[nombre] })))
}

const CatalogoPage = perezosa(() => import('../features/catalogo/pages/CatalogoPage'), 'CatalogoPage')
const MovimientosPage = perezosa(() => import('../features/movimientos/pages/MovimientosPage'), 'MovimientosPage')
const TransferenciasPage = perezosa(() => import('../features/transferencias/pages/TransferenciasPage'), 'TransferenciasPage')
const DashboardPage = perezosa(() => import('../features/dashboard/pages/DashboardPage'), 'DashboardPage')
const IndicadoresPage = perezosa(() => import('../features/dashboard/pages/IndicadoresPage'), 'IndicadoresPage')
const ReposicionPage = perezosa(() => import('../features/dashboard/pages/ReposicionPage'), 'ReposicionPage')
const ClasificacionABCPage = perezosa(() => import('../features/dashboard/pages/ClasificacionABCPage'), 'ClasificacionABCPage')
const CrearUsuarioPage = perezosa(() => import('../features/usuarios/pages/CrearUsuarioPage'), 'CrearUsuarioPage')
const UsuariosPage = perezosa(() => import('../features/usuarios/pages/UsuariosPage'), 'UsuariosPage')
const ProveedoresPage = perezosa(() => import('../features/proveedores/pages/ProveedoresPage'), 'ProveedoresPage')
const CierreDiarioPage = perezosa(() => import('../features/reportes/pages/CierreDiarioPage'), 'CierreDiarioPage')
const AntiguedadPage = perezosa(() => import('../features/reportes/pages/AntiguedadPage'), 'AntiguedadPage')
const PromocionesPage = perezosa(() => import('../features/promociones/pages/PromocionesPage'), 'PromocionesPage')
const HistorialPage = perezosa(() => import('../features/auditoria/pages/HistorialPage'), 'HistorialPage')

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
          { path: '/promociones', element: <PromocionesPage /> },
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
