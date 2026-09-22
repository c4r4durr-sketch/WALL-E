import { useMutation, useQueryClient } from '@tanstack/react-query'
import { actualizarHerramienta } from '../api/catalogoApi'

export function useActualizarHerramienta() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: actualizarHerramienta,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['herramientas'] }),
  })
}
