import { useNavigate } from 'react-router-dom'
import { Aviso, Button, Card, PageHeader, SkeletonFilas } from '../../../components/ui'
import { useClasificacionABC } from '../hooks/useIndicadores'
import { TablaABC } from '../components/TablaABC'

// Clasificación ABC del catálogo (HU19/HU20). Al elegir una herramienta se
// abre Indicadores con su EOQ y su punto de reorden.
export function ClasificacionABCPage() {
  const navigate = useNavigate()
  const { data: abc, isLoading, isError, refetch } = useClasificacionABC()

  return (
    <>
      <PageHeader
        migas={['Análisis', 'Clasificación ABC']}
        titulo="Clasificación ABC"
        subtitulo="Elige una herramienta para ver cuánto y cuándo pedir."
      />
      {isError && (
        <Aviso tono="error" accion={<Button tamano="sm" onClick={() => refetch()}>Reintentar</Button>}>
          No se pudo cargar la clasificación.
        </Aviso>
      )}
      {isLoading && (
        <Card sinPadding>
          <SkeletonFilas filas={8} columnas={5} />
        </Card>
      )}
      {abc && <TablaABC filas={abc} onSeleccionar={(id) => navigate(`/indicadores?herramienta=${id}`)} />}
    </>
  )
}
