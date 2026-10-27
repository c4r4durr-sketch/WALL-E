import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { actualizarDemanda, obtenerClasificacionABC, obtenerEOQ, obtenerROP } from '../api/indicadoresApi'

export function useClasificacionABC() {
  return useQuery({ queryKey: ['indicadores', 'abc'], queryFn: obtenerClasificacionABC })
}

// EOQ y ROP de una herramienta; sin herramienta elegida no se consulta.
export function useEOQ(herramientaId: number | null) {
  return useQuery({
    queryKey: ['indicadores', 'eoq', herramientaId],
    queryFn: () => obtenerEOQ(herramientaId!),
    enabled: herramientaId !== null,
  })
}

export function useROP(herramientaId: number | null) {
  return useQuery({
    queryKey: ['indicadores', 'rop', herramientaId],
    queryFn: () => obtenerROP(herramientaId!),
    enabled: herramientaId !== null,
  })
}

// HU21. La demanda anual cambia EOQ, ROP, las alertas del panel y el
// catálogo: se refresca todo lo que la muestra.
export function useActualizarDemanda() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: actualizarDemanda,
    onSuccess: () => {
      for (const queryKey of [['indicadores'], ['panel'], ['herramientas']]) {
        void queryClient.invalidateQueries({ queryKey })
      }
    },
  })
}
