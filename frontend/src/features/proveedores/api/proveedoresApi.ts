import { httpClient } from '../../../shared/api/httpClient'

// Espeja ProveedorSerializer (backend/apps/proveedores/interfaces/api/serializers.py).
export interface Proveedor {
  id: number
  nombre: string
  telefono: string
  email: string
  activo: boolean
  cantidad_herramientas: number
}

export type ProveedorPayload = Pick<Proveedor, 'nombre' | 'telefono' | 'email'>

const URL = '/proveedores/'

export async function listarProveedores(filtro: { buscar?: string; activos?: boolean } = {}): Promise<Proveedor[]> {
  const { data } = await httpClient.get<Proveedor[]>(URL, {
    params: { buscar: filtro.buscar || undefined, activos: filtro.activos || undefined },
  })
  return data
}

export async function crearProveedor(payload: ProveedorPayload): Promise<Proveedor> {
  const { data } = await httpClient.post<Proveedor>(URL, payload)
  return data
}

// PATCH: solo viajan los campos que cambian (editar o activar/desactivar).
export async function editarProveedor(
  { id, ...cambios }: Partial<ProveedorPayload & Pick<Proveedor, 'activo'>> & { id: number },
): Promise<Proveedor> {
  const { data } = await httpClient.patch<Proveedor>(`${URL}${id}/`, cambios)
  return data
}

export async function eliminarProveedor(id: number): Promise<void> {
  await httpClient.delete(`${URL}${id}/`)
}
