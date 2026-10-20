import { useMutation, useQueryClient } from '@tanstack/react-query'
import { actualizarHerramienta } from '../api/catalogoApi'

export function useActualizarHerramienta() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: actualizarHerramienta,
    // También el historial de costos (HU7): puede tener un cambio nuevo.
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: ['herramientas'] })
      void queryClient.invalidateQueries({ queryKey: ['historial-costos'] })
    },
  })
}
