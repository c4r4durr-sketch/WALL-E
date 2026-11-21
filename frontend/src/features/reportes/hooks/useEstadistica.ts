import { useQuery } from '@tanstack/react-query'
import { obtenerEstadistica, type FiltroEstadisticas, type Reporte } from '../api/estadisticasApi'

// Un reporte de la página /reportes. Cada gráfico pide el suyo por
// separado: el que llega primero se dibuja sin esperar a los demás.
export function useEstadistica<R extends Reporte>(reporte: R, filtro: FiltroEstadisticas, habilitado = true) {
  return useQuery({
    queryKey: ['estadisticas', reporte, filtro.desde, filtro.hasta, filtro.sucursal ?? null],
    queryFn: () => obtenerEstadistica(reporte, filtro),
    enabled: habilitado,
    placeholderData: (anterior) => anterior, // sin parpadeo al cambiar el filtro
  })
}
