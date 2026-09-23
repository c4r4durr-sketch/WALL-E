import { useQuery } from '@tanstack/react-query'
import { obtenerPanel } from '../api/indicadoresApi'

// Se refresca al volver a la pestaña (default de TanStack Query), así el
// panel refleja los movimientos registrados en otra pantalla.
export function usePanel() {
  return useQuery({ queryKey: ['panel'], queryFn: obtenerPanel })
}
