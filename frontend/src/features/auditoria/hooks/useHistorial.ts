import { useQuery } from '@tanstack/react-query'
import { consultarHistorial, obtenerOpcionesHistorial, type FiltroHistorial } from '../api/auditoriaApi'

export function useHistorial(filtro: FiltroHistorial, habilitado: boolean) {
  return useQuery({
    queryKey: ['historial', filtro],
    queryFn: () => consultarHistorial(filtro),
    enabled: habilitado,
    placeholderData: (anterior) => anterior, // sin parpadeo al cambiar de página
  })
}

export function useOpcionesHistorial() {
  return useQuery({ queryKey: ['historial-opciones'], queryFn: obtenerOpcionesHistorial })
}
