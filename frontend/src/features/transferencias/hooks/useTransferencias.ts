import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  completarTransferencia,
  listarTransferencias,
  rechazarTransferencia,
  solicitarTransferencia,
  type EstadoTransferencia,
} from '../api/transferenciasApi'

export function useTransferencias(estado?: EstadoTransferencia) {
  return useQuery({ queryKey: ['transferencias', estado ?? 'todas'], queryFn: () => listarTransferencias(estado) })
}

// Resolver una transferencia mueve stock: además del listado se refrescan
// stock, historial de movimientos, el panel de inicio y los indicadores
// (el stock de cada sucursal decide qué hay que pedir).
function useRefrescar() {
  const queryClient = useQueryClient()
  return () => {
    for (const clave of ['transferencias', 'stock', 'movimientos', 'panel', 'indicadores']) {
      queryClient.invalidateQueries({ queryKey: [clave] })
    }
  }
}

export function useSolicitarTransferencia() {
  return useMutation({ mutationFn: solicitarTransferencia, onSuccess: useRefrescar() })
}

export function useCompletarTransferencia() {
  return useMutation({ mutationFn: completarTransferencia, onSuccess: useRefrescar() })
}

export function useRechazarTransferencia() {
  return useMutation({ mutationFn: rechazarTransferencia, onSuccess: useRefrescar() })
}
