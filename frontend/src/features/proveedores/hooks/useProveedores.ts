import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { crearProveedor, editarProveedor, eliminarProveedor, listarProveedores } from '../api/proveedoresApi'

export function useProveedores(filtro: { buscar?: string; activos?: boolean } = {}) {
  return useQuery({
    queryKey: ['proveedores', filtro.buscar ?? '', filtro.activos ?? false],
    queryFn: () => listarProveedores(filtro),
    placeholderData: (anteriores) => anteriores, // sin parpadeo al buscar
  })
}

// Al cambiar un proveedor también cambia lo que muestra el catálogo
// (nombre del proveedor de cada herramienta).
function useInvalidar() {
  const queryClient = useQueryClient()
  return () => {
    void queryClient.invalidateQueries({ queryKey: ['proveedores'] })
    void queryClient.invalidateQueries({ queryKey: ['herramientas'] })
  }
}

export function useCrearProveedor() {
  const invalidar = useInvalidar()
  return useMutation({ mutationFn: crearProveedor, onSuccess: invalidar })
}

export function useEditarProveedor() {
  const invalidar = useInvalidar()
  return useMutation({ mutationFn: editarProveedor, onSuccess: invalidar })
}

export function useEliminarProveedor() {
  const invalidar = useInvalidar()
  return useMutation({ mutationFn: eliminarProveedor, onSuccess: invalidar })
}
