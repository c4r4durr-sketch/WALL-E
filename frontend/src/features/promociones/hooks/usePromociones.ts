import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { crearPromocion, listarPromociones, terminarPromocion, type Promocion } from '../api/promocionesApi'

export function usePromociones(vigentes: boolean) {
  return useQuery({
    queryKey: ['promociones', vigentes],
    queryFn: () => listarPromociones(vigentes),
    placeholderData: (anteriores) => anteriores, // sin parpadeo al cambiar el filtro
  })
}

// Las vigentes de una herramienta (en una sucursal, si se indica), para
// mostrar la etiqueta en cualquier lista.
export function usePromocionesVigentes() {
  const { data } = usePromociones(true)
  return (herramientaId: number, sucursalId?: number): Promocion[] =>
    (data ?? []).filter((p) => p.herramienta_id === herramientaId && (sucursalId === undefined || p.sucursal_id === sucursalId))
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
