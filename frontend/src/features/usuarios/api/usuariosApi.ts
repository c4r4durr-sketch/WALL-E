import { httpClient } from '../../../shared/api/httpClient'
import type { Rol } from '../../../shared/types/roles'

export interface Sucursal {
  id: number
  nombre: string
  direccion: string
  activa: boolean
}

// Espeja UsuarioSerializer (backend/apps/usuarios/interfaces/api/serializers.py).
// La contraseña nunca viene en las respuestas.
export interface Usuario {
  id: number
  username: string
  first_name: string
  last_name: string
  email: string
  rol: Rol
  sucursal: number | null
  sucursal_nombre: string | null
  is_active: boolean
}

export interface CrearUsuarioPayload {
  username: string
  password: string
  first_name: string
  last_name: string
  rol: Rol
  sucursal: number | null
}

export type EditarUsuarioPayload = Partial<
  Pick<Usuario, 'first_name' | 'last_name' | 'email' | 'rol' | 'sucursal' | 'is_active'>
>

const URL = '/usuarios/usuarios/'

export async function listarSucursales(): Promise<Sucursal[]> {
  const { data } = await httpClient.get<Sucursal[]>('/usuarios/sucursales/')
  return data
}

export async function listarUsuarios(): Promise<Usuario[]> {
  const { data } = await httpClient.get<Usuario[]>(URL)
  return data
}

export async function crearUsuario(payload: CrearUsuarioPayload): Promise<Usuario> {
  const { data } = await httpClient.post<Usuario>(URL, payload)
  return data
}

// PATCH: solo viajan los campos que cambian (editar o activar/desactivar).
export async function editarUsuario(
  { id, ...cambios }: EditarUsuarioPayload & { id: number },
): Promise<Usuario> {
  const { data } = await httpClient.patch<Usuario>(`${URL}${id}/`, cambios)
  return data
}

// HU3: el Administrador asigna una contraseña nueva; la anterior deja de servir.
export async function restablecerPassword({ id, password }: { id: number; password: string }): Promise<void> {
  await httpClient.post(`${URL}${id}/restablecer-password/`, { password })
}
