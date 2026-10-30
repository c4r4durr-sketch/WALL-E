import { Aviso, Button, Card, PageHeader, SkeletonFilas } from '../../../components/ui'
import { usePanel } from '../hooks/usePanel'
import { TablaAlertasReorden } from '../components/TablasPanel'

// Reposición EOQ: todas las herramientas que llegaron a su punto de
// reorden, con cuánto pedir (EOQ en cajas cerradas). Es la misma
// información de alertas del panel (GET /api/indicadores/panel/), completa.
export function ReposicionPage() {
  const { data: panel, isLoading, isError, refetch } = usePanel()

  return (
    <>
      <PageHeader
        migas={['Análisis', 'Reposición EOQ']}
        titulo="Reposición EOQ"
        subtitulo="Qué pedir hoy: herramientas en o bajo su punto de reorden y el pedido sugerido."
      />

      {isError && (
        <Aviso tono="error" accion={<Button tamano="sm" onClick={() => refetch()}>Reintentar</Button>}>
          No se pudieron cargar las alertas de reorden.
        </Aviso>
      )}
      {isLoading && (
        <Card sinPadding>
          <SkeletonFilas filas={6} />
        </Card>
      )}
      {panel && <TablaAlertasReorden alertas={panel.alertas} sinDatos={panel.herramientas_sin_datos_rop} />}
    </>
  )
}
