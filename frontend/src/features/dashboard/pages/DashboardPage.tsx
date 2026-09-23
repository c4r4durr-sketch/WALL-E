import { Link } from 'react-router-dom'
import { getSession } from '../../auth/session'
import { useLogout } from '../../auth/hooks/useLogout'
import { Rol } from '../../../shared/types/roles'
import { usePanel } from '../hooks/usePanel'
import { StatTile } from '../components/StatTile'
import { TablaAlertasReorden, TablaEstancadas } from '../components/TablasPanel'

const ROL_LABEL: Record<Rol, string> = {
  ADMINISTRADOR: 'Administrador',
  SUPERVISOR: 'Supervisor',
  EMPLEADO: 'Empleado',
}

// Panel principal (HU24): reemplaza la pantalla de bienvenida. Arriba,
// quién está conectado y accesos a los módulos; debajo, los indicadores y
// alertas del inventario (equivalente de vw_panel_auditoria).
export function DashboardPage() {
  const session = getSession()
  const logout = useLogout()
  const { data: panel, isLoading, isError, refetch } = usePanel()

  if (!session) return null

  const accesos = [
    { to: '/catalogo', texto: 'Catálogo de herramientas' },
    { to: '/movimientos', texto: 'Movimientos de inventario' },
    ...(session.rol === Rol.ADMINISTRADOR ? [{ to: '/usuarios/nuevo', texto: 'Crear nueva cuenta' }] : []),
  ]

  return (
    <div className="min-h-screen bg-slate-50 p-6">
      <div className="mx-auto max-w-5xl space-y-6">
        <header className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <h1 className="text-xl font-semibold text-slate-800">
              Bienvenido, {session.first_name} {session.last_name}
            </h1>
            <p className="text-sm text-slate-500">
              {ROL_LABEL[session.rol]}
              {session.sucursal_nombre && ` · ${session.sucursal_nombre}`}
            </p>
          </div>
          <button
            onClick={logout}
            className="rounded-md border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100"
          >
            Cerrar sesión
          </button>
        </header>

        <nav className="flex flex-wrap gap-2" aria-label="Módulos">
          {accesos.map((a) => (
            <Link
              key={a.to}
              to={a.to}
              className="rounded-md border border-slate-200 bg-white px-3 py-2 text-sm font-medium text-blue-700 shadow-sm hover:bg-slate-100"
            >
              {a.texto} →
            </Link>
          ))}
        </nav>

        {isLoading && <p className="text-sm text-slate-500">Cargando panel...</p>}
        {isError && (
          <p role="alert" className="rounded-md bg-red-50 px-3 py-2 text-sm text-red-700">
            No se pudo cargar el panel.{' '}
            <button onClick={() => refetch()} className="font-medium underline">Reintentar</button>
          </p>
        )}

        {panel && (
          <>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <StatTile
                etiqueta="Alertas de reorden"
                valor={panel.total_alertas_stock}
                alerta={panel.total_alertas_stock > 0}
                nota="Todo el stock está sobre su punto de reorden"
              />
              <StatTile
                etiqueta="Herramientas estancadas"
                valor={panel.total_herramientas_estancadas}
                alerta={panel.total_herramientas_estancadas > 0}
                nota={`Nada lleva más de ${panel.dias_para_estancamiento} días sin venderse`}
              />
              <StatTile etiqueta="Herramientas en catálogo" valor={panel.total_herramientas} />
              <StatTile etiqueta="Sucursales activas" valor={panel.total_sucursales_activas} />
            </div>

            <TablaAlertasReorden alertas={panel.alertas} sinDatos={panel.herramientas_sin_datos_rop} />
            <TablaEstancadas estancadas={panel.estancadas} dias={panel.dias_para_estancamiento} />
          </>
        )}
      </div>
    </div>
  )
}
