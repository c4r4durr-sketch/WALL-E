import { useQuery } from '@tanstack/react-query'
import { obtenerAntiguedad, type FiltroAntiguedad } from '../api/reportesApi'

export function useAntiguedad(filtro: FiltroAntiguedad) {
  return useQuery({
    queryKey: ['antiguedad', filtro.sucursal ?? null, filtro.dias_minimos],
    queryFn: () => obtenerAntiguedad(filtro),
    placeholderData: (anterior) => anterior, // sin parpadeo al cambiar el filtro
  })
}
