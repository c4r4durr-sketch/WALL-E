import { useMutation, useQueryClient } from '@tanstack/react-query'
import { crearHerramienta } from '../api/catalogoApi'

// Al crear una herramienta se invalida el listado para que la tabla del
// catálogo la muestre sin recargar la página.
export function useCrearHerramienta() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: crearHerramienta,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['herramientas'] }),
  })
}
