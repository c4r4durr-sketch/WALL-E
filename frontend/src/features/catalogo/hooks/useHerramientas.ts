import { useQuery } from '@tanstack/react-query'
import { listarHerramientas } from '../api/catalogoApi'

// Hook de lectura para el listado de herramientas. La UI (filtros, tabla,
// formulario de alta) se implementa junto con el resto de la feature.
export function useHerramientas() {
  return useQuery({ queryKey: ['herramientas'], queryFn: listarHerramientas })
}
