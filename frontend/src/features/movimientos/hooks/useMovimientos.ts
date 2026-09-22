import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { consultarStock, listarMovimientos, registrarAjuste, registrarMovimiento } from '../api/movimientosApi'

// Historial de una herramienta (todas las sucursales). Sin herramienta
// elegida no se consulta nada.
export function useHistorialMovimientos(herramientaId: number | null) {
  return useQuery({
    queryKey: ['movimientos', herramientaId],
    queryFn: () => listarMovimientos({ herramienta: herramientaId! }),
    enabled: herramientaId !== null,
  })
}

// Stock de una herramienta en cada sucursal activa.
export function useStock(herramientaId: number | null) {
  return useQuery({
    queryKey: ['stock', herramientaId],
    queryFn: () => consultarStock(herramientaId!),
    enabled: herramientaId !== null,
  })
}

// Al registrar un movimiento se refrescan historial y stock, para que la
// pantalla muestre el nuevo saldo sin recargar.
function useRefrescarInventario() {
  const queryClient = useQueryClient()
  return () => {
    queryClient.invalidateQueries({ queryKey: ['movimientos'] })
    queryClient.invalidateQueries({ queryKey: ['stock'] })
  }
}

export function useRegistrarMovimiento() {
  return useMutation({ mutationFn: registrarMovimiento, onSuccess: useRefrescarInventario() })
}

// Ajuste de stock (corrección): mismo refresco que un movimiento normal.
export function useRegistrarAjuste() {
  return useMutation({ mutationFn: registrarAjuste, onSuccess: useRefrescarInventario() })
}
