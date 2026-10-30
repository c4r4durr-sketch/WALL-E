import { Rol } from '../../shared/types/roles'

// HU23: la etiqueta de promoción la ponen y la quitan el Supervisor (solo
// en su sucursal) y el Administrador (en cualquiera); el Empleado solo la
// ve. El backend responde 403 en cualquier otro caso.
export function puedeGestionarPromociones(rol: Rol): boolean {
  return rol === Rol.ADMINISTRADOR || rol === Rol.SUPERVISOR
}

export function puedeGestionarEn(sesion: { rol: Rol; sucursal_id: number | null }, sucursalId: number): boolean {
  if (sesion.rol === Rol.ADMINISTRADOR) return true
  return sesion.rol === Rol.SUPERVISOR && sesion.sucursal_id === sucursalId
}
