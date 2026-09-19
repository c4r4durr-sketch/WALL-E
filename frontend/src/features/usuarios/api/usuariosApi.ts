import { httpClient } from '../../../shared/api/httpClient'
import type { Rol } from '../../../shared/types/roles'

export interface Sucursal {
  id: number
  nombre: string
  direccion: string
  activa: boolean
}

export interface CrearUsuarioPayload {
  username: string
  password: string
  first_name: string
  last_name: string
  rol: Rol
  sucursal: number | null
}

export async function listarSucursales(): Promise<Sucursal[]> {
  const { data } = await httpClient.get<Sucursal[]>('/usuarios/sucursales/')
  return data
}

export async function crearUsuario(payload: CrearUsuarioPayload): Promise<void> {
  await httpClient.post('/usuarios/usuarios/', payload)
}
