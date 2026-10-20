import { useQuery } from '@tanstack/react-query'
import { listarHistorialCostos } from '../api/catalogoApi'

export function useHistorialCostos(herramientaId: number) {
  return useQuery({
    queryKey: ['historial-costos', herramientaId],
    queryFn: () => listarHistorialCostos(herramientaId),
  })
}
