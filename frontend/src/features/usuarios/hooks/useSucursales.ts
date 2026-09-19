import { useQuery } from '@tanstack/react-query'
import { listarSucursales } from '../api/usuariosApi'

export function useSucursales() {
  return useQuery({ queryKey: ['sucursales'], queryFn: listarSucursales })
}
