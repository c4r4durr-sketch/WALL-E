import { Rol } from '../../shared/types/roles'

// HU23: solo el Administrador crea o termina promociones (el backend
// responde 403 a cualquier otro rol); todos las consultan.
export function puedeGestionarPromociones(rol: Rol): boolean {
  return rol === Rol.ADMINISTRADOR
}
