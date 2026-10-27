import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { crearPromocion, listarPromociones, terminarPromocion } from '../api/promocionesApi'

export function usePromociones(vigentes: boolean) {
  return useQuery({
    queryKey: ['promociones', vigentes],
    queryFn: () => listarPromociones(vigentes),
    placeholderData: (anteriores) => anteriores, // sin parpadeo al cambiar el filtro
  })
}

function useInvalidar() {
  const queryClient = useQueryClient()
  return () => queryClient.invalidateQueries({ queryKey: ['promociones'] })
}

export function useCrearPromocion() {
  const invalidar = useInvalidar()
  return useMutation({ mutationFn: crearPromocion, onSuccess: invalidar })
}

export function useTerminarPromocion() {
  const invalidar = useInvalidar()
  return useMutation({ mutationFn: terminarPromocion, onSuccess: invalidar })
}
