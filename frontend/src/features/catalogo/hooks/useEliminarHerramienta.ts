import { useMutation, useQueryClient } from '@tanstack/react-query'
import { eliminarHerramienta } from '../api/catalogoApi'

export function useEliminarHerramienta() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: eliminarHerramienta,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['herramientas'] }),
  })
}
