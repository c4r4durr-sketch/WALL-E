import { useQuery } from '@tanstack/react-query'
import { obtenerCierreDiario } from '../api/reportesApi'

export function useCierreDiario(filtro: { sucursal?: number; fecha: string }, habilitado: boolean) {
  return useQuery({
    queryKey: ['cierre-diario', filtro.sucursal ?? null, filtro.fecha],
    queryFn: () => obtenerCierreDiario(filtro),
    enabled: habilitado,
  })
}
