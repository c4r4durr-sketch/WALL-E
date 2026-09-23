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
// stock, historial de movimientos y el panel de inicio.
function useRefrescar() {
  const queryClient = useQueryClient()
  return () => {
    for (const clave of ['transferencias', 'stock', 'movimientos', 'panel']) {
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
