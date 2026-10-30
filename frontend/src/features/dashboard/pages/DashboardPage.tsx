import { Aviso, Button, Card, PageHeader, SkeletonFilas, SkeletonIndicadores } from '../../../components/ui'
import { getSession } from '../../auth/session'
import { fechaLarga, hoyEnLaPaz } from '../../../shared/formato'
import { usePanel } from '../hooks/usePanel'
import { StatTile } from '../components/StatTile'
import { TablaAlertasReorden, TablaEstancadas } from '../components/TablasPanel'

// Panel principal (HU24): saludo, indicadores del inventario y las
// alertas (equivalente de vw_panel_auditoria). Los accesos a los módulos
// están en la barra lateral.
export function DashboardPage() {
  const session = getSession()
  const { data: panel, isLoading, isError, refetch } = usePanel()

  if (!session) return null

  return (
    <>
      <PageHeader
        titulo={`Hola, ${session.first_name || session.username}`}
        subtitulo={`${fechaLarga(hoyEnLaPaz())}${session.sucursal_nombre ? ` · ${session.sucursal_nombre}` : ''}`}
      />

      {isError && (
        <Aviso tono="error" accion={<Button tamano="sm" onClick={() => refetch()}>Reintentar</Button>}>
          No se pudo cargar el panel.
        </Aviso>
      )}

      {isLoading && (
        <>
          <SkeletonIndicadores />
          <Card sinPadding>
            <SkeletonFilas filas={4} />
          </Card>
        </>
      )}

      {panel && (
        <>
          <div className="grid grid-cols-4 gap-5">
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

          <TablaAlertasReorden alertas={panel.alertas} sinDatos={panel.herramientas_sin_datos_rop} limite={5} />
          <TablaEstancadas estancadas={panel.estancadas} dias={panel.dias_para_estancamiento} />
        </>
      )}
    </>
  )
}
